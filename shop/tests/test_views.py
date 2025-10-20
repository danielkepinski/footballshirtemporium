from django.test import TestCase
from django.urls import reverse

from shop.models import Category, Product, Team


class ProductListViewTests(TestCase):
    def setUp(self):
        self.cat1 = Category.objects.create(name="Liverpool FC", slug="liverpool-fc")
        self.cat2 = Category.objects.create(name="Other", slug="other")
        self.team1 = Team.objects.create(name="Liverpool")
        self.team2 = Team.objects.create(name="Arsenal")

        self.p1 = Product.objects.create(
            category=self.cat1, name="LIV Home", slug="liv-home",
            price="10.00", available=True, team=self.team1,
        )
        self.p2 = Product.objects.create(
            category=self.cat2, name="ARS Home", slug="ars-home",
            price="12.00", available=True, team=self.team2,
        )

    def test_list_all(self):
        resp = self.client.get(reverse("shop:product_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "LIV Home")
        self.assertContains(resp, "ARS Home")

    def test_filter_by_category(self):
        url = reverse("shop:product_list_by_category", args=[self.cat1.slug])
        resp = self.client.get(url)
        self.assertContains(resp, "LIV Home")
        self.assertNotContains(resp, "ARS Home")

    def test_filter_by_team(self):
        url = reverse("shop:product_list_by_team", args=[self.team1.slug])
        resp = self.client.get(url)
        self.assertContains(resp, "LIV Home")
        self.assertNotContains(resp, "ARS Home")


class ProductDetailViewTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Liverpool FC", slug="liverpool-fc")
        team = Team.objects.create(name="Liverpool")
        self.p = Product.objects.create(
            category=cat, name="LIV Home", slug="liv-home",
            price="10.00", available=True, team=team,
        )

    def test_detail_ok(self):
        url = reverse("shop:product_detail", args=[self.p.id, self.p.slug])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p.name)
