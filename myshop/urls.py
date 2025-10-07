from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

from shop import views as shop_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Home page (hero only)
    path("", shop_views.home, name="home"),
    # Shop section
    path("shop/", include(("shop.urls", "shop"), namespace="shop")),
    # Other apps
    path("cart/", include(("cart.urls", "cart"), namespace="cart")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("payment/", include(("payment.urls", "payment"), namespace="payment")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("addresses/", include("addresses.urls", namespace="addresses")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
