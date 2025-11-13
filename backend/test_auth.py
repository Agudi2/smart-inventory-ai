"""Simple test script to verify authentication implementation."""

import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, '.')

from app.main import app
from app.core.database import get_db
from app.models.base import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

def test_register():
    """Test user registration."""
    print("Testing user registration...")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "Test1234",
            "full_name": "Test User"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    print("✓ Registration test passed\n")

def test_login():
    """Test user login."""
    print("Testing user login...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    print("✓ Login test passed\n")
    return data["access_token"], data["refresh_token"]

def test_get_me(access_token):
    """Test getting current user."""
    print("Testing get current user...")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    print("✓ Get current user test passed\n")

def test_refresh_token(refresh_token):
    """Test token refresh."""
    print("Testing token refresh...")
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    print("✓ Token refresh test passed\n")

def test_invalid_login():
    """Test login with invalid credentials."""
    print("Testing invalid login...")
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123"
        }
    )
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 401
    print("✓ Invalid login test passed\n")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Authentication System Tests")
        print("=" * 60 + "\n")
        
        test_register()
        access_token, refresh_token = test_login()
        test_get_me(access_token)
        test_refresh_token(refresh_token)
        test_invalid_login()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
