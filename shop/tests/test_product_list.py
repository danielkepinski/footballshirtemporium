from django.test import Client, TestCase
from django.urls import reverse
from shop.models import Category, Product

class ProductListTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Retro", slug="retro")
        Product.objects.create(category=self.cat, name="1990 Home", slug="1990-home", price=50)

    def test_product_list_ok(self):
        c = Client()
        r = c.get(reverse("shop:product_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "1990 Home")
