from rest_framework.views import APIView
from rest_framework import generics
from .tasks import audit_log
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Reservation, Order, OrderItem
from .serializers import ProductSerializer, ReservationSerializer, OrderSerializer, OrderItemSerializer

# Create your views here.
class CreateProductsView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer    

class ReservationCreateView(generics.ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

class RetrieveReservationView(generics.RetrieveAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

class OrderCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class OrderItemCreateView(generics.ListCreateAPIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class OrderUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    lookup_field = 'pk'


    def update(self, request, *args, **kwargs):

        ALLOWED_TRANSITIONS = {
            "PENDING": {"CONFIRMED", "CANCELLED"},
            "CONFIRMED": {"PROCESSING", "CANCELLED"},
            "PROCESSING": {"SHIPPED"},
            "SHIPPED": {"DELIVERED"},
            "DELIVERED": set(),
            "CANCELLED": set(),
        }

        instance = self.get_object()
        current_status = instance.status

        new_status = request.data.get('status', current_status)

        if new_status in ALLOWED_TRANSITIONS[current_status]:

            instance.status = new_status
            instance.save()



            audit_log(
                actor="System",
                action="Order Status Updated",
                obj_id= instance.id,
                obj_type=instance.__class__.__name__,
                old= current_status ,
                new=new_status
            )

            return Response(
                {
                    'order':OrderSerializer(instance).data,
                    'new_status': new_status,
                    'current_status': current_status
                }
            )

        return Response(
            {
                "error": "Invalid status transition", 
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )



from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .serializers import OrderFilter
from django.db.models import Sum, F

from rest_framework.pagination import CursorPagination

class OrderCursorPagination(CursorPagination):
    page_size = 2
    cursor_query_param = 'cursor'
    ordering = '-created_at'


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderCursorPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
      return Order.objects.select_related('user').prefetch_related('items__product').all()

from .models import AuditLog
from .serializers import AuditLogSerializer
class AuditLogView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
