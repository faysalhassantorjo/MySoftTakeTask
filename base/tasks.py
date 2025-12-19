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

from django.db import transaction
from django.utils import timezone
from .models import Reservation, Product

@shared_task
def update_reservation(reservation_id):
    from .serializers import ReservationSerializer

    with transaction.atomic():

        reservation = (
            Reservation.objects
            .select_for_update()
            .select_related('product')
            .filter(id=reservation_id).first()
        )

        if not reservation:
            return {"reservation_id": reservation_id, "status": "Reservation Not Found"}

        old_data = ReservationSerializer(reservation).data

        product = reservation.product

        # restore stock
        product.available_stock += reservation.quantity
        product.reserved_stock -= reservation.quantity
        product.save()

        reservation.is_active = False
        reservation.save()

        new_data = ReservationSerializer(reservation).data

        audit_log(
            actor="System",
            action="Reservation Expired",
            obj_id=reservation.id,
            obj_type="Reservation",
            old=old_data,
            new=new_data
        )

    return {"reservation_id": reservation_id, "status": "Reservation Updated"}


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