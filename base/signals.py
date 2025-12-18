from .models import Order
from django.db.models.signals import post_save
from django.dispatch import receiver
from .serializers import OrderSerializer

from .tasks import audit_log

@receiver(post_save, sender=Order)
def update_order(sender, instance, **kwargs):
    old_instance = Order.objects.get(id=instance.id)
    old_instance = OrderSerializer(old_instance)
    new_instance = OrderSerializer(instance)
    audit_log(
        actor="System",
        action="Order Updated",
        obj_id=instance.id,
        obj_type="Order",
        old=old_instance.data,
        new=new_instance.data
    )
