from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from shop import views as shop_views            
from django.contrib.auth.views import LogoutView  

urlpatterns = [
    path("admin/", admin.site.urls),

    # Home
    path("", shop_views.home, name="home"),

    # Apps
    path("shop/", include(("shop.urls", "shop"), namespace="shop")),
    path("cart/", include(("cart.urls", "cart"), namespace="cart")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("payment/", include(("payment.urls", "payment"), namespace="payment")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("django.contrib.auth.urls")),  

    #logout with redirect to products
    path(
        "accounts/logout/",
        LogoutView.as_view(next_page="shop:product_list"),
        name="logout",
    ),

    path("addresses/", include(("addresses.urls", "addresses"), namespace="addresses")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
from myshop import views as core_views
handler404 = core_views.custom_404
handler500 = core_views.custom_500    