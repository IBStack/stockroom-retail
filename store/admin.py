from django.contrib import admin
from .models import Category, Product, Sale, SaleItem
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): list_display = ('name',); search_fields = ('name',)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin): list_display = ('sku','name','category','price','stock','reorder_level','active'); list_filter = ('category','active'); search_fields = ('sku','name')
class SaleItemInline(admin.TabularInline): model = SaleItem; extra = 0; readonly_fields = ('unit_price',)
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin): list_display = ('receipt_number','sold_at','cashier','payment_method','total'); list_filter = ('payment_method','sold_at'); inlines = [SaleItemInline]; readonly_fields = ('receipt_number','total','sold_at')
