import os
import django



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from celery import group
from base.models import Product
from base.tasks import attempt_purchase_task

def main():
    product = Product.objects.create(
        name="Chaos Product 1",
        total_stock=5,
        available_stock=5,
        reserved_stock=0,
        price=100
    )

    job = group(attempt_purchase_task.s(product.id) for _ in range(50))
    result = job.apply_async()
    outputs = result.get()

    succeeded = outputs.count("SUCCESS")
    failed = outputs.count("FAILURE")

    product.refresh_from_db()

    print("========== CHAOS TEST RESULT ==========")
    print(f"Succeeded count : {succeeded}")
    print(f"Failed count    : {failed}")
    print(f"Final stock     : {product.total_stock}")
    print("=======================================")

if __name__ == "__main__":
    main()
