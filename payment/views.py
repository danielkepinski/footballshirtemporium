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

    if request.method == "POST":
        stripe.api_key = (settings.STRIPE_SECRET_KEY or "").strip()
        stripe.api_version = settings.STRIPE_API_VERSION

        success_url = request.build_absolute_uri(reverse("payment:completed"))
        cancel_url  = request.build_absolute_uri(reverse("payment:canceled"))

        CURRENCY = "gbp"  #gbp, usd, eur, ...
        session_data = {
            "mode": "payment",
            "client_reference_id": str(order.id),
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }
        for item in order.items.all():
            session_data["line_items"].append({
                "price_data": {
                    "unit_amount": int(item.price * Decimal("100")),
                    "currency": CURRENCY,
                    "product_data": {"name": item.product.name},
                },
                "quantity": item.quantity,
            })

        try:
            session = stripe.checkout.Session.create(**session_data)
        except Exception as e:
            return render(
                request,
                "payment/process.html",
                {"order": order, "stripe_error": str(e)},
        )

    return redirect(session.url, code=303)

# ↓ Add these two simple views below
def payment_completed(request):
    return render(request, "payment/completed.html")

def payment_canceled(request):
    return render(request, "payment/canceled.html")
