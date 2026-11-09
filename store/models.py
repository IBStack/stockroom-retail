from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ['name']
    def __str__(self): return f'{self.name} ({self.sku})'
    @property
    def low_stock(self): return self.stock <= self.reorder_level

class Sale(models.Model):
    PAYMENT_CHOICES = [('cash','Cash'),('card','Card'),('transfer','Transfer')]
    receipt_number = models.CharField(max_length=24, unique=True)
    sold_at = models.DateTimeField(auto_now_add=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default='cash')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    class Meta: ordering = ['-sold_at']

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def line_total(self): return self.quantity * self.unit_price
