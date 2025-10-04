# payment/tasks.py
from celery import shared_task
import logging
from django.core.mail import send_mail
from django.conf import settings
from orders.models import Order

logger = logging.getLogger(__name__)

@shared_task
def payment_completed(order_id: int) -> None:
    """
    Fires after a Stripe checkout session completes.
    Keep it simple for now: fetch the order, log, and email the customer.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logger.warning("payment_completed: order %s not found", order_id)
        return

    subject = f"Order #{order.id} paid"
    message = (
        f"Thanks for your purchase, {order.first_name}!\n\n"
        f"We've received your payment for order #{order.id}."
    )

    # Fallback addresses so this never crashes in Heroku if env isn’t set
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
    to_list = [order.email] if order.email else []

    try:
        if to_list:
            send_mail(subject, message, from_email, to_list, fail_silently=True)
    except Exception as e:
        logger.warning("payment_completed: email send failed for order %s: %s", order.id, e)

    logger.info("payment_completed handled for order %s", order.id)
