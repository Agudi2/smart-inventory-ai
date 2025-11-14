"""Integration test for Celery tasks with database."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models.product import Product
from app.models.inventory_transaction import InventoryTransaction
from app.services.alert_service import AlertService
from app.ml.prediction_service import MLPredictionService


def test_alert_service():
    """Test alert service with database."""
    print("\n" + "=" * 60)
    print("Testing Alert Service")
    print("=" * 60)
    
    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Initialize alert service
        alert_service = AlertService(db)
        
        # Test low stock alerts
        print("\n1. Checking low stock alerts...")
        low_stock_alerts = alert_service.check_low_stock_alerts()
        print(f"   Found {len(low_stock_alerts)} low stock alerts")
        
        # Test prediction alerts
        print("\n2. Checking prediction alerts...")
        prediction_alerts = alert_service.check_prediction_alerts()
        print(f"   Found {len(prediction_alerts)} prediction alerts")
        
        # Test auto-resolve
        print("\n3. Testing auto-resolve...")
        resolved_count = alert_service.auto_resolve_alerts()
        print(f"   Auto-resolved {resolved_count} alerts")
        
        db.close()
        print("\n✓ Alert service tests completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Alert service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_prediction_service():
    """Test ML prediction service with database."""
    print("\n" + "=" * 60)
    print("Testing ML Prediction Service")
    print("=" * 60)
    
    try:
        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Initialize prediction service
        prediction_service = MLPredictionService(db)
        
        # Get a product with data
        print("\n1. Finding products with sufficient data...")
        products = db.query(Product).limit(10).all()
        
        products_with_data = []
        for product in products:
            has_sufficient, days = prediction_service.has_sufficient_data(product.id)
            if has_sufficient:
                products_with_data.append((product, days))
                print(f"   ✓ Product '{product.name}' has {days} days of data")
        
        if not products_with_data:
            print("   No products with sufficient data found")
            print("   This is expected if the database is empty or has limited data")
            db.close()
            return True
        
        # Test data summary
        print("\n2. Getting data summary for first product...")
        test_product, _ = products_with_data[0]
        summary = prediction_service.get_data_summary(test_product.id)
        print(f"   Product: {test_product.name}")
        print(f"   Days of data: {summary.get('days_of_data', 0)}")
        print(f"   Has sufficient data: {summary.get('has_sufficient_data', False)}")
        
        db.close()
        print("\n✓ ML prediction service tests completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ ML prediction service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        engine = create_engine(settings.database_url)
        connection = engine.connect()
        connection.close()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. Database exists and is accessible")
        print("3. DATABASE_URL in .env is correct")
        return False


def main():
    """Run integration tests."""
    print("=" * 60)
    print("Celery Integration Tests")
    print("=" * 60)
    print("\nThese tests verify that Celery tasks can interact with the database")
    print("and perform their intended operations.")
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Only run other tests if database is accessible
    if results[0][1]:
        # Test 2: Alert service
        results.append(("Alert Service", test_alert_service()))
        
        # Test 3: ML prediction service
        results.append(("ML Prediction Service", test_ml_prediction_service()))
    else:
        print("\nSkipping other tests due to database connection failure")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✓ All integration tests passed!")
        print("Celery tasks should work correctly with the database.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
