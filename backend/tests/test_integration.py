"""
Integration tests for backend API endpoints.

These tests verify end-to-end functionality of API endpoints including:
- Authentication flow
- Product management
- Barcode scanning
- Inventory transactions
- Prediction endpoints
- Database operations

Note: Uses SQLite for testing. For full PostgreSQL integration tests,
run the application with a test database and use the test scripts in the root directory.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import get_db
from app.models.base import Base


# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_integration_temp.db"


@pytest.fixture(scope="module")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    
    # Dispose engine to close all connections
    engine.dispose()
    
    # Clean up database file
    import time
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists("./test_integration_temp.db"):
                os.remove("./test_integration_temp.db")
            break
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(0.1)
            else:
                # If we still can't delete after retries, just pass
                pass


@pytest.fixture(scope="module")
def test_session_factory(test_engine):
    """Create session factory for tests."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def client(test_session_factory):
    """Create test client with database override."""
    def override_get_db():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestAuthenticationIntegration:
    """Integration tests for authentication endpoints."""
    
    def test_complete_auth_flow(self, client):
        """Test complete authentication flow: register -> login -> get user -> refresh."""
        # Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@test.com",
                "password": "TestPass123",
                "full_name": "Integration Test User"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "integration@test.com"
        assert "id" in user_data
        
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "integration@test.com",
                "password": "TestPass123"
            }
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "integration@test.com"
        
        # Refresh token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        # FastAPI returns 403 when no credentials are provided
        assert response.status_code in [401, 403]


class TestProductIntegration:
    """Integration tests for product endpoints."""
    
    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token for product tests."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "product@test.com",
                "password": "TestPass123",
                "full_name": "Product Test User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "product@test.com", "password": "TestPass123"}
        )
        return login_response.json()["access_token"]
    
    def test_product_crud_flow(self, client, auth_token):
        """Test complete product CRUD flow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create product
        create_response = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "INT-TEST-001",
                "name": "Integration Test Product",
                "category": "Test Category",
                "current_stock": 100,
                "reorder_threshold": 20,
                "unit_cost": 25.99
            }
        )
        assert create_response.status_code == 201
        product = create_response.json()
        product_id = product["id"]
        assert product["sku"] == "INT-TEST-001"
        
        # Get product
        get_response = client.get(
            f"/api/v1/products/{product_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["sku"] == "INT-TEST-001"
        
        # Update product
        update_response = client.put(
            f"/api/v1/products/{product_id}",
            headers=headers,
            json={"name": "Updated Product Name", "current_stock": 150}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated Product Name"
        assert updated["current_stock"] == 150
        
        # List products
        list_response = client.get("/api/v1/products", headers=headers)
        assert list_response.status_code == 200
        products = list_response.json()
        assert len(products) > 0
        assert any(p["id"] == product_id for p in products)
        
        # Delete product
        delete_response = client.delete(
            f"/api/v1/products/{product_id}",
            headers=headers
        )
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_deleted = client.get(
            f"/api/v1/products/{product_id}",
            headers=headers
        )
        assert get_deleted.status_code == 404


class TestBarcodeIntegration:
    """Integration tests for barcode scanning."""
    
    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "barcode@test.com",
                "password": "TestPass123",
                "full_name": "Barcode Test User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "barcode@test.com", "password": "TestPass123"}
        )
        return login_response.json()["access_token"]
    
    def test_barcode_scan_workflow(self, client, auth_token):
        """Test barcode scanning workflow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create product with barcode
        product_response = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "BARCODE-001",
                "name": "Barcode Product",
                "category": "Test",
                "current_stock": 50,
                "reorder_threshold": 10,
                "barcode": "1234567890123"
            }
        )
        assert product_response.status_code == 201
        
        # Scan existing barcode
        scan_response = client.post(
            "/api/v1/barcode/scan",
            headers=headers,
            json={"barcode": "1234567890123"}
        )
        assert scan_response.status_code == 200
        scan_data = scan_response.json()
        assert scan_data["found"] is True
        assert scan_data["product_name"] == "Barcode Product"
        
        # Scan non-existent barcode
        scan_missing = client.post(
            "/api/v1/barcode/scan",
            headers=headers,
            json={"barcode": "9999999999999"}
        )
        assert scan_missing.status_code == 200
        assert scan_missing.json()["found"] is False
        
        # Lookup barcode
        lookup_response = client.get(
            "/api/v1/barcode/lookup/1234567890123",
            headers=headers
        )
        assert lookup_response.status_code == 200
        lookup_data = lookup_response.json()
        assert lookup_data["found"] is True
        assert lookup_data["product_name"] == "Barcode Product"


class TestInventoryIntegration:
    """Integration tests for inventory operations."""
    
    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "inventory@test.com",
                "password": "TestPass123",
                "full_name": "Inventory Test User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "inventory@test.com", "password": "TestPass123"}
        )
        return login_response.json()["access_token"]
    
    def test_inventory_adjustment_workflow(self, client, auth_token):
        """Test inventory adjustment workflow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create product
        product_response = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "INV-001",
                "name": "Inventory Product",
                "category": "Test",
                "current_stock": 100,
                "reorder_threshold": 20
            }
        )
        product_id = product_response.json()["id"]
        
        # Add stock
        add_response = client.post(
            "/api/v1/inventory/adjust",
            headers=headers,
            json={
                "product_id": product_id,
                "quantity": 50,
                "reason": "Restocking"
            }
        )
        assert add_response.status_code == 200
        add_data = add_response.json()
        assert add_data["transaction_type"] == "addition"
        assert add_data["quantity"] == 50
        assert add_data["new_stock"] == 150
        
        # Remove stock
        remove_response = client.post(
            "/api/v1/inventory/adjust",
            headers=headers,
            json={
                "product_id": product_id,
                "quantity": -30,
                "reason": "Sale"
            }
        )
        assert remove_response.status_code == 200
        remove_data = remove_response.json()
        assert remove_data["transaction_type"] == "removal"
        assert remove_data["new_stock"] == 120
        
        # Try to remove more than available (should fail)
        invalid_response = client.post(
            "/api/v1/inventory/adjust",
            headers=headers,
            json={
                "product_id": product_id,
                "quantity": -200,
                "reason": "Should fail"
            }
        )
        assert invalid_response.status_code == 400
        
        # Get stock movements
        movements_response = client.get(
            "/api/v1/inventory/movements",
            headers=headers
        )
        assert movements_response.status_code == 200
        movements = movements_response.json()
        assert len(movements) >= 2
        
        # Get product history
        history_response = client.get(
            f"/api/v1/inventory/products/{product_id}/history",
            headers=headers
        )
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) >= 2


class TestPredictionIntegration:
    """Integration tests for prediction endpoints."""
    
    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "prediction@test.com",
                "password": "TestPass123",
                "full_name": "Prediction Test User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "prediction@test.com", "password": "TestPass123"}
        )
        return login_response.json()["access_token"]
    
    def test_prediction_endpoints(self, client, auth_token):
        """Test prediction endpoints."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create product
        product_response = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "PRED-001",
                "name": "Prediction Product",
                "category": "Test",
                "current_stock": 100,
                "reorder_threshold": 20
            }
        )
        product_id = product_response.json()["id"]
        
        # Get prediction (should return insufficient data or null prediction)
        prediction_response = client.get(
            f"/api/v1/predictions/{product_id}",
            headers=headers
        )
        # Should either return 200 with null prediction or 400 for insufficient data
        assert prediction_response.status_code in [200, 400]
        
        # Get batch predictions
        batch_response = client.get(
            "/api/v1/predictions/batch",
            headers=headers
        )
        # Should return 200 with list or 422 if validation fails
        assert batch_response.status_code in [200, 422]
        if batch_response.status_code == 200:
            assert isinstance(batch_response.json(), list)


class TestDatabaseIntegration:
    """Integration tests for database operations and constraints."""
    
    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "database@test.com",
                "password": "TestPass123",
                "full_name": "Database Test User"
            }
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "database@test.com", "password": "TestPass123"}
        )
        return login_response.json()["access_token"]
    
    def test_unique_constraints(self, client, auth_token):
        """Test unique constraints on SKU and barcode."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create first product
        client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "UNIQUE-001",
                "name": "First Product",
                "category": "Test",
                "current_stock": 100,
                "reorder_threshold": 20,
                "barcode": "1111111111111"
            }
        )
        
        # Try to create product with duplicate SKU
        duplicate_sku = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "UNIQUE-001",
                "name": "Duplicate SKU",
                "category": "Test",
                "current_stock": 50,
                "reorder_threshold": 10
            }
        )
        assert duplicate_sku.status_code == 400
        
        # Try to create product with duplicate barcode
        duplicate_barcode = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "UNIQUE-002",
                "name": "Duplicate Barcode",
                "category": "Test",
                "current_stock": 50,
                "reorder_threshold": 10,
                "barcode": "1111111111111"
            }
        )
        assert duplicate_barcode.status_code == 400
    
    def test_transaction_atomicity(self, client, auth_token):
        """Test that stock adjustments are atomic."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create product
        product_response = client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "sku": "ATOMIC-001",
                "name": "Atomic Test",
                "category": "Test",
                "current_stock": 100,
                "reorder_threshold": 20
            }
        )
        product_id = product_response.json()["id"]
        
        # Make valid adjustment
        client.post(
            "/api/v1/inventory/adjust",
            headers=headers,
            json={
                "product_id": product_id,
                "quantity": 20,
                "reason": "Test"
            }
        )
        
        # Make invalid adjustment (should fail)
        client.post(
            "/api/v1/inventory/adjust",
            headers=headers,
            json={
                "product_id": product_id,
                "quantity": -500,
                "reason": "Should fail"
            }
        )
        
        # Verify stock is correct (only first adjustment applied)
        product_check = client.get(
            f"/api/v1/products/{product_id}",
            headers=headers
        )
        assert product_check.json()["current_stock"] == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
