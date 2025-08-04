"""
Authentication service with JWT token creation and management.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Tuple
from passlib.context import CryptContext

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(user_id: int) -> str:
    """
    Create a new JWT access token for the given user ID.
    
    Args:
        user_id: The user's database ID
        
    Returns:
        JWT access token string
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: int) -> Tuple[str, datetime]:
    """
    Create a new JWT refresh token for the given user ID.
    
    Args:
        user_id: The user's database ID
        
    Returns:
        Tuple of (refresh_token, expires_at_datetime)
    """
    # Refresh tokens last 30 days
    expire = datetime.utcnow() + timedelta(days=30)
    
    # Create a secure random token ID for revocation purposes
    token_id = secrets.token_urlsafe(32)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": token_id  # JWT ID for token revocation
    }
    
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token, expire

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The bcrypt hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.
    
    Args:
        password: The plain text password
        
    Returns:
        Bcrypt hashed password string
    """
    return pwd_context.hash(password)

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(
        token, 
        settings.jwt_secret.get_secret_value(), 
        algorithms=[settings.jwt_algorithm]
    )

def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(32)

def create_password_reset_token(user_id: int) -> str:
    """
    Create a JWT token for password reset.
    
    Args:
        user_id: The user's database ID
        
    Returns:
        JWT password reset token
    """
    expire = datetime.utcnow() + timedelta(hours=settings.reset_token_expire_hours)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "password_reset"
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
