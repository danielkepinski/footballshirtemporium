
from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            first_name = models.CharField(max_length=50)
            last_name = models.CharField(max_length=50)
            email = models.EmailField()  
            address = models.CharField(max_length=250)
            city = models.CharField(max_length=100)
            postal_code = models.CharField(max_length=20)
            
        ]
