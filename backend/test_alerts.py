"""Tests for alert system functionality."""

import pytest
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.product import Product
from app.models.user import User
from app.models.alert import Alert
from app.models.ml_prediction import MLPrediction
from app.core.security import hash_password, create_access_token


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_product(db_session):
    """Create a test product."""
    product = Product(
        sku="TEST-001",
        name="Test Product",
        category="Test Category",
        current_stock=5,
        reorder_threshold=10,
        unit_cost=10.00
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture(scope="function")
def test_product_critical(db_session):
    """Create a test product with critical stock."""
    product = Product(
        sku="TEST-002",
        name="Critical Product",
        category="Test Category",
        current_stock=0,
        reorder_threshold=10,
        unit_cost=15.00
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


def test_check_low_stock_alerts(db_session, test_product):
    """Test low stock alert generation."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    alerts = alert_service.check_low_stock_alerts()
    
    # Should create one alert for the low stock product
    assert len(alerts) == 1
    assert alerts[0].product_id == test_product.id
    assert alerts[0].alert_type == "low_stock"
    assert alerts[0].severity == "warning"
    assert alerts[0].status == "active"


def test_check_low_stock_alerts_critical(db_session, test_product_critical):
    """Test critical stock alert generation."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    alerts = alert_service.check_low_stock_alerts()
    
    # Should create one critical alert for out of stock product
    assert len(alerts) == 1
    assert alerts[0].product_id == test_product_critical.id
    assert alerts[0].alert_type == "low_stock"
    assert alerts[0].severity == "critical"
    assert "out of stock" in alerts[0].message.lower()


def test_check_prediction_alerts(db_session, test_product):
    """Test predicted depletion alert generation."""
    from app.services.alert_service import AlertService
    
    # Create a prediction with depletion in 5 days
    prediction = MLPrediction(
        product_id=test_product.id,
        predicted_depletion_date=date.today() + timedelta(days=5),
        confidence_score=0.85,
        daily_consumption_rate=1.0,
        model_version="test-v1"
    )
    db_session.add(prediction)
    db_session.commit()
    
    alert_service = AlertService(db_session)
    alerts = alert_service.check_prediction_alerts()
    
    # Should create one alert for predicted depletion
    assert len(alerts) == 1
    assert alerts[0].product_id == test_product.id
    assert alerts[0].alert_type == "predicted_depletion"
    assert alerts[0].status == "active"


def test_no_duplicate_alerts(db_session, test_product):
    """Test that duplicate alerts are not created."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    
    # Create alerts twice
    alerts1 = alert_service.check_low_stock_alerts()
    alerts2 = alert_service.check_low_stock_alerts()
    
    # Should return the same alert, not create a duplicate
    assert len(alerts1) == 1
    assert len(alerts2) == 1
    assert alerts1[0].id == alerts2[0].id


def test_acknowledge_alert(db_session, test_product):
    """Test acknowledging an alert."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    
    # Create an alert
    alerts = alert_service.check_low_stock_alerts()
    alert = alerts[0]
    
    # Acknowledge the alert
    acknowledged_alert = alert_service.acknowledge_alert(alert.id)
    
    assert acknowledged_alert.status == "acknowledged"
    assert acknowledged_alert.acknowledged_at is not None


def test_resolve_alert(db_session, test_product):
    """Test resolving an alert."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    
    # Create an alert
    alerts = alert_service.check_low_stock_alerts()
    alert = alerts[0]
    
    # Resolve the alert
    resolved_alert = alert_service.resolve_alert(alert.id)
    
    assert resolved_alert.status == "resolved"
    assert resolved_alert.resolved_at is not None
    assert resolved_alert.acknowledged_at is not None


def test_auto_resolve_low_stock_alerts(db_session, test_product):
    """Test auto-resolving low stock alerts when stock is replenished."""
    from app.services.alert_service import AlertService
    
    alert_service = AlertService(db_session)
    
    # Create a low stock alert
    alerts = alert_service.check_low_stock_alerts()
    assert len(alerts) == 1
    assert alerts[0].status == "active"
    
    # Replenish stock
    test_product.current_stock = 20
    db_session.commit()
    
    # Auto-resolve alerts
    resolved_count = alert_service.auto_resolve_alerts()
    
    assert resolved_count == 1
    
    # Check that the alert is now resolved
    db_session.refresh(alerts[0])
    assert alerts[0].status == "resolved"


def test_list_alerts_api(client, auth_headers, db_session, test_product):
    """Test listing alerts via API."""
    from app.services.alert_service import AlertService
    
    # Create some alerts
    alert_service = AlertService(db_session)
    alert_service.check_low_stock_alerts()
    
    # List alerts
    response = client.get("/api/v1/alerts", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["alert_type"] == "low_stock"
    assert data[0]["product_name"] == "Test Product"


def test_acknowledge_alert_api(client, auth_headers, db_session, test_product):
    """Test acknowledging an alert via API."""
    from app.services.alert_service import AlertService
    
    # Create an alert
    alert_service = AlertService(db_session)
    alerts = alert_service.check_low_stock_alerts()
    alert_id = str(alerts[0].id)
    
    # Acknowledge via API
    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
    assert data["acknowledged_at"] is not None


def test_resolve_alert_api(client, auth_headers, db_session, test_product):
    """Test resolving an alert via API."""
    from app.services.alert_service import AlertService
    
    # Create an alert
    alert_service = AlertService(db_session)
    alerts = alert_service.check_low_stock_alerts()
    alert_id = str(alerts[0].id)
    
    # Resolve via API
    response = client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None


def test_get_alert_settings_api(client, auth_headers):
    """Test getting alert settings via API."""
    response = client.get("/api/v1/alerts/settings", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "alert_threshold_days" in data
    assert "low_stock_enabled" in data
    assert "predicted_depletion_enabled" in data


def test_update_alert_settings_api(client, auth_headers):
    """Test updating alert settings via API."""
    update_data = {
        "alert_threshold_days": 14,
        "low_stock_enabled": True,
        "predicted_depletion_enabled": False
    }
    
    response = client.put("/api/v1/alerts/settings", headers=auth_headers, json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["alert_threshold_days"] == 14


def test_filter_alerts_by_status(client, auth_headers, db_session, test_product):
    """Test filtering alerts by status."""
    from app.services.alert_service import AlertService
    
    # Create and acknowledge an alert
    alert_service = AlertService(db_session)
    alerts = alert_service.check_low_stock_alerts()
    alert_service.acknowledge_alert(alerts[0].id)
    
    # Filter by active status
    response = client.get("/api/v1/alerts?status=active", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0
    
    # Filter by acknowledged status
    response = client.get("/api/v1/alerts?status=acknowledged", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_alerts_by_type(client, auth_headers, db_session, test_product):
    """Test filtering alerts by type."""
    from app.services.alert_service import AlertService
    
    # Create a low stock alert
    alert_service = AlertService(db_session)
    alert_service.check_low_stock_alerts()
    
    # Filter by low_stock type
    response = client.get("/api/v1/alerts?alert_type=low_stock", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Filter by predicted_depletion type
    response = client.get("/api/v1/alerts?alert_type=predicted_depletion", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
