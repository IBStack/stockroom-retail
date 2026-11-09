from django.contrib import admin
from .models import (Category, Customer, Product, Sale, SaleItem, Vendor, PurchaseOrder,
                     PurchaseOrderItem, StockAdjustment, Return, ReturnItem)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'email', 'phone')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'cost', 'stock', 'reorder_level', 'active')
    list_filter = ('category', 'active')
    search_fields = ('sku', 'name')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('unit_price',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'sold_at', 'cashier', 'customer', 'payment_method', 'total')
    list_filter = ('payment_method', 'sold_at')
    search_fields = ('receipt_number', 'customer__name')
    inlines = [SaleItemInline]
    readonly_fields = ('receipt_number', 'total', 'sold_at')


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'vendor', 'status', 'ordered_at', 'expected_at', 'received_at')
    list_filter = ('status', 'vendor')
    search_fields = ('order_number', 'vendor__name')
    inlines = [PurchaseOrderItemInline]


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'delta', 'reason', 'actor', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('product__name', 'product__sku', 'note')
    readonly_fields = ('created_at',)


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'sale', 'processed_by', 'total', 'created_at')
    search_fields = ('return_number', 'sale__receipt_number')
    inlines = [ReturnItemInline]
    readonly_fields = ('return_number', 'total', 'created_at')
