from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from base.models import Product, Reservation


@transaction.atomic
def reserve_stock(product_id: int, quantity: int):
    """
    Reserve product stock safely under concurrency.

    Guarantees:
    - available_stock never goes negative
    - stock invariant is preserved
    - operation is atomic
    """

    # 🔒 Lock the product row
    product = Product.objects.select_for_update().get(id=product_id)

    # ✅ Validate inside the lock
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    if product.available_stock < quantity:
        raise ValueError("Insufficient stock")

    # 🔄 Update stock
    product.available_stock -= quantity
    product.reserved_stock += quantity
    product.save()

    # ⏳ Create time-bound reservation
    reservation = Reservation.objects.create(
        product=product,
        quantity=quantity,
        expires_at=timezone.now() + timedelta(minutes=10),
        is_active=True,
    )


    return reservation
