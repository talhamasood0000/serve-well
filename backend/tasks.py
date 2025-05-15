import base64
from celery import shared_task
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.core.files.base import ContentFile

from backend.helpers import create_conversation, re_structure_orders
from backend.models import Company, Order, QuestionTemplate, Analytics
from backend.utils import (
    send_whats_app_message,
    transcribe_audio_file,
    analyze_review_with_groq,
    create_next_question_for_order,
)


@shared_task
def start_review():
    for company in Company.objects.all():
        print("Executing task for company", company)

        # Get orders older than 6 hours, ordered by customer then order date
        orders = (
            company.orders.filter(order_at__lte=timezone.now() - timedelta(hours=6))
            .order_by("order_at")
        )

        seen_customers = {}
        for order in orders:
            phone = order.customer_phone_number
            if phone in seen_customers:
                continue  # already found an uncompleted order for this customer

            if not order.is_order_completed:
                seen_customers[phone] = order

        for order in seen_customers.values():
            print("Processing order", order)

            question_template = QuestionTemplate.objects.filter(
                order=order,
            ).exists()

            if not question_template:
                QuestionTemplate.objects.create(
                    order=order,
                    question="Hi! We'd love to hear your thoughts — how was your experience at our restaurant?",
                    priority=1,
                )
            print("Processing order", order)
            latest_unanswered_question = (
                QuestionTemplate.objects.filter(order=order)
                .filter(Q(answer__isnull=True) | Q(answer=""))
                .order_by("priority")
                .first()
            )

            if latest_unanswered_question:
                print("Sending question to", order.customer_phone_number)
                send_whats_app_message(
                    company.instance_id,
                    company.api_token,
                    order.customer_phone_number,
                    latest_unanswered_question.question,
                )


@shared_task
def process_next_step_for_order(
    message_sender_phone_number,
    instance_id,
    message_content,
    message_type="chat",
    media_type=None,
    media_data=None,
):
    company = Company.objects.filter(instance_id=instance_id).first()
    if not company:
        return

    orders = Order.objects.filter(
        company=company,
        customer_phone_number=message_sender_phone_number,
    ).order_by("order_at")

    order = None
    for o in orders:
        if not o.is_order_completed:
            order = o
            break

    if not order:
        return

    # Get all unanswered questions for this order
    unanswered_question = (
        QuestionTemplate.objects.filter(order=order)
        .filter(Q(answer__isnull=True) | Q(answer=""))
        .filter(audio="")
        .order_by("priority")
    )

    if not unanswered_question.exists():
        send_whats_app_message(
            company.instance_id,
            company.api_token,
            order.customer_phone_number,
            "We've already received all your responses. Thank you!",
        )
        return

    # Get the first unanswered question
    latest_unanswered_question = unanswered_question.first()

    # Handle different types of messages
    if message_type == "chat":
        # Handle text message
        latest_unanswered_question.answer = message_content
        latest_unanswered_question.save()

    elif message_type == "ptt" and media_data:
        # Handle audio message
        try:
            # Decode base64 data
            audio_content = base64.b64decode(media_data)

            # Generate a filename with timestamp
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            extension = "ogg" if "ogg" in media_type else "mp3"
            filename = f"audio_{order.id}_{latest_unanswered_question.id}_{timestamp}.{extension}"

            # Save the file to the audio field
            latest_unanswered_question.audio.save(
                filename, ContentFile(audio_content), save=True
            )
            print(
                f"Saved audio response for order {order.number}, question {latest_unanswered_question.question}"
            )

            # Transcribe the audio file
            file_path = latest_unanswered_question.audio.path

            transcribed_text = transcribe_audio_file(file_path, language="english")
            if transcribed_text:
                latest_unanswered_question.answer = transcribed_text
                latest_unanswered_question.save()

        except Exception as e:
            print(f"Error processing audio file: {e}")
            return

    # Try to create next question
    questions = QuestionTemplate.objects.filter(order=order)
    latest_priority = latest_unanswered_question.priority + 1
    next_question = create_next_question_for_order(questions)
    if next_question:
        if latest_priority == 4:
            QuestionTemplate.objects.create(
                order=order,
                question=next_question,
                answer="N/A",
                priority=latest_priority,
            )
            send_whats_app_message(
                company.instance_id,
                company.api_token,
                order.customer_phone_number,
                next_question,
            )            
            return # No more questions to ask
        else:
            QuestionTemplate.objects.create(
                order=order,
                question=next_question,
                priority=latest_priority,
            )

    # Check if there are more questions to ask
    remaining_questions = (
        QuestionTemplate.objects.filter(order=order)
        .filter(Q(answer__isnull=True) | Q(answer=""))
        .filter(audio="")
        .order_by("priority")
        .exclude(id=latest_unanswered_question.id)
    )

    if remaining_questions.exists():
        next_unanswered_question = remaining_questions.first()
        send_whats_app_message(
            company.instance_id,
            company.api_token,
            order.customer_phone_number,
            next_unanswered_question.question,
        )
    else:
        send_whats_app_message(
            company.instance_id,
            company.api_token,
            order.customer_phone_number,
            "Thank you for your responses.",
        )


@shared_task
def analyze_orders_sentiment():
    """
    Analyze customer feedback for an order and save the results to Analytics model
    """

    # Find orders with no analytics records
    orders_with_analytics = Analytics.objects.values_list("order_id", flat=True)
    orders_without_analytics = (
        Order.objects.exclude(id__in=orders_with_analytics)
        .select_related("questions")
        .order_by("-order_at", "id", "questions__priority")
        .values("id", "questions__answer", "questions__question", "questions__priority")
    )

    orders_dict = re_structure_orders(orders_without_analytics)

    for order_id, questions in orders_dict.items():
        conversation = create_conversation(questions)
        analysis = analyze_review_with_groq(conversation)

        if "error" in analysis:
            print(f"Error occurred while generating analysis for order {order_id}")
            print(f"Error {analysis}")
            continue

        Analytics.objects.create(
            order_id=order_id,
            sentiment_label=analysis.get("sentiment"),
            emotions=analysis.get("emotions", []),
            extracted_keywords=analysis.get("keywords", []),
            products=analysis.get("product_name", []),
        )
        print(f"Analytics created for order {order_id}")
