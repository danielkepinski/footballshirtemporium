# cart/cart.py
from decimal import Decimal
from django.conf import settings
from shop.models import Product


class Cart:
    def __init__(self, request):
        """Initialize the cart stored in the session."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def __iter__(self):
        """
        Iterate over cart items, attaching Product objects.
        Orphaned entries (where the product no longer exists)
        are removed from the session to avoid template/url errors.
        """
        cart_copy = self.cart.copy()
        product_ids = list(cart_copy.keys())

        # attach products that still exist
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            cart_copy[str(product.id)]["product"] = product

        # prune orphans (no Product attached)
        stale_keys = [pid for pid, data in cart_copy.items() if "product" not in data]
        if stale_keys:
            for pid in stale_keys:
                self.cart.pop(pid, None)
                cart_copy.pop(pid, None)
            self.save()

        # yield normalized items
        for item in cart_copy.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """Add a product to the cart or update its quantity."""
        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {"quantity": 0, "price": str(product.price)}
        if override_quantity:
            self.cart[pid]["quantity"] = quantity
        else:
            self.cart[pid]["quantity"] += quantity
        self.save()

    def save(self):
        """Mark the session as modified to ensure it is saved."""
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the cart."""
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        """Remove cart entirely from the session."""
        self.session.pop(settings.CART_SESSION_ID, None)
        self.save()

    def get_total_price(self):
        """Total using current (possibly pruned) items."""
        total = Decimal("0.00")
        for item in self:
            total += item["total_price"]
        return total
