from celery import shared_task
from .models import Reservation, Product
from django.db import transaction
from django.db.models import F


from .models import AuditLog

def audit_log(actor, action, obj_id, obj_type, old=None, new=None):
    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            object_type=obj_type,
            object_id=obj_id,
            old_value=old,
            new_value=new
        )
    except Exception as e:
        print(e)

@shared_task
def update_reservation(reservation_id):
    from .serializers import ReservationSerializer

    reservation = Reservation.objects.filter(id=reservation_id)

    old_reservation = ReservationSerializer(reservation).data
    reservation.update(is_active=False)
    new_reservation = ReservationSerializer(reservation).data
    product = reservation.product
    product.available_stock += reservation.quantity
    product.reserved_stock -= reservation.quantity
    product.save()

    audit_log(actor="System", action="Reservation Updated", obj_id=reservation_id, obj_type="Reservation", old=old_reservation, new=new_reservation)
    return {'reservation_id': reservation_id}

@shared_task
def reservation_cleanup():

    reservations =Reservation.objects.filter(is_active=False)

    for reservation in reservations:
        update_reservation.delay(reservation.id)

    return "Reservation Cleanup Completed"


@shared_task(bind=True)
def attempt_purchase_task(self,product_id):
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        if product.total_stock > 0:
            product.total_stock = F('total_stock') - 1
            product.available_stock = F('available_stock') - 1
            product.reserved_stock = F('reserved_stock') + 1
            product.save(update_fields=["total_stock","available_stock","reserved_stock"])
            return "SUCCESS"
        else:
            return "FAILURE"    