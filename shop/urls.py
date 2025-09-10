# shop/urls.py
from django.urls import path
from . import views   # 👈 this line is missing in your file

app_name = "shop"

urlpatterns = [
    path("product/<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("", views.product_list, name="product_list"),
]
