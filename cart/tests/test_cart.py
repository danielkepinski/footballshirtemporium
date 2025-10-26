from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase, override_settings

from shop.models import Category, Product, Team

# IMPORTANT: adjust if your Cart class lives elsewhere
from cart.cart import Cart


@override_settings(CART_SESSION_ID="cart")
class CartTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        team = Team.objects.create(name="Team")

        self.p1 = Product.objects.create(
            category=cat, name="Prod 1", slug="p1",
            price=Decimal("9.99"), available=True, team=team
        )
        self.p2 = Product.objects.create(
            category=cat, name="Prod 2", slug="p2",
            price=Decimal("5.50"), available=True, team=team
        )

        # real Django session; wrap in a minimal request object
        self.session = self.client.session
        self.request = SimpleNamespace(session=self.session)
        self.cart = Cart(self.request)

    def test_add_new_product_and_len_and_total(self):
        self.cart.add(self.p1, quantity=1)
        self.cart.add(self.p2, quantity=3)

        self.assertEqual(len(self.cart), 4)

        expected = Decimal("9.99") * 1 + Decimal("5.50") * 3
        self.assertEqual(self.cart.get_total_price(), expected)

        # session kept in sync (Cart mutates the same dict reference)
        self.assertIn(str(self.p1.id), self.session["cart"])
        self.assertTrue(self.session.modified)

    def test_add_same_product_increments_when_not_override(self):
        self.cart.add(self.p1, quantity=2)
        self.cart.add(self.p1, quantity=3)  # increments
        self.assertEqual(self.cart.cart[str(self.p1.id)]["quantity"], 5)

    def test_override_quantity(self):
        self.cart.add(self.p1, quantity=2)
        self.cart.add(self.p1, quantity=10, override_quantity=True)
        self.assertEqual(self.cart.cart[str(self.p1.id)]["quantity"], 10)

    def test_remove_product(self):
        self.cart.add(self.p1, quantity=1)
        self.cart.add(self.p2, quantity=1)
        self.cart.remove(self.p1)
        self.assertNotIn(str(self.p1.id), self.cart.cart)
        self.assertEqual(len(self.cart), 1)

    def test_iter_enriches_with_product_and_computes_totals(self):
        self.cart.add(self.p1, quantity=2)
        self.cart.add(self.p2, quantity=4)

        items = list(self.cart)
        self.assertEqual(len(items), 2)

        by_id = {it["product"].id: it for it in items}
        i1 = by_id[self.p1.id]
        self.assertEqual(i1["product"], self.p1)
        self.assertEqual(i1["price"], Decimal("9.99"))
        self.assertEqual(i1["quantity"], 2)
        self.assertEqual(i1["total_price"], Decimal("9.99") * 2)

        i2 = by_id[self.p2.id]
        self.assertEqual(i2["product"], self.p2)
        self.assertEqual(i2["price"], Decimal("5.50"))
        self.assertEqual(i2["quantity"], 4)
        self.assertEqual(i2["total_price"], Decimal("5.50") * 4)

    def test_iter_prunes_orphaned_product_ids(self):
        # Manually inject an orphan id into the underlying dict
        self.cart.cart["999999"] = {"quantity": 1, "price": "1.00"}
        self.cart.save()

        # Before iteration, orphan exists
        self.assertIn("999999", self.cart.cart)

        # Iteration should prune it (since no Product with that id)
        _ = list(self.cart)  # triggers pruning
        self.assertNotIn("999999", self.cart.cart)
        # And session was marked modified by save()
        self.assertTrue(self.session.modified)

    def test_clear_empties_session_then_reinit_is_empty(self):
        self.cart.add(self.p1, quantity=1)
        self.cart.add(self.p2, quantity=1)

        # Clear removes the session key but does not wipe the in-memory dict
        self.cart.clear()
        self.assertNotIn("cart", self.request.session)

        # Re-create a Cart: __init__ will create an empty cart key again
        fresh_cart = Cart(self.request)
        self.assertIn("cart", self.request.session)
        self.assertEqual(fresh_cart.cart, {})
        self.assertEqual(len(fresh_cart), 0)
        self.assertTrue(self.request.session.modified)
