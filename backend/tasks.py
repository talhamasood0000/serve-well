import time
from datetime import datetime, timedelta
from celery import shared_task

from backend.models import Company, Order, QuestionTemplate
from backend.whats_app_utils import send_whats_app_message


@shared_task
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True


@shared_task    
def debug_task(self):
    for company in Company.objects.all():
        for order in Order.objects.filter(company=company, time__lte=datetime.now() - timedelta(hours=6)):
            latest_unanswered_question = QuestionTemplate.objects.filter(order=order, answer=None).order_by("priority").first()
            if latest_unanswered_question:
                send_whats_app_message(company.instance_id, order.customer_phone_number, latest_unanswered_question.question)
