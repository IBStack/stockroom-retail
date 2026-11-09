from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('pos/', views.pos, name='pos'),
    path('pos/checkout/', views.checkout, name='checkout'),
    path('sales/', views.sales, name='sales'),
    path('customers/', views.customers, name='customers'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('vendors/', views.vendors, name='vendors'),
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('purchase-orders/<int:pk>/receive/', views.receive_purchase_order, name='receive_purchase_order'),
    path('adjustments/', views.stock_adjustments, name='stock_adjustments'),
    path('returns/', views.returns, name='returns'),
    path('reports/', views.reports, name='reports'),
]
