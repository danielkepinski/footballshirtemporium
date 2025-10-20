from decimal import Decimal
from django.test import TestCase, override_settings

from orders.models import Order, OrderItem
from shop.models import Category, Product, Team


class OrderModelTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team A")
        self.p = Product.objects.create(
            category=cat, name="P", slug="p", price="9.99", available=True, team=team
        )
        self.order = Order.objects.create(
            first_name="A", last_name="B", email="a@example.com",
            address="1 Street", postal_code="SW1A 1AA", city="London"
        )

    def test_total_cost(self):
        OrderItem.objects.create(order=self.order, product=self.p, price="9.99", quantity=3)
        self.assertEqual(self.order.get_total_cost(), Decimal("29.97"))

    @override_settings(STRIPE_SECRET_KEY="sk_test_123")
    def test_get_stripe_url_payment_intent(self):
        self.order.stripe_id = "pi_12345"
        self.assertIn("/test/payments/pi_12345", self.order.get_stripe_url())

    @override_settings(STRIPE_SECRET_KEY="sk_test_123")
    def test_get_stripe_url_checkout_session(self):
        self.order.stripe_id = "cs_98765"
        self.assertIn("/test/checkouts/sessions/cs_98765", self.order.get_stripe_url())

    def test_get_stripe_url_empty(self):
        self.order.stripe_id = ""
        self.assertEqual(self.order.get_stripe_url(), "")
