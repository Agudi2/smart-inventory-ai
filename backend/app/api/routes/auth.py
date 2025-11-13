"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse
)
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException, ValidationException
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.register(user_data)
        return UserResponse.from_orm(user)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and receive access and refresh tokens"
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and generate JWT tokens.
    
    Args:
        credentials: User login credentials
        db: Database session
        
    Returns:
        TokenResponse: Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_service = AuthService(db)
        tokens = auth_service.login(credentials)
        return tokens
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate new access token using refresh token"
)
def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        token_data: Refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        auth_service = AuthService(db)
        tokens = auth_service.refresh_token(token_data.refresh_token)
        return tokens
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
def get_me(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse.from_orm(current_user)
