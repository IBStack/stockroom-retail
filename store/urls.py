from django.urls import path
from . import views
urlpatterns = [path('', views.dashboard, name='dashboard'), path('products/', views.products, name='products'), path('products/new/', views.product_create, name='product_create'), path('products/<int:pk>/edit/', views.product_edit, name='product_edit'), path('pos/', views.pos, name='pos'), path('pos/checkout/', views.checkout, name='checkout'), path('sales/', views.sales, name='sales')]
