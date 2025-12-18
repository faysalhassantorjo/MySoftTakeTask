from django.db import models

# Create your models here.
from django.utils import timezone
import uuid
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=100)
    total_stock = models.IntegerField()
    available_stock = models.IntegerField()
    reserved_stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    def clean(self):
        assert self.available_stock + self.reserved_stock == self.total_stock

class Reservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    
    def get_price(self):
        return self.product.price * self.quantity
    



class Order(models.Model):
    STATUS = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    status = models.CharField(max_length=100, choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at', 'status'])
        ]

    def get_total_price(self):
        return sum(item.get_price() for item in self.items.all())    

    def __str__(self):
        return f"{self.user} - {self.status}"



class AuditLog(models.Model):
    actor = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
