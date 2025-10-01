from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", shop_views.home, name="home"), #home with only hero/product grid
    path("shop/", include(("shop.urls", "shop"), namespace="shop")), #shop page (product list etc)
    path("cart/", include(("cart.urls", "cart"), namespace="cart")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("payment/", include(("payment.urls", "payment"), namespace="payment")),  
    path("accounts/", include(("accounts.urls", "account"), namespace="account")),
    path("accounts/", include("django.contrib.auth.urls")), #login/password reset!
    path("addresses/", include(("addresses.urls", "addresses"), namespace="addresses")), 
    path("", include(("shop.urls", "shop"), namespace="shop")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
