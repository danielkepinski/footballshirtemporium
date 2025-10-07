# payment/views.py
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

    # Configure Stripe (safe if keys are blank in dev—errors will surface in the template)
    stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()
    # Optional: lock API version
    # stripe.api_version = settings.STRIPE_API_VERSION

    if request.method == "POST":
        success_url = request.build_absolute_uri(reverse("payment:completed"))
        cancel_url = request.build_absolute_uri(reverse("payment:canceled"))
        CURRENCY = getattr(settings, "STRIPE_CURRENCY", "gbp")

        # Build line items
        line_items = []
        for item in order.items.all():
            unit_amount = int(Decimal(item.price) * 100)  # convert pounds → pence
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
    return render(request, "payment/completed.html")


def payment_canceled(request):
    return render(request, "payment/canceled.html")
