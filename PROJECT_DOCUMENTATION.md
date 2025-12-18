# Project Documentation

## Project Overview

This is a Django REST Framework-based **E-commerce Inventory Management System** with stock reservation capabilities, asynchronous task processing, and order management functionality.

**Created:** December 2025  
**Tech Stack:** Django 6.0, Django REST Framework, Celery, Redis, PostgreSQL, Docker

---

## Core Features Implemented

### 1. **Product & Inventory Management**
- Product model with stock tracking:
  - `total_stock`: Total available inventory
  - `available_stock`: Currently available for purchase
  - `reserved_stock`: Temporarily reserved inventory
- Stock validation ensures `available_stock + reserved_stock = total_stock`
- Price tracking with decimal precision

### 2. **Stock Reservation System**
- **Time-based reservations** with automatic expiration (10 minutes)
- **Pessimistic locking** using `select_for_update()` to prevent race conditions
- **Atomic transactions** to ensure data consistency
- **Background task scheduling** using Celery to auto-release expired reservations
- UUID-based reservation IDs for uniqueness

### 3. **Order Management**
- Multi-status order workflow:
  - `PENDING` → `CONFIRMED` → `PROCESSING` → `SHIPPED` → `DELIVERED`
  - Option to `CANCELLED` at appropriate stages
- **State machine validation** - only allowed transitions are permitted
- Order items with multiple products
- Automatic total price calculation
- User association for orders

### 4. **Advanced Order Querying**
- **Filtering capabilities:**
  - By status
  - By date range (`start_date`, `end_date`)
  - By total price range (`min_total`, `max_total`)
- **Cursor-based pagination** for efficient large dataset browsing
- **Query optimization** using `select_related` and `prefetch_related`
- **Database indexing** on frequently queried fields (`user + status`, `created_at + status`)

### 5. **Audit Logging**
- Complete audit trail for all critical operations:
  - Reservation creation
  - Reservation updates/expiration
  - Order status changes
- Tracks: actor, action, object type, object ID, old/new values, timestamp

### 6. **Asynchronous Task Processing**
- **Celery workers** for background task execution
- **Celery Beat** for scheduled/periodic tasks
- **Redis** as message broker
- Tasks implemented:
  - `update_reservation`: Auto-expires reservations after timeout
  - `reservation_cleanup`: Periodic cleanup of inactive reservations
  - `attempt_purchase_task`: Concurrent purchase simulation with pessimistic locking

### 7. **Dockerized Deployment**
Complete Docker Compose setup with 5 services:
- **web**: Django application server
- **redis**: Message broker for Celery
- **celery**: Worker for async tasks
- **celery-beat**: Scheduler for periodic tasks
- **db**: PostgreSQL database

---

## Technical Architecture

### Models (`base/models.py`)

#### Product
```python
- name: CharField
- total_stock: IntegerField
- available_stock: IntegerField
- reserved_stock: IntegerField
- price: DecimalField
```

#### Reservation
```python
- id: UUIDField (Primary Key)
- product: ForeignKey(Product)
- quantity: IntegerField
- expires_at: DateTimeField
- created_at: DateTimeField
- is_active: BooleanField
```

#### Order
```python
- status: CharField (choices: PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED)
- created_at: DateTimeField
- user: ForeignKey(User)
- Indexes: (user, status), (created_at, status)
```

#### OrderItem
```python
- order: ForeignKey(Order)
- product: ForeignKey(Product)
- quantity: IntegerField
- Method: get_price()
```

#### AuditLog
```python
- actor: CharField
- action: CharField
- object_type: CharField
- object_id: CharField
- old_value: JSONField
- new_value: JSONField
- timestamp: DateTimeField
```

### API Endpoints (`base/urls.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create-products/` | GET, POST | List all products or create new product |
| `/reservation/` | POST | Create a new stock reservation |
| `/create-order/` | GET, POST | List all orders or create new order |
| `/order/<id>/` | GET, PUT, PATCH | Retrieve or update specific order |
| `/order-list/` | GET | Paginated and filtered order list |

### Serializers (`base/serializers.py`)

- **ProductSerializer**: Full product serialization
- **ReservationSerializer**: Custom `create()` method with:
  - Database-level locking
  - Stock validation
  - Atomic transaction handling
  - Audit logging
  - Celery task scheduling
- **OrderSerializer**: Order with nested total price calculation
- **OrderFilter**: Django-filter integration for advanced querying

### Views (`base/views.py`)

- **CreateProductsView**: `ListCreateAPIView` for products
- **ReservationCreateView**: `CreateAPIView` with custom stock logic
- **OrderCreateView**: `ListCreateAPIView` for orders
- **OrderUpdateView**: `RetrieveUpdateAPIView` with state machine validation
- **OrderListView**: `ListAPIView` with:
  - Cursor pagination
  - DjangoFilterBackend integration
  - Query optimization
  - Ordering support

### Background Tasks (`base/tasks.py`)

- **audit_log()**: Helper function to create audit entries
- **update_reservation()**: Celery task to expire reservations and restore stock
- **reservation_cleanup()**: Scheduled task to clean up inactive reservations
- **attempt_purchase_task()**: Simulates concurrent purchase with locking

---

## Key Design Patterns & Best Practices

### 1. **Concurrency Control**
- **Pessimistic locking** with `select_for_update()` prevents double-booking
- **Atomic transactions** ensure all-or-nothing operations
- **Django F() expressions** for atomic database-level operations

### 2. **Performance Optimization**
- Database indexing on frequently queried fields
- `select_related()` for one-to-one/foreign key relationships
- `prefetch_related()` for reverse foreign keys and many-to-many
- Cursor-based pagination for efficient large result sets

### 3. **Data Integrity**
- Model-level validation (`clean()` method)
- Serializer validation for business logic
- State machine pattern for order status transitions
- Audit logging for compliance and debugging

### 4. **Scalability**
- Asynchronous task processing offloads heavy operations
- Redis for fast message brokering
- Docker containerization for easy deployment
- Postgres for robust data storage

### 5. **Code Organization**
- Separation of concerns (models, serializers, views, tasks)
- Read-only fields in serializers prevent unauthorized modifications
- Reusable audit logging function

---

## Docker Services Configuration

### Services
1. **web** (Django App): Port 8000
2. **redis**: Port 6379
3. **celery**: Background worker
4. **celery-beat**: Task scheduler
5. **db** (PostgreSQL): Port 5432

### Volumes
- Application code mounted for hot-reload during development
- PostgreSQL data persisted in named volume

---

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 6.0 | Web framework |
| djangorestframework | 3.16.1 | REST API framework |
| django-filter | 25.2 | Advanced filtering |
| celery | 5.6.0 | Async task queue |
| redis | ≥4.5 | Message broker |
| psycopg2-binary | Latest | PostgreSQL adapter |
| django-celery-beat | Latest | Periodic tasks |
| django-celery-results | 2.6.0 | Task result backend |

---

## Testing & Validation

### Chaos Testing
A `chaostest.py` file exists to simulate concurrent purchase scenarios and test the robustness of the locking mechanism.

---

## Security Considerations

- **Transaction isolation** prevents race conditions
- **State machine validation** prevents invalid order transitions
- **Read-only serializer fields** prevent field tampering
- **UUID for reservations** prevents enumeration attacks

---

## Future Enhancements (Potential)

- [ ] Add user authentication (JWT/OAuth)
- [ ] Implement payment gateway integration
- [ ] Add email notifications for order status changes
- [ ] Implement inventory alerts when stock is low
- [ ] Add analytics dashboard for order metrics
- [ ] Implement API rate limiting
- [ ] Add comprehensive test suite (unit, integration)
- [ ] Set up CI/CD pipeline
- [ ] Add API documentation (Swagger/OpenAPI)
- [ ] Implement caching layer (Redis cache)

---

## Development Notes

- Currently using SQLite for development (as evidenced by `db.sqlite3` file)
- PostgreSQL configured in Docker Compose for production-like environment
- Celery beat schedule file present (`celerybeat-schedule`)
- Git repository initialized

---

## How to Run

```bash
# Start all services with Docker Compose
docker compose up

# The application will be available at:
# - Django API: http://localhost:8000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

---

**Last Updated:** December 18, 2025
