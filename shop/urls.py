# shop/urls.py
from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    path("product/<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
    path("<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("", views.product_list, name="product_list"),
    path("team/<slug:team_slug>/", views.product_list, name="product_list_by_team"),
    path("contact/", views.contact, name="contact"), 
    path("search/", views.search, name="search"),
]
