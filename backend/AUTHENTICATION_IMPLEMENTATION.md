# Authentication System Implementation

## Overview

The authentication system has been successfully implemented for the Smart Inventory Management System. It provides secure user registration, login, token management, and protected route access using JWT (JSON Web Tokens) and bcrypt password hashing.

## Components Implemented

### 1. Security Utilities (`app/core/security.py`)

Core security functions for password hashing and JWT token management:

- **Password Hashing**:
  - `hash_password(password)` - Hash passwords using bcrypt
  - `verify_password(plain_password, hashed_password)` - Verify password against hash

- **JWT Token Management**:
  - `create_access_token(data, expires_delta)` - Create short-lived access tokens (15 min default)
  - `create_refresh_token(data)` - Create long-lived refresh tokens (7 days default)
  - `decode_token(token)` - Decode and validate JWT tokens
  - `verify_token_type(payload, expected_type)` - Verify token type (access/refresh)

### 2. Authentication Schemas (`app/schemas/auth.py`)

Pydantic models for request/response validation:

- `UserRegister` - User registration with email, password, and optional full name
  - Password validation: minimum 8 characters, must contain letters and digits
- `UserLogin` - Login credentials (email and password)
- `TokenResponse` - JWT token response with access_token, refresh_token, and token_type
- `TokenRefresh` - Refresh token request
- `UserResponse` - User information response (excludes password)
- `UserUpdate` - User profile update schema

### 3. Authentication Service (`app/services/auth_service.py`)

Business logic for authentication operations:

- `register(user_data)` - Register new user with hashed password
- `login(credentials)` - Authenticate user and generate tokens
- `refresh_token(refresh_token)` - Generate new tokens using refresh token
- `get_current_user(token)` - Get user from access token

### 4. Authentication Dependencies (`app/core/dependencies.py`)

FastAPI dependencies for protecting routes:

- `get_current_user()` - Extract and validate user from JWT token
- `get_current_active_user()` - Ensure user is active
- `require_role(role)` - Require specific role (admin, manager, user)
- `require_admin()` - Require admin role

### 5. Authentication API Endpoints (`app/api/routes/auth.py`)

RESTful API endpoints:

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and receive tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user information (protected)

## API Usage Examples

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-11-13T10:30:00",
  "updated_at": "2024-11-13T10:30:00"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-11-13T10:30:00",
  "updated_at": "2024-11-13T10:30:00"
}
```

### 4. Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Protecting Routes

### Basic Protection (Requires Authentication)

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.email}"}
```

### Role-Based Protection

```python
from app.core.dependencies import require_role, require_admin

# Require specific role
@router.post("/manager-only")
def manager_route(current_user: User = Depends(require_role("manager"))):
    return {"message": "Manager access granted"}

# Require admin role
@router.delete("/admin-only")
def admin_route(current_user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}
```

## Security Features

### Password Security
- Bcrypt hashing with automatic salt generation
- Minimum password requirements (8+ characters, letters + digits)
- Passwords never stored in plain text

### JWT Token Security
- Short-lived access tokens (15 minutes)
- Long-lived refresh tokens (7 days)
- Token type verification (access vs refresh)
- Configurable secret key and algorithm
- Automatic expiration handling

### API Security
- HTTP Bearer token authentication
- Proper HTTP status codes (401 for unauthorized, 403 for forbidden)
- User account status checking (active/inactive)
- Role-based access control

## Configuration

All authentication settings are configurable via environment variables:

```env
# JWT Authentication
JWT_SECRET_KEY="your-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Error Handling

The system provides clear error messages for common scenarios:

- **Invalid credentials**: 401 Unauthorized
- **Expired token**: 401 Unauthorized
- **Inactive user**: 403 Forbidden
- **Insufficient permissions**: 403 Forbidden
- **Email already exists**: 400 Bad Request
- **Invalid password format**: 422 Validation Error

## Testing

A comprehensive test suite has been created to verify:

1. Password hashing and verification
2. JWT token creation and decoding
3. Schema validation
4. API route registration
5. Token type verification

Run tests with:
```bash
cd backend
python test_auth_simple.py
```

## Requirements Met

This implementation satisfies all requirements from the specification:

✅ **Requirement 7.1**: JWT-based authentication for all API endpoints  
✅ **Requirement 7.2**: JWT token generation on valid login  
✅ **Requirement 7.3**: Request processing with valid JWT token  
✅ **Requirement 7.4**: Authentication error (401) for invalid/expired tokens  
✅ **Requirement 7.5**: Logging of authentication attempts and API access  

## Next Steps

The authentication system is now ready for use. Future tasks can:

1. Use `Depends(get_current_active_user)` to protect endpoints
2. Use `Depends(require_admin)` for admin-only endpoints
3. Use `Depends(require_role("manager"))` for role-specific endpoints
4. Access current user information via the `current_user` parameter

## Files Created

- `backend/app/core/security.py` - Security utilities
- `backend/app/schemas/auth.py` - Authentication schemas
- `backend/app/services/auth_service.py` - Authentication service
- `backend/app/core/dependencies.py` - FastAPI dependencies
- `backend/app/api/routes/auth.py` - Authentication endpoints
- `backend/test_auth_simple.py` - Test suite
- `backend/AUTHENTICATION_IMPLEMENTATION.md` - This documentation

## Dependencies Added

- `email-validator==2.1.0` - Email validation for Pydantic schemas
