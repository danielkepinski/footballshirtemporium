from decimal import Decimal

from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import TestCase

from cart.cart import Cart
from shop.models import Category, Product, Team


def add_session_to_request(request: HttpRequest) -> HttpRequest:
    """Attach a session to a Request for unit tests."""
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


class CartTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team A")
        self.p1 = Product.objects.create(
            category=cat, name="P1", slug="p1", price="10.00", available=True, team=team
        )
        self.p2 = Product.objects.create(
            category=cat, name="P2", slug="p2", price="5.50", available=True, team=team
        )

    def test_add_iter_len_total_remove_clear(self):
        req = add_session_to_request(HttpRequest())
        cart = Cart(req)

        cart.add(self.p1, quantity=2)
        cart.add(self.p2, quantity=1)

        # length = total quantity
        self.assertEqual(len(cart), 3)

        # items iterate with product attached and totals computed
        items = list(cart)
        self.assertEqual(items[0]["product"].id, self.p1.id)
        self.assertEqual(items[0]["total_price"], Decimal("20.00"))

        # total across cart
        self.assertEqual(cart.get_total_price(), Decimal("25.50"))

        # remove
        cart.remove(self.p2)
        self.assertEqual(cart.get_total_price(), Decimal("20.00"))

        # clear
        cart.clear()
        self.assertEqual(len(cart), 0)
