from django.urls import path
from .views import ReservationCreateView, OrderUpdateView, OrderListView, CreateProductsView, OrderCreateView, OrderItemCreateView

urlpatterns = [
    path('create-products/', CreateProductsView.as_view(), name='create-products'),
    path('reservation/', ReservationCreateView.as_view(), name='reservation-create'),
    path('create-order/', OrderCreateView.as_view(), name='create-order'),
    path('order-item/', OrderItemCreateView.as_view(), name='order-item-create'),
    path('order/<int:pk>/', OrderUpdateView.as_view(), name='order-update'),
    path('order-list/', OrderListView.as_view(), name='order-list'),
]