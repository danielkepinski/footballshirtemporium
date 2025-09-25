# payment/webhook.py
import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .tasks import payment_completed


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    if not sig_header:
        return HttpResponseBadRequest("Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") == "payment" and session.get("payment_status") == "paid":
            order_id = session.get("client_reference_id")
            if not order_id:
                return HttpResponseBadRequest("Missing client_reference_id")

            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return HttpResponseNotFound("Order not found")

            # mark order as paid and store Stripe PI id
            order.paid = True
            order.stripe_id = session.get("payment_intent")
            order.save()

            # fire task (sync in DEBUG to avoid broker errors)
            from django.conf import settings as dj_settings
            if dj_settings.DEBUG:
                payment_completed(order.id)
            else:
                payment_completed.delay(order.id)

    return HttpResponse(status=200)
