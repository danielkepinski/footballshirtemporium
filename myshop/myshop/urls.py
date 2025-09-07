"""
URL configuration for myshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "shop"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.product_list, name="product_list"),
    path("<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("products/<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
]

# Serve static files when DEBUG is False (for local testing only).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
