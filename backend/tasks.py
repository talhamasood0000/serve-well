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
