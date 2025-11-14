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

For detailed database setup information, see [DATABASE_SETUP.md](DATABASE_SETUP.md)

### Running the Application

#### Using Docker Compose (Recommended)

```bash
# Start all services (backend, database, redis, celery)
docker-compose up -d

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
