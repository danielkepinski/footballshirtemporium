from django.conf import settings
from django.db import models


class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
             models.Index(fields=['paid']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_stripe_url(self) -> str:
        """
        Return a direct link to this order in the Stripe Dashboard (test/live).
        Supports payment_intent (pi_...) and checkout session (cs_...).
        """
        if not self.stripe_id:
            return ""

        base = "https://dashboard.stripe.com"
        if settings.STRIPE_SECRET_KEY.startswith("sk_test_"):
            base += "/test"

        sid = self.stripe_id
        if sid.startswith("pi_"):
            path = f"/payments/{sid}"
        elif sid.startswith("cs_"):
            path = f"/checkouts/sessions/{sid}"
        else:
            # fallback to payments
            path = f"/payments/{sid}"

        return base + path
    
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'shop.Product',
        related_name='order_items',
        on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity