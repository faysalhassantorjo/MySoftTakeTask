from django.db import transaction
from django.utils import timezone

from base.models import Order
from base.services.stock_service import (
    release_reserved_stock,
    confirm_reserved_stock,
)


@transaction.atomic
def change_order_status(order_id: int, new_status: str):

    order = Order.objects.select_for_update().get(id=order_id)
    old_status = order.status

    if old_status == new_status:
        return order

    invalid_transitions = {
        "CONFIRMED": ["CANCELLED", "EXPIRED"],
        "CANCELLED": ["CONFIRMED"],
        "EXPIRED": ["CONFIRMED"],
    }

    if old_status in invalid_transitions and new_status in invalid_transitions[old_status]:
        raise ValueError(f"Invalid status transition {old_status} → {new_status}")

    if new_status == "CONFIRMED":
        confirm_reserved_stock(order)

    elif new_status in ["CANCELLED", "EXPIRED"]:
        release_reserved_stock(order)


    order.status = new_status
    order.updated_at = timezone.now()
    order.save()

    return order
