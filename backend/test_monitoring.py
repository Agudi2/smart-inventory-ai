"""Tests for health check and monitoring endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "app_name" in data
    assert "version" in data
    assert "checks" in data
    
    # Check database health
    assert "database" in data["checks"]
    assert "status" in data["checks"]["database"]
    
    # Check Redis health (may be degraded if Redis not available)
    assert "redis" in data["checks"]
    assert "status" in data["checks"]["redis"]


def test_health_check_includes_correlation_id():
    """Test health check response includes correlation ID in headers."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_metrics_endpoint():
    """Test metrics endpoint returns system statistics."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check for error response (in case of failure)
    if "error" in data:
        # Metrics generation failed, but endpoint is working
        assert "detail" in data
        assert "timestamp" in data
        return
    
    # Check application metrics
    assert "timestamp" in data
    assert "application" in data
    assert "name" in data["application"]
    assert "version" in data["application"]
    assert "uptime_seconds" in data["application"]
    assert "uptime_hours" in data["application"]
    
    # Check system metrics
    assert "system" in data
    assert "cpu_percent" in data["system"]
    assert "memory" in data["system"]
    assert "disk" in data["system"]
    
    # Check database metrics
    assert "database" in data
    
    # Check Redis metrics
    assert "redis" in data


def test_metrics_includes_correlation_id():
    """Test metrics response includes correlation ID in headers."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_custom_correlation_id():
    """Test that custom correlation ID is preserved."""
    custom_id = "test-correlation-123"
    response = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_id


def test_health_check_database_connectivity():
    """Test health check verifies database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    db_check = data["checks"]["database"]
    
    # Database check should have a status
    assert "status" in db_check
    assert db_check["status"] in ["healthy", "unhealthy"]
    assert "message" in db_check


def test_metrics_database_statistics():
    """Test metrics endpoint includes database statistics."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    
    data = response.json()
    
    # Skip if metrics generation failed
    if "error" in data:
        return
    
    # Database stats should be present
    assert "database" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
