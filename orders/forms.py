# orders/forms.py
import re
from django import forms
from django.core.validators import RegexValidator
from .models import Order

# Stricter  postcode pattern
UK_POSTCODE_PATTERN = re.compile(
    r'^(GIR\s?0AA|(?:[A-PR-UWYZ][0-9][0-9]?|[A-PR-UWYZ][A-HK-Y][0-9][0-9]?|'
    r'[A-PR-UWYZ][0-9][A-HJKPSTUW]|[A-PR-UWYZ][A-HK-Y][0-9][ABEHMNPRV-Y])\s?'
    r'[0-9][ABD-HJLNP-UW-Z]{2})$',
    re.IGNORECASE
)

def normalize_uk_postcode(value: str) -> str:
    s = re.sub(r'\s+', '', value or '').upper()
    return s[:-3] + ' ' + s[-3:] if len(s) > 3 else s

validate_uk_postcode = RegexValidator(
    UK_POSTCODE_PATTERN,
    message="Enter a valid UK postcode (e.g. SW1A 1AA)."
)

class OrderCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50, strip=True,
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "First name"})
    )
    last_name = forms.CharField(
        max_length=50, strip=True,
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Last name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"})
    )
    address = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={"autocomplete": "address-line1", "placeholder": "Address line"})
    )
    postal_code = forms.CharField(
        max_length=8,  # typical max incl. space
        validators=[validate_uk_postcode],
        widget=forms.TextInput(attrs={"autocomplete": "postal-code", "placeholder": "Postcode"})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"autocomplete": "address-level2", "placeholder": "City"})
    )

    class Meta:
        model = Order
        fields = ["first_name", "last_name", "email", "address", "postal_code", "city"]

    # Normalise values
    def clean_postal_code(self):
        pc = self.cleaned_data["postal_code"]
        # validator runs first; just normalize spacing/case for storage
        return normalize_uk_postcode(pc)

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip().title()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip().title()
