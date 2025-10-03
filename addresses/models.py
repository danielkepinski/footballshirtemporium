from django.conf import settings
from django.db import models

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    name = models.CharField(max_length=100, help_text="e.g. Home, Work")
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="GB", help_text="ISO country code")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "name"]
        unique_together = [("user", "name")]

    def __str__(self):
        return f"{self.name} • {self.line1}, {self.city}"
