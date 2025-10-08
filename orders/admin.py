# orders/admin.py
import csv
import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html  


from .models import Order, OrderItem


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{opts.verbose_name}.csv"'
    writer = csv.writer(response)

    fields = [
        f for f in opts.get_fields()
        if not f.many_to_many and not f.one_to_many
    ]
    writer.writerow([f.verbose_name for f in fields])

    for obj in queryset:
        row = []
        for f in fields:
            value = getattr(obj, f.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime("%d/%m/%Y")
            row.append(value)
        writer.writerow(row)
    return response

export_to_csv.short_description = "Export to CSV"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "first_name",
        "last_name",
        "email",
        "address",
        "postal_code",
        "city",
        "paid",
        "order_payment",   
        "created",
        "updated",
        "order_detail",    
        "order_pdf",       
    ]
    list_filter = ["paid", "created", "updated"]
    search_fields = ["first_name", "last_name", "email", "id"]
    inlines = [OrderItemInline]
    actions = [export_to_csv]

    # admin column: link to Stripe
    def order_payment(self, obj):
        url = obj.get_stripe_url()
        if not url:
            return "-"
        return format_html('<a href="{}" target="_blank" rel="noopener">Stripe</a>', url)
    order_payment.short_description = "Stripe"

    # admin column: link to detail view 
    def order_detail(self, obj):
        url = reverse("orders:admin_order_detail", args=[obj.id])
        return format_html('<a href="{}">View</a>', url)
    order_detail.short_description = "Detail"

    # admin column: link to PDF 
    def order_pdf(self, obj):
        url = reverse("orders:admin_order_pdf", args=[obj.id])
        return format_html('<a href="{}">PDF</a>', url)
    order_pdf.short_description = "Invoice"
