from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["name", "line1", "line2", "city", "postal_code", "country", "is_default"]
