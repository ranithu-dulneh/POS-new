from django.contrib import admin
from .models import Product, Order, OrderItem

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'product_code', 'price', 'stock_quantity')
    search_fields = ('name', 'barcode', 'product_code')
    list_filter = ('stock_quantity',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price_at_sale')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type', 'date_created', 'total_amount')
    list_filter = ('order_type', 'date_created')
    inlines = [OrderItemInline]
    date_hierarchy = 'date_created'

admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
