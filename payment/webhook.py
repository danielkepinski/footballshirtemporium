# payment/webhook.py
import logging
import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .tasks import payment_completed

logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    """Verify Stripe signature and handle checkout.session.completed."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not sig_header:
        logger.warning("Stripe webhook: missing signature header")
        return HttpResponseBadRequest("Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=(settings.STRIPE_WEBHOOK_SECRET or "").strip(),
        )
    except ValueError:
        # Invalid payload
        logger.warning("Stripe webhook: invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        logger.warning("Stripe webhook: signature verification failed")
        return HttpResponse(status=400)

    # ---- Handle events ----
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") == "payment" and session.get("payment_status") == "paid":
            order_id = session.get("client_reference_id")
            if not order_id:
                logger.warning("Stripe webhook: missing client_reference_id")
                return HttpResponse(status=200)

            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                logger.warning("Stripe webhook: order %s not found", order_id)
                return HttpResponse(status=404)

            # Mark order as paid and store Stripe payment intent ID
            order.paid = True
            order.stripe_id = session.get("payment_intent")
            order.save(update_fields=["paid", "stripe_id"])

            # Call task synchronously in dev/eager, else async
            if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or getattr(settings, "DEBUG", False):
                payment_completed(order.id)
            else:
                payment_completed.delay(order.id)

    return HttpResponse(status=200)
