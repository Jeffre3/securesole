from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_view, name='register_redirect'),  # 👈 Root URL points to register_view
    path('home', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('product/', views.product_view, name='product'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),  # 👈 Added verify_2fa URL path
    path('remove_from_cart/', views.remove_from_cart, name='remove_from_cart'),
]
