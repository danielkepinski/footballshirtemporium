# payment/webhook.py
from __future__ import annotations

import logging
import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .tasks import payment_completed

logger = logging.getLogger(__name__)


def _finalize_order(order: Order, stripe_ref: str | None) -> None:
    """Mark order paid, persist Stripe reference, and trigger the email task once."""
    updates = []
    already_paid = order.paid

    if not order.paid:
        order.paid = True
        updates.append("paid")

    # keep a stable Stripe reference (prefer payment_intent id)
    if stripe_ref and order.stripe_id != stripe_ref:
        order.stripe_id = stripe_ref
        updates.append("stripe_id")

    if updates:
        order.save(update_fields=updates)

    # Only send email once
    if not already_paid:
        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or getattr(settings, "DEBUG", False):
            payment_completed(order.id)
        else:
            payment_completed.delay(order.id)


@csrf_exempt
def stripe_webhook(request):
    """Verify Stripe signature and mark orders paid on success."""
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
        logger.warning("Stripe webhook: invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: signature verification failed")
        return HttpResponse(status=400)

    etype = event.get("type", "")
    data = event.get("data", {}).get("object", {})  # resource payload

    # --- Path 1: Checkout Session completed (recommended) ---
    if etype == "checkout.session.completed":
        # Guard: only handle one-time payments
        if data.get("mode") != "payment":
            return HttpResponse(status=200)

        # Stripe docs: payment_status can be 'paid'
        if data.get("payment_status") == "paid":
            order_id = data.get("client_reference_id") or (data.get("metadata") or {}).get("order_id")
            if not order_id:
                logger.warning("Stripe webhook: session missing order id")
                return HttpResponse(status=200)

            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                logger.warning("Stripe webhook: Order %s not found", order_id)
                return HttpResponse(status=200)

            # Prefer the PaymentIntent id; fallback to session id
            stripe_ref = data.get("payment_intent") or data.get("id")
            _finalize_order(order, stripe_ref)

    # --- Path 2: PaymentIntent succeeded (extra safety if metadata used) ---
    elif etype == "payment_intent.succeeded":
        md = data.get("metadata") or {}
        order_id = md.get("order_id")
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                logger.warning("Stripe webhook (PI): Order %s not found", order_id)
                return HttpResponse(status=200)
            _finalize_order(order, data.get("id"))

    

    return HttpResponse(status=200)
