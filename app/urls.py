from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # Landing Page
    path('login', views.login_, name='login'), # Login Page
    path('signup', views.signup_, name='signup'), # Signup Page 
    path('logout', views.logout_, name='logout'), # Logout User
    path('home', views.home, name='home'), # Home Page
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'), # Admin Dashboard
    path('add_product', views.add_product, name="add_product"), # Add new product
    path('product_details/<str:product_id>', views.product_details, name='product_details'), # Product Details Page
    path('search', views.search, name='search'), # Search Details Page
    path('review/<str:product_id>', views.review, name='review') # Add review
]