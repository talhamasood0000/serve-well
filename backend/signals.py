from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.models import Order
from backend.utils import create_questions_for_order

@receiver(post_save, sender=Order)
def order_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler that runs when an Order is saved
    """
    if created:
        create_questions_for_order(instance)
