"""Simple test to verify authentication implementation compiles correctly."""

import sys
sys.path.insert(0, '.')

print("Testing imports...")

# Test core security utilities
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
print("✓ Security utilities imported successfully")

# Test schemas
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse
)
print("✓ Auth schemas imported successfully")

# Test service
from app.services.auth_service import AuthService
print("✓ Auth service imported successfully")

# Test dependencies
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin
)
print("✓ Auth dependencies imported successfully")

# Test routes
from app.api.routes import auth
print("✓ Auth routes imported successfully")

# Test main app
from app.main import app
print("✓ Main app imported successfully")

# Test password hashing
print("\nTesting password hashing...")
password = "Test1234"
hashed = hash_password(password)
print(f"  Original: {password}")
print(f"  Hashed: {hashed[:50]}...")
assert verify_password(password, hashed), "Password verification failed"
assert not verify_password("WrongPassword", hashed), "Wrong password should not verify"
print("✓ Password hashing works correctly")

# Test JWT token creation
print("\nTesting JWT token creation...")
token_data = {"sub": "test-user-id", "email": "test@example.com", "role": "user"}
access_token = create_access_token(token_data)
refresh_token = create_refresh_token({"sub": "test-user-id"})
print(f"  Access token: {access_token[:50]}...")
print(f"  Refresh token: {refresh_token[:50]}...")
print("✓ JWT tokens created successfully")

# Test token decoding
print("\nTesting JWT token decoding...")
decoded = decode_token(access_token)
print(f"  Decoded payload: {decoded}")
assert decoded["sub"] == "test-user-id"
assert decoded["email"] == "test@example.com"
assert decoded["type"] == "access"
print("✓ JWT token decoding works correctly")

# Test API routes are registered
print("\nTesting API routes registration...")
routes = [route.path for route in app.routes]
print(f"  Registered routes: {len(routes)}")
assert "/api/v1/auth/register" in routes, "Register route not found"
assert "/api/v1/auth/login" in routes, "Login route not found"
assert "/api/v1/auth/refresh" in routes, "Refresh route not found"
assert "/api/v1/auth/me" in routes, "Me route not found"
print("✓ All auth routes registered correctly")

# Test schema validation
print("\nTesting schema validation...")
try:
    # Valid user registration
    user_reg = UserRegister(
        email="test@example.com",
        password="Test1234",
        full_name="Test User"
    )
    print(f"  Valid registration: {user_reg.email}")
    print("✓ Valid schema accepted")
except Exception as e:
    print(f"✗ Valid schema rejected: {e}")
    sys.exit(1)

try:
    # Invalid password (no digit)
    user_reg = UserRegister(
        email="test@example.com",
        password="TestPassword",
        full_name="Test User"
    )
    print("✗ Invalid password accepted (should have been rejected)")
    sys.exit(1)
except ValueError as e:
    print(f"  Invalid password rejected: {e}")
    print("✓ Password validation works")

print("\n" + "=" * 60)
print("All authentication implementation tests passed! ✓")
print("=" * 60)
print("\nAuthentication system is ready to use:")
print("  - POST /api/v1/auth/register - Register new user")
print("  - POST /api/v1/auth/login - Login and get tokens")
print("  - POST /api/v1/auth/refresh - Refresh access token")
print("  - GET /api/v1/auth/me - Get current user info")
