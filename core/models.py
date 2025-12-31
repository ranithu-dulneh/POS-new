from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=100, unique=True, db_index=True)
    product_code = models.CharField(max_length=50, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.product_code})"

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('ONLINE', 'Online'),
        ('POS', 'In-Shop POS'),
    ]

    date_created = models.DateTimeField(default=timezone.now)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} - {self.get_order_type_display()} - {self.date_created.strftime('%Y-%m-%d')}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.price_at_sale and self.product:
            self.price_at_sale = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted Product"
        return f"{product_name} x {self.quantity}"
