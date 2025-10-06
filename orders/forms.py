# orders/forms.py
from django import forms
from django.core.validators import RegexValidator
from .models import Order

UK_POSTCODE_RE = r"^(GIR ?0AA|(?:(?:[A-Z]{1,2}\d[A-Z\d]?) ?\d[A-Z]{2}))$"

class OrderCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50, strip=True,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"})
    )
    last_name = forms.CharField(
        max_length=50, strip=True,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"})
    )
    email = forms.EmailField(  # <-- validates email format
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"})
    )
    address = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={"autocomplete": "address-line1", "placeholder": "Address line"})
    )
    postal_code = forms.CharField(
        max_length=20,
        validators=[RegexValidator(UK_POSTCODE_RE, "Enter a valid UK postcode (e.g. SW1A 1AA).", flags=0)],
        widget=forms.TextInput(attrs={"autocomplete": "postal-code", "placeholder": "Postcode"})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"autocomplete": "address-level2", "placeholder": "City"})
    )

    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "postal_code", "city"]


    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip().title()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip().title()
