"""
Security utilities for authentication and authorization.
Provides password hashing, JWT token management, and security helpers.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext


# Mock settings for now - in real app this would come from config
class MockSettings:
    ALGORITHM = "HS256"
    SECRET_KEY = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

settings = MockSettings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Custom expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    """Decode access token - alias for verify_token."""
    return verify_token(token, "access")


def verify_access_token(token: str) -> Optional[dict]:
    """Verify access token - alias for verify_token."""
    return verify_token(token, "access")


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify refresh token."""
    return verify_token(token, "refresh")


def create_verification_token(email: str) -> str:
    """
    Create email verification token.
    
    Args:
        email: Email address to verify
        
    Returns:
        Verification token
    """
    data = {"email": email, "type": "email_verification"}
    expire = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    data.update({"exp": expire})
    
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_verification_token(token: str) -> Optional[str]:
    """
    Verify email verification token.
    
    Args:
        token: Verification token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "email_verification":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload.get("email")
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Create password reset token.
    
    Args:
        email: Email address for password reset
        
    Returns:
        Password reset token
    """
    data = {"email": email, "type": "password_reset"}
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    data.update({"exp": expire})
    
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token.
    
    Args:
        token: Password reset token
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "password_reset":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload.get("email")
    except JWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Secure random token (hex encoded)
    """
    return secrets.token_hex(length)


def encrypt_data(data: str) -> str:
    """Mock encryption function."""
    return data  # In real implementation, use proper encryption


def generate_api_key() -> str:
    """
    Generate API key.
    
    Returns:
        API key string
    """
    # Generate a secure random token and add a prefix
    token = generate_secure_token(20)
    return f"gl_{token}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify API key against its hash.
    
    Args:
        api_key: Plain API key
        hashed_key: Hashed API key
        
    Returns:
        True if key matches, False otherwise
    """
    return hash_api_key(api_key) == hashed_key


def require_permission(permission: str):
    """Mock permission requirement function."""
    def decorator(func):
        return func
    return decorator
