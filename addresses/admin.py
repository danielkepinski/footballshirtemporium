from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "city", "postal_code", "country", "is_default"]
    list_filter = ["is_default", "country"]
    search_fields = ["user__username", "name", "line1", "city", "postal_code"]
