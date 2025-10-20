# shop/forms.py
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Your name")
    email = forms.EmailField(label="Your email")
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}), label="Message")

    # simple honeypot (hidden field)
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        # bots fill hidden fields; humans won't
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Invalid submission.")
        return self.cleaned_data["website"]
