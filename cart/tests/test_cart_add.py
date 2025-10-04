from django.test import Client, TestCase
from django.urls import reverse
from shop.models import Category, Product

class CartTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Retro", slug="retro")
        self.product = Product.objects.create(category=cat, name="1992 Away", slug="1992-away", price=60)

    def test_add_to_cart(self):
        c = Client()
        r = c.post(reverse("cart:cart_add", args=[self.product.id]), {"quantity": 1, "override": False})
        self.assertEqual(r.status_code, 302)  # redirects to cart
        r = c.get(reverse("cart:cart_detail"))
        self.assertContains(r, "1992 Away")
