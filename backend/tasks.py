import base64
import time
from celery import shared_task
from datetime import timedelta

from django.utils import timezone
from django.core.files.base import ContentFile

from backend.models import Company, Order, QuestionTemplate
from backend.utils import send_whats_app_message, transcribe_audio_file


@shared_task
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True


@shared_task    
def start_review():
    for company in Company.objects.all():
        print("Executing task for company", company)
        for order in company.orders.filter(company=company, order_at__lte=timezone.now() - timedelta(hours=6)):
            print("Processing order", order)
            latest_unanswered_question = QuestionTemplate.objects.filter(order=order, answer="").order_by("priority").first()
            if latest_unanswered_question:
                print("Sending question to", order.customer_phone_number)
                send_whats_app_message(company.instance_id, company.api_token, order.customer_phone_number, latest_unanswered_question.question)


@shared_task
def process_next_step_for_order(
    message_sender_phone_number, 
    instance_id,  
    message_content,
    message_type='chat',
    media_type=None,
    media_data=None
):
    company = Company.objects.filter(instance_id=instance_id).first()
    if not company:
        return
    
    orders = Order.objects.filter(
        company=company, 
        customer_phone_number=message_sender_phone_number, 
    ).order_by("-order_at")

    order = None
    for o in orders:
        if not o.is_order_completed:
            order = o

    if not order:
        return
    
    # Get all unanswered questions for this order
    unanswered_question = QuestionTemplate.objects.filter(
        order=order
    ).filter(
        answer=""
    ).filter(
        audio=""
    ).order_by("priority")

    if not unanswered_question.exists():
        send_whats_app_message(
            company.instance_id, 
            company.api_token, 
            order.customer_phone_number, 
            "We've already received all your responses. Thank you!"
        )
        return

    # Get the first unanswered question    
    latest_unanswered_question = unanswered_question.first()
    
    # Handle different types of messages
    if message_type == 'chat':
        # Handle text message
        latest_unanswered_question.answer = message_content
        latest_unanswered_question.save()
        
    elif message_type == 'ptt' and media_data:
        # Handle audio message
        try:
            # Decode base64 data
            audio_content = base64.b64decode(media_data)
            
            # Generate a filename with timestamp
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            extension = 'ogg' if 'ogg' in media_type else 'mp3'
            filename = f"audio_{order.id}_{latest_unanswered_question.id}_{timestamp}.{extension}"
            
            # Save the file to the audio field
            latest_unanswered_question.audio.save(filename, ContentFile(audio_content), save=True)
            print(f"Saved audio response for order {order.number}, question {latest_unanswered_question.question}")

            # Transcribe the audio file
            file_path = latest_unanswered_question.audio.path

            transcribed_text = transcribe_audio_file(file_path, language="english")
            if transcribed_text:
                latest_unanswered_question.answer = transcribed_text
                latest_unanswered_question.save()
            
        except Exception as e:
            print(f"Error processing audio file: {e}")
            return
    
    # Check if there are more questions to ask
    remaining_questions = unanswered_question.exclude(id=latest_unanswered_question.id)
    
    if remaining_questions.exists():
        next_unanswered_question = remaining_questions.first()
        send_whats_app_message(
            company.instance_id, 
            company.api_token, 
            order.customer_phone_number, 
            next_unanswered_question.question
        )
    else:
        send_whats_app_message(
            company.instance_id, 
            company.api_token, 
            order.customer_phone_number, 
            "Thank you for your responses."
        )
