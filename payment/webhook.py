# payment/webhook.py (only the relevant part shown)
from django.conf import settings
from .tasks import payment_completed

# ...

    if event.type == 'checkout.session.completed':
        session = event.data.object
        if session.mode == 'payment' and session.payment_status == 'paid':
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)

            order.paid = True
            order.stripe_id = session.payment_intent
            order.save()

            # Call synchronously in dev or when eager is enabled; else Celery
            if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or settings.DEBUG:
                payment_completed(order.id)
            else:
                payment_completed.delay(order.id)

    return HttpResponse(status=200)
