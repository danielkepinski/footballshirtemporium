from decimal import Decimal

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from orders.models import Order


def payment_process(request):
    # Expect this to be set by orders.views.order_create
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect("orders:order_create")

    order = get_object_or_404(Order, id=order_id)

    # Configure Stripe
    stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()

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
            unit_amount = int(Decimal(item.price) * 100)  # convert pounds to pence
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

    # GET render summary and a POST form button
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
    Render the thank-you page with a real order number.
    Strategy:
      1) Use order_id saved in the session during order_create.
      2) If missing, use ?session_id=... from Stripe success redirect
         and retrieve Checkout Session to recover client_reference_id.
    """
    order = None

    # 1) Try the id we stored in the session
    order_id = request.session.get("order_id")

    # 2) Fallback via Stripe Checkout Session id
    if not order_id:
        session_id = request.GET.get("session_id")
        if session_id and settings.STRIPE_SECRET_KEY:
            try:
                stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()
                s = stripe.checkout.Session.retrieve(session_id)
                order_id = s.get("client_reference_id") or (s.get("metadata") or {}).get("order_id")
            except Exception:
                order_id = None

    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = None

    return render(request, "payment/completed.html", {"order": order})


def payment_canceled(request):
    return render(request, "payment/canceled.html")
