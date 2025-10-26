from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order, OrderItem
from shop.models import Category, Product, Team


@override_settings(
    STRIPE_SECRET_KEY="sk_test_123",
    STRIPE_PUBLISHABLE_KEY="pk_test_123",
    STRIPE_CURRENCY="gbp",
)
class PaymentProcessTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team")
        self.prod = Product.objects.create(
            category=cat, name="P", slug="p", price="12.34", available=True, team=team
        )
        self.order = Order.objects.create(
            first_name="A",
            last_name="B",
            email="a@example.com",
            address="1 Street",
            postal_code="SW1A 1AA",
            city="London",
        )
        OrderItem.objects.create(
            order=self.order, product=self.prod, price="12.34", quantity=2
        )

    def _put_order_in_session(self):
        s = self.client.session
        s["order_id"] = self.order.id
        s.save()

    def test_get_renders_summary_and_has_publishable_key(self):
        self._put_order_in_session()
        resp = self.client.get(reverse("payment:process"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "£")
        self.assertEqual(resp.context["STRIPE_PUBLISHABLE_KEY"], "pk_test_123")

    def test_redirects_to_create_order_when_missing_session(self):
        resp = self.client.get(reverse("payment:process"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("orders:order_create"), resp["Location"])

    @patch("payment.views.stripe.checkout.Session.create")
    def test_post_creates_stripe_session_and_redirects_and_saves_pi(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://stripe.example/session"
        mock_session.payment_intent = "pi_123"
        mock_session.id = "cs_test_ABC"
        mock_create.return_value = mock_session

        self._put_order_in_session()
        resp = self.client.post(reverse("payment:process"))
        # Accept 302 (Django redirect) or 303 (explicit see-other)
        self.assertIn(resp.status_code, (302, 303))
        self.assertEqual(resp["Location"], "https://stripe.example/session")

        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["mode"], "payment")
        self.assertEqual(kwargs["client_reference_id"], str(self.order.id))
        self.assertEqual(kwargs["metadata"]["order_id"], str(self.order.id))
        self.assertTrue(kwargs["line_items"])
        first_item = kwargs["line_items"][0]
        self.assertEqual(first_item["price_data"]["currency"], "gbp")
        self.assertEqual(first_item["price_data"]["unit_amount"], 1234)  # 12.34 → 1234
        self.assertEqual(first_item["quantity"], 2)
        self.assertIn("{CHECKOUT_SESSION_ID}", kwargs["success_url"])
        self.assertIn(reverse("payment:canceled"), kwargs["cancel_url"])

        self.order.refresh_from_db()
        self.assertEqual(self.order.stripe_id, "pi_123")

    @patch("payment.views.stripe.checkout.Session.create")
    def test_post_saves_session_id_if_no_payment_intent(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://stripe.example/session2"
        mock_session.id = "cs_456"
        mock_session.payment_intent = None
        mock_create.return_value = mock_session

        self._put_order_in_session()
        resp = self.client.post(reverse("payment:process"))
        # Accept 302 (Django redirect) or 303 (explicit see-other)
        self.assertIn(resp.status_code, (302, 303))
        self.order.refresh_from_db()
        self.assertEqual(self.order.stripe_id, "cs_456")

    @patch("payment.views.stripe.checkout.Session.create", side_effect=Exception("boom"))
    def test_post_handles_exception_and_renders_error(self, _mock_create):
        self._put_order_in_session()
        resp = self.client.post(reverse("payment:process"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "boom")
        self.assertContains(resp, "£")


@override_settings(
    STRIPE_SECRET_KEY="sk_test_123",
    STRIPE_PUBLISHABLE_KEY="pk_test_123",
    CELERY_TASK_ALWAYS_EAGER=True,
)
class PaymentCompletedTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team")
        self.prod = Product.objects.create(
            category=cat, name="P", slug="p", price="10.00", available=True, team=team
        )
        self.order = Order.objects.create(
            first_name="A",
            last_name="B",
            email="a@example.com",
            address="1 Street",
            postal_code="SW1A 1AA",
            city="London",
        )
        OrderItem.objects.create(
            order=self.order, product=self.prod, price=Decimal("10.00"), quantity=1
        )

    def _put_order_in_session(self):
        s = self.client.session
        s["order_id"] = self.order.id
        s.save()

    @patch("payment.views.send_paid_email")
    @patch("payment.views.stripe.checkout.Session.retrieve")
    def test_completed_marks_paid_and_updates_stripe_id_when_webhook_not_yet_processed(
        self, mock_retrieve, mock_send_email
    ):
        self._put_order_in_session()
        mock_retrieve.return_value = {
            "payment_status": "paid",
            "payment_intent": "pi_999",
            "client_reference_id": str(self.order.id),
            "metadata": {"order_id": str(self.order.id)},
        }

        resp = self.client.get(reverse("payment:completed") + "?session_id=cs_abc")
        self.assertEqual(resp.status_code, 200)

        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertEqual(self.order.stripe_id, "pi_999")
        mock_send_email.assert_called_once_with(self.order.id)

    @patch("payment.views.send_paid_email")
    @patch("payment.views.stripe.checkout.Session.retrieve")
    def test_completed_recovers_order_when_no_session_order_id(
        self, mock_retrieve, mock_send_email
    ):
        mock_retrieve.return_value = {
            "payment_status": "paid",
            "payment_intent": "pi_111",
            "client_reference_id": str(self.order.id),
            "metadata": {"order_id": str(self.order.id)},
        }

        resp = self.client.get(reverse("payment:completed") + "?session_id=cs_recover")
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertEqual(self.order.stripe_id, "pi_111")
        mock_send_email.assert_called_once_with(self.order.id)

    @patch("payment.views.send_paid_email")
    @patch("payment.views.stripe.checkout.Session.retrieve")
    def test_completed_does_not_send_email_again_if_already_paid(
        self, mock_retrieve, mock_send_email
    ):
        self.order.paid = True
        self.order.stripe_id = "pi_existing"
        self.order.save()

        mock_retrieve.return_value = {
            "payment_status": "paid",
            "payment_intent": "pi_existing",
            "client_reference_id": str(self.order.id),
        }

        self._put_order_in_session()
        resp = self.client.get(reverse("payment:completed") + "?session_id=cs_same")
        self.assertEqual(resp.status_code, 200)
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertEqual(self.order.stripe_id, "pi_existing")
        mock_send_email.assert_not_called()

    @patch("payment.views.stripe.checkout.Session.retrieve", side_effect=Exception("stripe down"))
    def test_completed_gracefully_renders_if_stripe_retrieve_fails(self, _mock_retrieve):
        resp = self.client.get(reverse("payment:completed") + "?session_id=cs_broken")
        self.assertEqual(resp.status_code, 200)

    def test_canceled_renders(self):
        resp = self.client.get(reverse("payment:canceled"))
        self.assertEqual(resp.status_code, 200)
