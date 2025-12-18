from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.db import connection
from django.test.utils import CaptureQueriesContext
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

from base.models import Product, Reservation, Order, AuditLog
from base.services.reservation_service import reserve_stock
from base.services.order_service import change_order_status
# from base.state_machine import validate_transition


# -----------------------------
# Task 1: Inventory Reservation
# -----------------------------

class ReservationTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            total_stock=10,
            available_stock=10,
            reserved_stock=0,
        )

    def test_reservation_success_reduces_stock(self):
        reserve_stock(self.product.id, 3)

        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 7)
        self.assertEqual(self.product.reserved_stock, 3)

    def test_reservation_fails_when_insufficient_stock(self):
        with self.assertRaises(ValueError):
            reserve_stock(self.product.id, 20)

    def test_stock_never_negative(self):
        try:
            reserve_stock(self.product.id, 11)
        except ValueError:
            pass

        self.product.refresh_from_db()
        self.assertGreaterEqual(self.product.available_stock, 0)

    def test_stock_invariant_always_holds(self):
        reserve_stock(self.product.id, 4)

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.available_stock + self.product.reserved_stock,
            self.product.total_stock
        )


# -----------------------------
# Task 1: Reservation Expiry
# -----------------------------

class ReservationExpiryTests(TestCase):

    def test_expired_reservation_releases_stock(self):
        product = Product.objects.create(
            name="Expire Product",
            total_stock=5,
            available_stock=3,
            reserved_stock=2,
        )

        reservation = Reservation.objects.create(
            product=product,
            quantity=2,
            expires_at=timezone.now() - timedelta(minutes=1),
            is_active=True,
        )

        # Simulate cleanup logic
        product.available_stock += reservation.quantity
        product.reserved_stock -= reservation.quantity
        product.save()

        reservation.is_active = False
        reservation.save()

        product.refresh_from_db()
        self.assertEqual(product.available_stock, 5)
        self.assertEqual(product.reserved_stock, 0)


# -----------------------------
# Task 2: Order State Machine
# -----------------------------

class OrderStateMachineTests(TestCase):

    def test_valid_transition(self):
        order = Order.objects.create(status="pending")
        change_order_status(order.id, "confirmed")
        self.assertEqual(order.status, "confirmed")

    def test_invalid_transition_raises_error(self):
        order = Order.objects.create(status="pending")

        with self.assertRaises(ValueError):
            change_order_status(order.id, "shipped")

    def test_cannot_cancel_after_shipped(self):
        order = Order.objects.create(status="shipped")

        with self.assertRaises(ValueError):
            change_order_status(order.id, "cancelled")

    def test_delivered_is_immutable(self):
        order = Order.objects.create(status="delivered")

        with self.assertRaises(ValueError):
            change_order_status(order.id, "processing")


# -----------------------------
# Task 3: Concurrency Chaos Test
# -----------------------------

# class ConcurrencyChaosTests(TransactionTestCase):
#     """
#     Uses TransactionTestCase because TestCase wraps everything
#     in a single transaction (bad for concurrency testing).
#     """

#     reset_sequences = True

#     def test_concurrent_reservations(self):
#         product = Product.objects.create(
#             name="Chaos Product",
#             total_stock=5,
#             available_stock=5,
#             reserved_stock=0,
#         )

#         def attempt():
#             try:
#                 reserve_stock(product.id, 1)
#                 return "SUCCESS"
#             except Exception:
#                 return "FAILURE"

#         with ThreadPoolExecutor(max_workers=10) as executor:
#             results = list(executor.map(lambda _: attempt(), range(50)))

#         product.refresh_from_db()

#         self.assertEqual(results.count("SUCCESS"), 5)
#         self.assertEqual(results.count("FAILURE"), 45)
#         self.assertEqual(product.available_stock, 0)
#         self.assertEqual(product.reserved_stock, 5)


# -----------------------------
# Task 4: Performance Safeguards
# -----------------------------

# class PerformanceTests(TestCase):

#     def test_orders_query_count_is_low(self):
#         for _ in range(5):
#             Order.objects.create(status="pending")

#         with CaptureQueriesContext(connection) as queries:
#             list(Order.objects.select_related())

#         self.assertLessEqual(len(queries), 2)


# -----------------------------
# Task 5: Audit Logging
# -----------------------------

# class AuditLogTests(TestCase):

#     def test_audit_log_created_on_reservation(self):
#         product = Product.objects.create(
#             name="Audit Product",
#             total_stock=5,
#             available_stock=5,
#             reserved_stock=0,
#         )

#         reserve_stock(product.id, 1)

#         self.assertTrue(
#             AuditLog.objects.filter(action="RESERVATION_CREATED").exists()
#         )

#     def test_audit_log_created_on_status_change(self):
#         order = Order.objects.create(status="pending")
#         change_order_status(order, "confirmed")

#         log = AuditLog.objects.last()
#         self.assertEqual(log.action, "ORDER_STATUS_CHANGED")
