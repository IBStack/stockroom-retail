from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name


class Customer(models.Model):
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name


class Vendor(models.Model):
    name = models.CharField(max_length=160, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
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
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
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


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [('draft','Draft'),('sent','Sent'),('partial','Partially received'),('received','Received'),('cancelled','Cancelled')]
    order_number = models.CharField(max_length=24, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    ordered_at = models.DateTimeField(auto_now_add=True)
    expected_at = models.DateField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    class Meta: ordering = ['-ordered_at']
    def __str__(self): return self.order_number
    @property
    def total(self): return sum((item.line_total for item in self.items.all()), Decimal('0.00'))


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def line_total(self): return self.quantity_ordered * self.unit_cost
    @property
    def outstanding(self): return max(self.quantity_ordered - self.quantity_received, 0)


class StockAdjustment(models.Model):
    REASON_CHOICES = [('sale','Sale'),('purchase','Purchase receipt'),('return','Customer return'),('manual','Manual count'),('correction','Correction')]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='adjustments')
    delta = models.IntegerField()
    reason = models.CharField(max_length=12, choices=REASON_CHOICES)
    note = models.CharField(max_length=240, blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']


class Return(models.Model):
    return_number = models.CharField(max_length=24, unique=True)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='returns')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=240, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']


class ReturnItem(models.Model):
    return_record = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def line_total(self): return self.quantity * self.unit_price
