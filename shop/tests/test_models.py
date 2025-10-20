from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify

from shop.models import Category, Product, Team


class ShopModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Liverpool FC", slug="liverpool-fc")
        self.team = Team.objects.create(name="Liverpool")

    def test_category_str_and_url(self):
        self.assertEqual(str(self.cat), "Liverpool FC")
        self.assertEqual(
            self.cat.get_absolute_url(),
            reverse("shop:product_list_by_category", args=[self.cat.slug]),
        )

    def test_team_slug_autofill_and_url(self):
        t = Team.objects.create(name="Manchester United")
        self.assertEqual(t.slug, slugify("Manchester United"))
        self.assertEqual(
            t.get_absolute_url(),
            reverse("shop:product_list_by_team", args=[t.slug]),
        )

    def test_product_str_and_url(self):
        p = Product.objects.create(
            category=self.cat,
            name="liverpool 89/90 away",
            slug="liverpool-8990-away",
            price="45.00",
            available=True,
            team=self.team,
        )
        self.assertEqual(str(p), "liverpool 89/90 away")
        self.assertEqual(
            p.get_absolute_url(),
            reverse("shop:product_detail", args=[p.id, p.slug]),
        )
