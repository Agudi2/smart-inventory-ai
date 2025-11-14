# Smart Inventory Management System - Backend

FastAPI backend for the Smart Inventory Management System with ML-powered stock prediction.

## Features

- RESTful API with FastAPI
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication
- ML-based stock depletion prediction
- Background tasks with Celery
- Barcode scanning integration
- Vendor management and price comparison

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. (Optional) Seed database with sample data:
```bash
python seed_data.py
```

For detailed database setup information, see [DATABASE_SETUP.md](DATABASE_SETUP.md)
For seed data documentation, see [SEED_DATA_README.md](SEED_DATA_README.md)

### Running the Application

#### Using Docker Compose (Recommended)

```bash
# Start all services (backend, database, redis, celery)
docker-compose up -d

# Start with database seeding (first time setup)
# Edit docker-compose.yml and set SEED_DATABASE: "true"
docker-compose up --build

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

#### Manual Development Mode

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start Celery worker (in a separate terminal):
```bash
celery -A app.core.celery_app:celery_app worker --loglevel=info
```

3. Start Celery Beat scheduler (in a separate terminal):
```bash
celery -A app.core.celery_app:celery_app beat --loglevel=info
```

### Background Tasks with Celery

The application uses Celery for background task processing:

- **ML Model Training**: Weekly training of forecasting models (Sundays at 2 AM)
- **Alert Checking**: Hourly checks for low stock and predicted depletion alerts
- **Auto-Resolve Alerts**: Every 6 hours, automatically resolve invalid alerts

For detailed Celery setup and usage, see [CELERY_SETUP.md](CELERY_SETUP.md)

#### Testing Celery Setup

```bash
python test_celery_setup.py
```

### API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Usage Guide

### Authentication Flow

The API uses JWT (JSON Web Token) authentication. Most endpoints require authentication.

#### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Login to Get Access Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Use Access Token in Requests

Include the access token in the `Authorization` header for all authenticated requests:

```bash
curl -X GET "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. Refresh Expired Token

When the access token expires (default: 15 minutes), use the refresh token to get a new one:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Common API Workflows

#### Product Management

**Create a Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "WDG-001",
    "name": "Widget A",
    "category": "Electronics",
    "current_stock": 100,
    "reorder_threshold": 20,
    "unit_cost": 12.99
  }'
```

**List Products with Filtering:**
```bash
# Get all products
curl -X GET "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by category
curl -X GET "http://localhost:8000/api/v1/products?category=Electronics" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search products
curl -X GET "http://localhost:8000/api/v1/products?search=widget" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update Product:**
```bash
curl -X PUT "http://localhost:8000/api/v1/products/PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_stock": 150,
    "reorder_threshold": 25
  }'
```

#### Inventory Management

**Adjust Stock Level:**
```bash
# Add stock (positive quantity)
curl -X POST "http://localhost:8000/api/v1/inventory/adjust" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "quantity": 50,
    "reason": "Received shipment from vendor"
  }'

# Remove stock (negative quantity)
curl -X POST "http://localhost:8000/api/v1/inventory/adjust" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "quantity": -10,
    "reason": "Sold to customer"
  }'
```

**View Stock Movement History:**
```bash
# All movements
curl -X GET "http://localhost:8000/api/v1/inventory/movements" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Movements for specific product
curl -X GET "http://localhost:8000/api/v1/inventory/movements?product_id=PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Product history
curl -X GET "http://localhost:8000/api/v1/inventory/products/PRODUCT_ID/history" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Barcode Scanning

**Scan a Barcode:**
```bash
curl -X POST "http://localhost:8000/api/v1/barcode/scan" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "012345678905"
  }'
```

**Lookup Barcode (GET):**
```bash
curl -X GET "http://localhost:8000/api/v1/barcode/lookup/012345678905" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Link Barcode to Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/barcode/link" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "012345678905",
    "product_id": "PRODUCT_ID"
  }'
```

#### ML Predictions

**Get Stock Depletion Prediction:**
```bash
curl -X GET "http://localhost:8000/api/v1/predictions/PRODUCT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Train ML Model for Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions/train" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "force_retrain": false
  }'
```

**Batch Predictions for All Products:**
```bash
curl -X GET "http://localhost:8000/api/v1/predictions/batch" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check Data Availability:**
```bash
curl -X GET "http://localhost:8000/api/v1/predictions/PRODUCT_ID/data-summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Vendor Management

**Create Vendor:**
```bash
curl -X POST "http://localhost:8000/api/v1/vendors" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Supplies",
    "contact_email": "sales@acme.com",
    "contact_phone": "+1-555-0100",
    "address": "123 Main St, City, State 12345"
  }'
```

**Add Vendor Price for Product:**
```bash
curl -X POST "http://localhost:8000/api/v1/vendors/VENDOR_ID/prices" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "unit_price": 12.99,
    "lead_time_days": 7,
    "minimum_order_quantity": 10
  }'
```

**Compare Vendors for Product:**
```bash
curl -X GET "http://localhost:8000/api/v1/products/PRODUCT_ID/vendors" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Alert Management

**List Active Alerts:**
```bash
# All alerts
curl -X GET "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/alerts?status=active" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by type and severity
curl -X GET "http://localhost:8000/api/v1/alerts?alert_type=low_stock&severity=critical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Acknowledge Alert:**
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/ALERT_ID/acknowledge" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Resolve Alert:**
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/ALERT_ID/resolve" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get/Update Alert Settings:**
```bash
# Get settings
curl -X GET "http://localhost:8000/api/v1/alerts/settings" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update settings
curl -X PUT "http://localhost:8000/api/v1/alerts/settings" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_threshold_days": 14,
    "low_stock_enabled": true,
    "predicted_depletion_enabled": true
  }'
```

### Health Check and Monitoring

**Health Check (No Authentication Required):**
```bash
curl -X GET "http://localhost:8000/health"
```

**System Metrics:**
```bash
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Error Handling

The API returns standard HTTP status codes and JSON error responses:

**Success Codes:**
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return

**Client Error Codes:**
- `400 Bad Request`: Invalid request data or business logic error
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

**Server Error Codes:**
- `500 Internal Server Error`: Unexpected server error

**Error Response Format:**
```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "type": "ExceptionClassName"
}
```

### Rate Limiting

API requests are rate-limited to ensure fair usage:
- Default: 100 requests per minute per IP address
- Authenticated users may have higher limits

### Pagination

List endpoints support pagination using `skip` and `limit` query parameters:

```bash
# Get first 10 products
curl -X GET "http://localhost:8000/api/v1/products?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get next 10 products
curl -X GET "http://localhost:8000/api/v1/products?skip=10&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Best Practices

1. **Token Management:**
   - Store access tokens securely (never in localStorage for production)
   - Implement automatic token refresh before expiration
   - Handle 401 errors by refreshing token and retrying request

2. **Error Handling:**
   - Always check response status codes
   - Parse error responses for detailed information
   - Implement retry logic for transient failures

3. **Performance:**
   - Use pagination for large datasets
   - Cache prediction results (they're cached server-side for 1 hour)
   - Batch operations when possible

4. **ML Predictions:**
   - Check data availability before requesting predictions
   - Products need minimum 30 days of transaction history
   - Train models weekly or after significant data changes
   - Use batch predictions for dashboard views

5. **Inventory Updates:**
   - Always provide a reason for stock adjustments
   - Use transactions for atomic operations
   - Monitor alerts after bulk stock changes

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoint routes
│   ├── core/                # Core configuration and utilities
│   │   ├── config.py        # Settings and environment config
│   │   ├── celery_app.py    # Celery configuration
│   │   └── exceptions.py    # Custom exceptions
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic schemas for validation
│   ├── services/            # Business logic layer
│   ├── ml/                  # Machine learning services
│   ├── tasks/               # Celery background tasks
│   │   ├── ml_tasks.py      # ML training tasks
│   │   └── alert_tasks.py   # Alert checking tasks
│   └── main.py              # FastAPI application entry point
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── CELERY_SETUP.md         # Celery documentation
└── .env.example            # Example environment variables
```

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `CORS_ORIGINS`: Allowed CORS origins for frontend

## License

MIT
