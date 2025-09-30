from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.conf import settings  # <-- added

from cart.cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .tasks import order_created


def order_create(request):
    cart = Cart(request)

    # guard against empty cart
    if not cart:
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            if request.user.is_authenticated:
            order.user = request.user
            order.save(update_fields=["user"])
                for item in cart:
                    OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

            # clear the cart
            cart.clear()

            # ---- Celery: call synchronously in dev (DEBUG=True), else async
            if settings.DEBUG:
                order_created(order.id)
            else:
                order_created.delay(order.id)
            # ----

            # set the order in the session
            request.session["order_id"] = order.id
            # redirect for payment
            return redirect("payment:process")
    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order/create.html",
        {"cart": cart, "form": form},
    )


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "admin/orders/order/detail.html", {"order": order})


@staff_member_required
def admin_order_pdf(request, order_id):
    try:
        import weasyprint
    except Exception as e:
        return HttpResponseServerError(
            "PDF generation is unavailable on this machine. "
            f"WeasyPrint dependencies are missing. Details: {e}"
        )

    order = get_object_or_404(Order, id=order_id)
    html = render_to_string("orders/order/pdf.html", {"order": order})

    # Locate optional stylesheet (won't crash if missing)
    css_path = finders.find("css/pdf.css")
    stylesheets = [weasyprint.CSS(css_path)] if css_path else []

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="order_{order.id}.pdf"'

    weasyprint.HTML(string=html).write_pdf(response, stylesheets=stylesheets)
    return response
