from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("profile/", views.profile_edit, name="profile"),            
    path("delete/", views.delete_account, name="delete_account"),   
    path('account/', views.account, name='account'), 
]