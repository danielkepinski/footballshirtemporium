from decimal import Decimal

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from orders.models import Order
from .tasks import payment_completed as send_paid_email  # avoid name clash with view


def payment_process(request):
    # Expect this to be set by orders.views.order_create
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect("orders:order_create")

    order = get_object_or_404(Order, id=order_id)

    # Configure Stripe
    stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()
    # Optional: lock API version
    # stripe.api_version = settings.STRIPE_API_VERSION

    if request.method == "POST":
        success_url = (
            request.build_absolute_uri(reverse("payment:completed"))
            + "?session_id={CHECKOUT_SESSION_ID}"
        )
        cancel_url = request.build_absolute_uri(reverse("payment:canceled"))
        CURRENCY = getattr(settings, "STRIPE_CURRENCY", "gbp")

        # Build line items
        line_items = []
        for item in order.items.all():
            unit_amount = int(Decimal(item.price) * 100)  # pounds → pence
            line_items.append(
                {
                    "price_data": {
                        "unit_amount": unit_amount,
                        "currency": CURRENCY,
                        "product_data": {"name": item.product.name},
                    },
                    "quantity": item.quantity,
                }
            )

        # Session data (include identifiers for webhook lookup)
        session_data = {
            "mode": "payment",
            "line_items": line_items,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": str(order.id),
            "metadata": {"order_id": str(order.id)},
        }

        try:
            session = stripe.checkout.Session.create(**session_data)

            # Save a stable Stripe reference early (PI id if available, else session id)
            stripe_identifier = getattr(session, "payment_intent", None) or session.id
            if stripe_identifier and stripe_identifier != order.stripe_id:
                order.stripe_id = stripe_identifier
                order.save(update_fields=["stripe_id"])

        except Exception as e:
            # Show the error on the page
            return render(
                request,
                "payment/process.html",
                {
                    "order": order,
                    "stripe_error": str(e),
                    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                },
            )

        # Only redirect after successful Session creation (POST branch)
        return redirect(session.url, code=303)

    # GET → render summary and a POST form button
    return render(
        request,
        "payment/process.html",
        {
            "order": order,
            "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
        },
    )


def payment_completed(request):
    """
    Thank-you page.
    Primary: webhook marks orders as paid.
    Fallback: if we have a session_id, retrieve the Checkout Session from Stripe;
              if it's paid, mark the order as paid here too.
    """
    stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()

    order = None
    order_id = request.session.get("order_id")

    # If we lost the session, recover via the Checkout Session
    session_id = request.GET.get("session_id")
    session_obj = None

    if not order_id and session_id:
        try:
            session_obj = stripe.checkout.Session.retrieve(session_id)
            order_id = session_obj.get("client_reference_id") or (
                session_obj.get("metadata") or {}
            ).get("order_id")
        except Exception:
            order_id = None

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = None

    # Fallback: if webhook hasn’t updated yet, verify with Stripe and mark paid
    if order and not order.paid and session_id:
        try:
            session_obj = session_obj or stripe.checkout.Session.retrieve(session_id)
            if session_obj.get("payment_status") == "paid":
                pi = session_obj.get("payment_intent")

                changed = False
                if not order.paid:
                    order.paid = True
                    changed = True
                if pi and order.stripe_id != pi:
                    order.stripe_id = pi
                    changed = True
                if changed:
                    order.save(update_fields=["paid", "stripe_id"])

                    # Send the "paid" email once
                    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) or getattr(settings, "DEBUG", False):
                        send_paid_email(order.id)
                    else:
                        send_paid_email.delay(order.id)
        except Exception:
            # If Stripe retrieval fails, just render the page; webhook may still update later
            pass

    return render(request, "payment/completed.html", {"order": order})


def payment_canceled(request):
    return render(request, "payment/canceled.html")
