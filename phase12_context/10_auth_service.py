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
    create_refresh_token
)
from models.user import User


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user."""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            User.email == user_data["email"]
        ).first()
        
        if existing_user:
            raise ValueError("Email address is already registered")
        
        # Create new user
        try:
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                is_active=False,  # Requires email verification
                is_verified=False
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return {
                "user_id": user.id,
                "email": user.email,
                "message": "User registered successfully. Email verification required."
            }
            
        except IntegrityError:
            self.db.rollback()
            raise ValueError("User registration failed")
    
    async def login_user(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        email = login_data.get("email")
        password = login_data.get("password")
        
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # Update login timestamp
        user.update_login_timestamp()
        self.db.commit()
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "is_admin": user.is_admin,
                "is_verified": user.is_verified
            }
        }
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify user email with token."""
        # Mock implementation for context
        return {"message": "Email verified successfully"}
    
    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email."""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token (mock implementation)
        return {"message": "Password reset email sent"}
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password."""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Invalid current password")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return {"message": "Password changed successfully"}
