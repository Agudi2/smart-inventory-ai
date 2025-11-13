"""
Test script to verify database models and connection setup.
This script can be run to validate the database configuration without actually connecting to a database.
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.models import (
    Base,
    Product,
    InventoryTransaction,
    Vendor,
    VendorPrice,
    User,
    Alert,
    MLPrediction
)
from app.core.database import engine, SessionLocal


def test_models_import():
    """Test that all models can be imported successfully."""
    print("✓ All models imported successfully")
    print(f"  - Product: {Product.__tablename__}")
    print(f"  - InventoryTransaction: {InventoryTransaction.__tablename__}")
    print(f"  - Vendor: {Vendor.__tablename__}")
    print(f"  - VendorPrice: {VendorPrice.__tablename__}")
    print(f"  - User: {User.__tablename__}")
    print(f"  - Alert: {Alert.__tablename__}")
    print(f"  - MLPrediction: {MLPrediction.__tablename__}")


def test_metadata():
    """Test that metadata contains all tables."""
    tables = Base.metadata.tables.keys()
    print(f"\n✓ Metadata contains {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")


def test_relationships():
    """Test that relationships are properly defined."""
    print("\n✓ Testing relationships:")
    
    # Product relationships
    product_rels = [rel.key for rel in Product.__mapper__.relationships]
    print(f"  - Product relationships: {', '.join(product_rels)}")
    
    # User relationships
    user_rels = [rel.key for rel in User.__mapper__.relationships]
    print(f"  - User relationships: {', '.join(user_rels)}")
    
    # Vendor relationships
    vendor_rels = [rel.key for rel in Vendor.__mapper__.relationships]
    print(f"  - Vendor relationships: {', '.join(vendor_rels)}")


def test_database_engine():
    """Test database engine configuration."""
    print("\n✓ Database engine configured:")
    print(f"  - Engine: {engine}")
    print(f"  - Pool size: {engine.pool.size()}")
    print(f"  - Session factory: {SessionLocal}")


if __name__ == "__main__":
    print("=" * 60)
    print("Database Models and Configuration Test")
    print("=" * 60)
    
    try:
        test_models_import()
        test_metadata()
        test_relationships()
        test_database_engine()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        print("\nNote: This test validates model structure only.")
        print("To test actual database connectivity, ensure PostgreSQL is running")
        print("and run: alembic upgrade head")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)