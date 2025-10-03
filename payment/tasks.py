from io import BytesIO

from celery import shared_task
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from orders.models import Order


@shared_task
def payment_completed(order_id: int) -> None:
    """Send invoice email (PDF attached if WeasyPrint is available)."""
    order = Order.objects.get(id=order_id)

    subject = f"Football Shirt Emporium - Invoice #{order.id}"
    body = "Please find your invoice attached. Thank you for your order."

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com"),
        to=[order.email] if getattr(order, "email", None) else [],
    )

    # Try to render a PDF; if WeasyPrint or its native deps are missing, just send the email without attachment.
    try:
        import weasyprint  # lazy import so migrations/URL checks don't fail on Windows
        html = render_to_string("orders/order/pdf.html", {"order": order})

        css_path = finders.find("css/pdf.css")
        stylesheets = [weasyprint.CSS(css_path)] if css_path else []

        pdf_io = BytesIO()
        weasyprint.HTML(string=html).write_pdf(pdf_io, stylesheets=stylesheets)
        email.attach(
            filename=f"order_{order.id}.pdf",
            content=pdf_io.getvalue(),
            mimetype="application/pdf",
        )
    except Exception:
        # Optional: log this if you want visibility instead of silent pass.
        # import logging; logging.getLogger(__name__).warning("PDF generation skipped", exc_info=True)
        pass

    email.send(fail_silently=True)
