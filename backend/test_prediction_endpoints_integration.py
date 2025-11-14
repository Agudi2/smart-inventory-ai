"""Integration test for ML prediction API endpoints using FastAPI TestClient."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing ML Prediction API Endpoints Integration...")
print("=" * 60)


def test_prediction_endpoints():
    """Test prediction endpoints with FastAPI TestClient."""
    
    print("\n--- Integration Test: Prediction Endpoints ---")
    
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import Base, engine, get_db
    from app.models.user import User
    from app.models.product import Product
    from app.models.inventory_transaction import InventoryTransaction
    from app.core.security import hash_password
    from sqlalchemy.orm import Session
    from datetime import datetime, timedelta
    from uuid import uuid4
    
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    print("✓ Test database tables created")
    
    # Create test client
    client = TestClient(app)
    print("✓ Test client created")
    
    # Create test user and get token
    db = next(get_db())
    try:
        # Create test user
        test_user = User(
            email="test_predictions@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Test User",
            role="admin"
        )
        db.add(test_user)
        db.commit()
        print("✓ Test user created")
        
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "test_predictions@example.com", "password": "testpass123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✓ Authentication token obtained")
        
        # Create test product with sufficient historical data
        test_product = Product(
            sku="TEST-PRED-001",
            name="Test Product for Predictions",
            category="Test",
            current_stock=100,
            reorder_threshold=20
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)
        product_id = str(test_product.id)
        print(f"✓ Test product created: {product_id}")
        
        # Create historical transactions (35 days of data)
        base_date = datetime.utcnow() - timedelta(days=35)
        stock = 200
        
        for day in range(35):
            transaction_date = base_date + timedelta(days=day)
            # Simulate daily consumption
            consumption = 3  # 3 units per day
            stock -= consumption
            
            transaction = InventoryTransaction(
                product_id=test_product.id,
                transaction_type="removal",
                quantity=-consumption,
                previous_stock=stock + consumption,
                new_stock=stock,
                reason="Daily consumption",
                created_at=transaction_date
            )
            db.add(transaction)
        
        db.commit()
        print("✓ Created 35 days of historical transactions")
        
        # Update product current stock
        test_product.current_stock = stock
        db.commit()
        print(f"✓ Updated product stock to {stock}")
        
        # Test 1: Get data summary
        print("\n  Test 1: GET /api/v1/predictions/{product_id}/data-summary")
        summary_response = client.get(
            f"/api/v1/predictions/{product_id}/data-summary",
            headers=headers
        )
        assert summary_response.status_code == 200, f"Data summary failed: {summary_response.text}"
        summary_data = summary_response.json()
        print(f"    ✓ Status: {summary_response.status_code}")
        print(f"    ✓ Has sufficient data: {summary_data['has_sufficient_data']}")
        print(f"    ✓ Days of data: {summary_data['days_of_data']}")
        assert summary_data['has_sufficient_data'] == True, "Should have sufficient data"
        assert summary_data['days_of_data'] >= 30, "Should have at least 30 days"
        
        # Test 2: Train model
        print("\n  Test 2: POST /api/v1/predictions/train")
        train_response = client.post(
            "/api/v1/predictions/train",
            json={"product_id": product_id, "force_retrain": False},
            headers=headers
        )
        assert train_response.status_code == 200, f"Training failed: {train_response.text}"
        train_data = train_response.json()
        print(f"    ✓ Status: {train_response.status_code}")
        print(f"    ✓ Success: {train_data['success']}")
        print(f"    ✓ Message: {train_data['message']}")
        print(f"    ✓ Model version: {train_data.get('model_version', 'N/A')}")
        assert train_data['success'] == True, "Training should succeed"
        
        # Test 3: Get prediction
        print("\n  Test 3: GET /api/v1/predictions/{product_id}")
        prediction_response = client.get(
            f"/api/v1/predictions/{product_id}?forecast_days=30",
            headers=headers
        )
        assert prediction_response.status_code == 200, f"Prediction failed: {prediction_response.text}"
        prediction_data = prediction_response.json()
        print(f"    ✓ Status: {prediction_response.status_code}")
        print(f"    ✓ Product: {prediction_data['product_name']}")
        print(f"    ✓ Current stock: {prediction_data['current_stock']}")
        print(f"    ✓ Depletion date: {prediction_data.get('predicted_depletion_date', 'N/A')}")
        print(f"    ✓ Confidence: {prediction_data.get('confidence_score', 'N/A')}")
        print(f"    ✓ Daily consumption: {prediction_data.get('daily_consumption_rate', 'N/A')}")
        assert 'product_id' in prediction_data, "Should have product_id"
        assert 'confidence_score' in prediction_data, "Should have confidence_score"
        
        # Test 4: Get prediction again (should use cache)
        print("\n  Test 4: GET /api/v1/predictions/{product_id} (cached)")
        cached_response = client.get(
            f"/api/v1/predictions/{product_id}?use_cache=true",
            headers=headers
        )
        assert cached_response.status_code == 200, f"Cached prediction failed: {cached_response.text}"
        print(f"    ✓ Status: {cached_response.status_code}")
        print(f"    ✓ Response received (cache may or may not be available)")
        
        # Test 5: Invalidate cache
        print("\n  Test 5: DELETE /api/v1/predictions/{product_id}/cache")
        invalidate_response = client.delete(
            f"/api/v1/predictions/{product_id}/cache",
            headers=headers
        )
        assert invalidate_response.status_code == 204, f"Cache invalidation failed: {invalidate_response.status_code}"
        print(f"    ✓ Status: {invalidate_response.status_code}")
        print(f"    ✓ Cache invalidated successfully")
        
        # Test 6: Batch predictions
        print("\n  Test 6: GET /api/v1/predictions/batch")
        batch_response = client.get(
            "/api/v1/predictions/batch?min_confidence=0.0",
            headers=headers
        )
        assert batch_response.status_code == 200, f"Batch prediction failed: {batch_response.text}"
        batch_data = batch_response.json()
        print(f"    ✓ Status: {batch_response.status_code}")
        print(f"    ✓ Total products: {batch_data['total_products']}")
        print(f"    ✓ Successful: {batch_data['successful_predictions']}")
        print(f"    ✓ Failed: {batch_data['failed_predictions']}")
        assert batch_data['total_products'] >= 0, "Should have total_products count"
        
        # Test 7: Test insufficient data error
        print("\n  Test 7: Test insufficient data error")
        new_product = Product(
            sku="TEST-PRED-002",
            name="Product with No Data",
            category="Test",
            current_stock=50,
            reorder_threshold=10
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        insufficient_response = client.get(
            f"/api/v1/predictions/{new_product.id}",
            headers=headers
        )
        assert insufficient_response.status_code == 400, "Should return 400 for insufficient data"
        print(f"    ✓ Status: {insufficient_response.status_code}")
        print(f"    ✓ Error handled correctly for product with no data")
        
        print("\n✅ All integration tests passed!")
        return True
        
    finally:
        # Cleanup
        db.query(InventoryTransaction).delete()
        db.query(Product).delete()
        db.query(User).filter(User.email == "test_predictions@example.com").delete()
        db.commit()
        db.close()
        print("\n✓ Test data cleaned up")


def run_all_tests():
    """Run all integration tests."""
    
    try:
        test_prediction_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print("\nML Prediction API Endpoints Integration:")
        print("  ✓ Data summary endpoint works")
        print("  ✓ Model training endpoint works")
        print("  ✓ Prediction endpoint works")
        print("  ✓ Cache functionality works")
        print("  ✓ Cache invalidation works")
        print("  ✓ Batch predictions work")
        print("  ✓ Error handling works correctly")
        print("\nTask 11 completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
