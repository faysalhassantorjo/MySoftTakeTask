from django.contrib import admin

# Register your models here.
from .models import Product, Reservation, Order, OrderItem, AuditLog
admin.site.register(Product)
admin.site.register(Reservation)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(AuditLog)
