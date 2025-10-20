from unittest.mock import patch
from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order, OrderItem
from shop.models import Category, Product, Team


@override_settings(STRIPE_SECRET_KEY="sk_test_123", STRIPE_PUBLISHABLE_KEY="pk_test_123")
class PaymentProcessTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team")
        self.prod = Product.objects.create(
            category=cat, name="P", slug="p", price="12.34", available=True, team=team
        )
        self.order = Order.objects.create(
            first_name="A", last_name="B", email="a@example.com",
            address="1 Street", postal_code="SW1A 1AA", city="London"
        )
        OrderItem.objects.create(order=self.order, product=self.prod, price="12.34", quantity=2)

    def test_get_renders_summary(self):
        # put order_id in session
        s = self.client.session
        s["order_id"] = self.order.id
        s.save()

        resp = self.client.get(reverse("payment:process"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "£")  # summary shows prices

    def test_redirects_to_create_order_when_missing_session(self):
        resp = self.client.get(reverse("payment:process"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("orders:order_create"), resp["Location"])

    @patch("payment.views.stripe.checkout.Session.create")
    def test_post_creates_stripe_session_and_redirects(self, mock_create):
        mock_create.return_value.url = "https://stripe.example/session"
        # put order_id in session
        s = self.client.session
        s["order_id"] = self.order.id
        s.save()

        resp = self.client.post(reverse("payment:process"))
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(resp["Location"], "https://stripe.example/session")

        # Verify line-items and metadata were built
        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs["mode"], "payment")
        self.assertEqual(kwargs["client_reference_id"], str(self.order.id))
        self.assertEqual(kwargs["metadata"]["order_id"], str(self.order.id))
        self.assertTrue(kwargs["line_items"])
