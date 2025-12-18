from rest_framework import serializers
from .models import Product, Reservation, Order, AuditLog, OrderItem
from django.db import transaction
from datetime import timedelta
from django.utils import timezone

from .tasks import update_reservation, audit_log

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'is_active': {'read_only': True},
            'expires_at': {'read_only': True},
        }
    

    #  Reserve stock using DB lock (select_for_update) + transaction.atomic
    def create(self, validated_data):
        with transaction.atomic():
            product = validated_data['product'].select_for_update()
            quantity = validated_data['quantity']

            if product.available_stock < quantity:
                raise serializers.ValidationError("Not enough stock available")

            product.available_stock -= quantity
            product.reserved_stock += quantity
            product.save()

            reservation = Reservation.objects.create(**validated_data)

            serialized_data = ReservationSerializer(reservation).data

            object_type = reservation.__class__.__name__

            audit_log(actor="System", action="Reservation Created", obj_id=reservation.id, obj_type=object_type, old=None, new=serialized_data)

            reservation.expires_at = timezone.now() + timedelta(minutes=10)
            reservation.save()

            update_reservation.apply_async(args=[reservation.id], countdown=20)

            return reservation  

from django.contrib.auth.models import User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

from django_filters.rest_framework import FilterSet
class OrderSerializer(serializers.ModelSerializer):
    # user = UserSerializer()
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'user', 'get_total_price']



from django_filters import rest_framework as filters
from django.db.models import Sum, F
from .models import Order

class OrderFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    status = filters.ChoiceFilter(choices=Order.STATUS)

    min_total = filters.NumberFilter( method='filter_min_total')
    max_total = filters.NumberFilter(method='filter_max_total')

    class Meta:
        model = Order
        fields = ['status', 'start_date', 'end_date']

    def filter_min_total(self, queryset, name, value):
        return queryset.annotate(
            total=Sum(F('items__quantity') * F('items__product__price'))
        ).filter(total__gte=value)

    def filter_max_total(self, queryset, name, value):
        return queryset.annotate(
            total=Sum(F('items__quantity') * F('items__product__price'))
        ).filter(total__lte=value)

