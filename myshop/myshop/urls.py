"""
URL configuration for myshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings   # ✅ import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
]

# Serve static files when DEBUG is False (for local testing only).
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
