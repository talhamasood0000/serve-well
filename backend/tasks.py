import time
from celery import shared_task
from datetime import timedelta

from django.utils import timezone

from backend.models import Company, Order, QuestionTemplate
from backend.whats_app_utils import send_whats_app_message


@shared_task
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True


@shared_task    
def start_review():
    for company in Company.objects.all():
        for order in company.orders.filter(company=company, time__lte=timezone.now() - timedelta(hours=6)):
            latest_unanswered_question = QuestionTemplate.objects.filter(order=order, answer="").order_by("priority").first()
            if latest_unanswered_question:
                send_whats_app_message(company.instance_id, company.api_token, order.customer_phone_number, latest_unanswered_question.question)


@shared_task
def process_next_step_for_order(
    message_sender_phone_number, 
    instance_id,  
    message_content
):
    company = Company.objects.filter(instance_id=instance_id).first()
    if not company:
        return
    
    order = Order.objects.filter(
        company=company, 
        customer_phone_number=message_sender_phone_number, 
    ).order_by("-time").first()

    if not order:
        return
    
    unanswered_question = QuestionTemplate.objects.filter(order=order, answer="").order_by("priority")
    if unanswered_question:
        latest_unanswered_question = unanswered_question.first()
        latest_unanswered_question.answer = message_content
        latest_unanswered_question.save()
    
    if unanswered_question.count() > 1:
        next_unanswered_question = unanswered_question[1]
        send_whats_app_message(company.instance_id, company.api_token, order.customer_phone_number, next_unanswered_question.question)
    else:
        send_whats_app_message(company.instance_id, company.api_token, order.customer_phone_number, "Thank you for your response. We will get back to you soon.")
