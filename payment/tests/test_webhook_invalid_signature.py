from django.test import Client, TestCase
from django.urls import reverse

class WebhookTests(TestCase):
    def test_webhook_requires_signature(self):
        c = Client()
        r = c.post(reverse("payment:stripe-webhook"), data="{}", content_type="application/json")
        self.assertEqual(r.status_code, 400)
