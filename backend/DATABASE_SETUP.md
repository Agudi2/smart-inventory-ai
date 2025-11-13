# Database Setup Guide

This document describes the database models, migrations, and setup process for the Smart Inventory Management System.

## Database Models

The system uses SQLAlchemy ORM with the following models:

### 1. Product
- **Table**: `products`
- **Description**: Stores product information and inventory levels
- **Key Fields**: sku, name, category, current_stock, reorder_threshold, barcode, unit_cost
- **Relationships**: inventory_transactions, vendor_prices, alerts, ml_predictions

### 2. InventoryTransaction
- **Table**: `inventory_transactions`
- **Description**: Records all stock movements (additions, removals, adjustments)
- **Key Fields**: product_id, transaction_type, quantity, previous_stock, new_stock, reason
- **Relationships**: product, user

### 3. Vendor
- **Table**: `vendors`
- **Description**: Stores supplier information
- **Key Fields**: name, contact_email, contact_phone, address
- **Relationships**: vendor_prices

### 4. VendorPrice
- **Table**: `vendor_prices`
- **Description**: Links vendors to products with pricing information
- **Key Fields**: vendor_id, product_id, unit_price, lead_time_days, minimum_order_quantity
- **Relationships**: vendor, product
- **Constraints**: Unique constraint on (vendor_id, product_id)

### 5. User
- **Table**: `users`
- **Description**: User accounts for authentication and authorization
- **Key Fields**: email, hashed_password, full_name, role, is_active
- **Relationships**: inventory_transactions

### 6. Alert
- **Table**: `alerts`
- **Description**: Low stock and predicted depletion notifications
- **Key Fields**: product_id, alert_type, severity, message, status
- **Relationships**: product

### 7. MLPrediction
- **Table**: `ml_predictions`
- **Description**: Machine learning predictions for stock depletion
- **Key Fields**: product_id, predicted_depletion_date, confidence_score, daily_consumption_rate
- **Relationships**: product

## Database Connection

The database connection is managed in `app/core/database.py` with the following features:

- **Connection Pooling**: QueuePool with 5 connections, max overflow of 10
- **Pool Pre-ping**: Verifies connections before use
- **Connection Recycling**: Recycles connections after 1 hour
- **Session Management**: Context manager for automatic session cleanup

### Usage Example

```python
from app.core.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
```

## Alembic Migrations

Alembic is configured for database migrations with the following structure:

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_migration.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
```

### Migration Commands

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback one migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

**View current version:**
```bash
alembic current
```

## Initial Setup

### 1. Start PostgreSQL Database

Using Docker Compose (recommended):
```bash
docker-compose up -d db
```

Or start PostgreSQL manually on port 5432.

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update the database URL:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/inventory
```

### 3. Run Migrations

Apply the initial migration to create all tables:
```bash
cd backend
alembic upgrade head
```

### 4. Verify Setup

Run the test script to verify models and configuration:
```bash
python test_db_setup.py
```

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐
│   Product   │
├─────────────┤
│ id (PK)     │
│ sku (UQ)    │
│ name        │
│ category    │
│ barcode (UQ)│
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
       ▼                              ▼
┌──────────────────────┐    ┌─────────────────┐
│ InventoryTransaction │    │  VendorPrice    │
├──────────────────────┤    ├─────────────────┤
│ id (PK)              │    │ id (PK)         │
│ product_id (FK)      │    │ product_id (FK) │
│ transaction_type     │    │ vendor_id (FK)  │
│ quantity             │    │ unit_price      │
│ user_id (FK)         │    └────────┬────────┘
└──────────────────────┘             │
                                     ▼
┌─────────────┐              ┌─────────────┐
│    User     │              │   Vendor    │
├─────────────┤              ├─────────────┤
│ id (PK)     │              │ id (PK)     │
│ email (UQ)  │              │ name        │
│ role        │              │ contact     │
└─────────────┘              └─────────────┘

       ┌──────────────────────────────┐
       │                              │
       ▼                              ▼
┌─────────────┐              ┌──────────────┐
│   Alert     │              │ MLPrediction │
├─────────────┤              ├──────────────┤
│ id (PK)     │              │ id (PK)      │
│ product_id  │              │ product_id   │
│ alert_type  │              │ depl_date    │
│ status      │              │ confidence   │
└─────────────┘              └──────────────┘
```

## Indexes

The following indexes are created for query optimization:

- **products**: sku, category, barcode
- **inventory_transactions**: product_id, created_at
- **vendor_prices**: product_id
- **users**: email
- **alerts**: product_id, status
- **ml_predictions**: product_id, created_at

## Foreign Key Constraints

All foreign keys use `CASCADE` delete to maintain referential integrity:

- When a product is deleted, all related transactions, vendor prices, alerts, and predictions are deleted
- When a vendor is deleted, all related vendor prices are deleted
- User deletion does not cascade (transactions retain user_id for audit trail)

## Connection Pooling Configuration

The database engine is configured with:

- **Pool Size**: 5 connections
- **Max Overflow**: 10 additional connections
- **Pool Pre-ping**: Enabled (verifies connections)
- **Pool Recycle**: 3600 seconds (1 hour)
- **Echo**: Enabled in debug mode

## Troubleshooting

### Connection Refused Error

If you see "connection refused" errors:
1. Ensure PostgreSQL is running: `docker-compose ps`
2. Check the DATABASE_URL in your .env file
3. Verify PostgreSQL is listening on the correct port

### Migration Conflicts

If migrations fail:
1. Check current version: `alembic current`
2. View migration history: `alembic history`
3. Manually resolve conflicts or downgrade: `alembic downgrade -1`

### Model Changes Not Detected

If Alembic doesn't detect model changes:
1. Ensure all models are imported in `app/models/__init__.py`
2. Verify models inherit from `Base`
3. Check that `alembic/env.py` imports all models

## Best Practices

1. **Always use migrations** - Never modify the database schema directly
2. **Test migrations** - Test on a development database before production
3. **Use transactions** - Wrap multi-step operations in database transactions
4. **Close sessions** - Always use `get_db()` dependency for automatic cleanup
5. **Index strategically** - Add indexes for frequently queried columns
6. **Monitor pool** - Watch connection pool usage in production

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
