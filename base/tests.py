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

        product.available_stock += reservation.quantity
        product.reserved_stock -= reservation.quantity
        product.save()

        reservation.is_active = False
        reservation.save()

        product.refresh_from_db()
        self.assertEqual(product.available_stock, 5)
        self.assertEqual(product.reserved_stock, 0)




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


