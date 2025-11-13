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

Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python:
```bash
python -m app.main
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
│   │   └── exceptions.py    # Custom exceptions
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic schemas for validation
│   ├── services/            # Business logic layer
│   ├── ml/                  # Machine learning services
│   └── main.py              # FastAPI application entry point
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
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
