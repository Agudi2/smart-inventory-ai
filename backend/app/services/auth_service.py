"""Authentication service for user registration, login, and token management."""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID

from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.exceptions import UnauthorizedException, ValidationException


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize authentication service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def register(self, user_data: UserRegister) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            User: Created user object
            
        Raises:
            ValidationException: If email already exists
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValidationException(f"User with email {user_data.email} already exists")
        
        # Create new user with hashed password
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role="user",  # Default role
            is_active=True
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user
    
    def login(self, credentials: UserLogin) -> TokenResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            credentials: User login credentials
            
        Returns:
            TokenResponse: Access and refresh tokens
            
        Raises:
            UnauthorizedException: If credentials are invalid
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == credentials.email).first()
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            TokenResponse: New access and refresh tokens
            
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        verify_token_type(payload, "refresh")
        
        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid token payload")
        
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise UnauthorizedException("Invalid user ID in token")
        
        # Verify user still exists and is active
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedException("User not found")
        
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        # Generate new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    
    def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token: JWT access token
            
        Returns:
            User: Current authenticated user
            
        Raises:
            UnauthorizedException: If token is invalid or user not found
        """
        # Decode and validate access token
        payload = decode_token(token)
        verify_token_type(payload, "access")
        
        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Invalid token payload")
        
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise UnauthorizedException("Invalid user ID in token")
        
        # Get user from database
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedException("User not found")
        
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")
        
        return user
