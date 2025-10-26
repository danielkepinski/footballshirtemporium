from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

class AccountsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("dan", "d@e.com", "pass12345")

    def test_dashboard_requires_login(self):
        res = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(res.status_code, 302)  # redirect to login

    def test_dashboard_ok_when_logged_in(self):
        self.client.login(username="dan", password="pass12345")
        res = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "My orders")
