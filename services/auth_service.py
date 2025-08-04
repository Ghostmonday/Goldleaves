"""
Authentication service implementation.
Handles user registration, login, password reset, and email verification.
"""

from datetime import timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, create_verification_token,
    create_password_reset_token, verify_verification_token,
    verify_password_reset_token, validate_password_strength
)
from core.exceptions import (
    AuthenticationError, ValidationError, NotFoundError
)
from models.user import User
from schemas.auth import UserRegister, UserLogin, Token
from app.config import settings


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, user_data: UserRegister) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Dictionary with registration result
            
        Raises:
            ValidationError: If user data is invalid
        """
        # Validate password strength
        password_errors = validate_password_strength(user_data.password)
        if password_errors:
            raise ValidationError(f"Password validation failed: {', '.join(password_errors)}")
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            (User.email == user_data.email) | 
            (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise ValidationError("Email address is already registered")
            else:
                raise ValidationError("Username is already taken")
        
        # Create new user
        try:
            user = User(
                email=user_data.email,
                username=user_data.username or user_data.email.split('@')[0],
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                hashed_password=get_password_hash(user_data.password),
                is_active=False,  # Requires email verification
                is_verified=False
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Generate verification token
            verification_token = create_verification_token(user.email)
            
            # In a real application, you would send the verification email here
            # For now, we'll just return the token for testing
            
            return {
                "user_id": user.id,
                "email": user.email,
                "verification_token": verification_token,
                "message": "User registered successfully. Email verification required."
            }
            
        except IntegrityError:
            self.db.rollback()
            raise ValidationError("User registration failed due to data constraints")
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """
        Authenticate user and return tokens.
        
        Args:
            login_data: User login credentials
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email or username
        user = self.db.query(User).filter(
            (User.email == login_data.username_or_email) |
            (User.username == login_data.username_or_email)
        ).first()
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is not active. Please verify your email.")
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "username": user.username},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "type": "refresh"}
        )
        
        # Update last login
        user.last_login = user.updated_at
        self.db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token response
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "username": user.username},
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "type": "refresh"}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify user email using verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            Verification result
            
        Raises:
            ValidationError: If token is invalid
        """
        email = verify_verification_token(token)
        if not email:
            raise ValidationError("Invalid or expired verification token")
        
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundError("User not found")
        
        if user.is_verified:
            return {"message": "Email already verified"}
        
        # Activate and verify user
        user.is_active = True
        user.is_verified = True
        user.email_verified_at = user.updated_at
        self.db.commit()
        
        return {"message": "Email verified successfully"}
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset for user.
        
        Args:
            email: User email address
            
        Returns:
            Reset request result
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists for security
            return {"message": "If the email exists, a reset link will be sent"}
        
        # Generate reset token
        reset_token = create_password_reset_token(email)
        
        # In a real application, you would send the reset email here
        # For now, we'll just return the token for testing
        
        return {
            "message": "Password reset link sent to email",
            "reset_token": reset_token  # Remove in production
        }
    
    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Reset result
            
        Raises:
            ValidationError: If token is invalid or password is weak
        """
        # Validate new password
        password_errors = validate_password_strength(new_password)
        if password_errors:
            raise ValidationError(f"Password validation failed: {', '.join(password_errors)}")
        
        # Verify reset token
        email = verify_password_reset_token(token)
        if not email:
            raise ValidationError("Invalid or expired reset token")
        
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return {"message": "Password reset successfully"}
    
    async def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Get user by access token.
        
        Args:
            token: JWT access token
            
        Returns:
            User object if token is valid, None otherwise
        """
        payload = verify_token(token, "access")
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
