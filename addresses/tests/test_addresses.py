from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

class AddressTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="a", password="pw")

    def test_list_requires_login(self):
        r = self.client.get(reverse("addresses:list"))
        self.assertEqual(r.status_code, 302)

    def test_create_address(self):
        self.client.login(username="a", password="pw")
        r = self.client.post(reverse("addresses:create"), {
            "name": "Home", "line1": "1 High St", "line2": "",
            "city": "London", "postal_code": "SW1A 1AA", "country": "GB",
            "is_default": True,
        })
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse("addresses:list"))
        self.assertContains(r, "Home")
