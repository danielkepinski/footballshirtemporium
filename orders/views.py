# orders/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .tasks import order_created


def order_create(request):
    """
    Create an order from the current cart.
    - Works for guest users (no login required).
    - If user is authenticated, attach the user to the order.
    - Stores order_id in session for the payment step.
    """
    cart = Cart(request)

    # If cart is empty, bounce back to the cart page.
    if not cart:  # Cart.__len__ == 0 => falsy
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Create order
            order = form.save()

            # Attach user if logged in (guest checkout otherwise)
            if request.user.is_authenticated:
                order.user = request.user
                order.save(update_fields=["user"])

            # Persist line items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            # Clear cart now that order is created
            cart.clear()

            # Send confirmation email/task (sync in DEBUG, async in prod)
            if settings.DEBUG:
                order_created(order.id)
            else:
                order_created.delay(order.id)

            # Remember this order for the payment step
            request.session["order_id"] = order.id

            # Friendly message shown on the payment/process page
            messages.info(request, "Almost there — please complete payment.")

            return redirect("payment:process")
    else:
        form = OrderCreateForm()

    return render(request, "orders/order/create.html", {"cart": cart, "form": form})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "admin/orders/order/detail.html", {"order": order})


@staff_member_required
def admin_order_pdf(request, order_id):
    # Import here so local environments without WeasyPrint don't break startup
    try:
        import weasyprint
    except Exception as e:
        return HttpResponseServerError(
            "PDF generation is unavailable on this machine. "
            f"WeasyPrint dependencies are missing. Details: {e}"
        )

    order = get_object_or_404(Order, id=order_id)
    html = render_to_string("orders/order/pdf.html", {"order": order})

    css_path = finders.find("css/pdf.css")
    stylesheets = [weasyprint.CSS(css_path)] if css_path else []

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="order_{order.id}.pdf"'

    weasyprint.HTML(string=html).write_pdf(response, stylesheets=stylesheets)
    return response
