"""
Security utilities for authentication and authorization.
Provides password hashing, JWT token management, and security helpers.
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, Callable, List
import secrets
import hashlib
import re

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings


# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Simple function to test if file execution gets this far
def verify_access_token(token: str) -> Optional[dict]:
    """Temporary function for testing."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "access":
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except JWTError:
        return None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Security constants
BCRYPT_ROUNDS = 12
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class TokenValidationError(SecurityError):
    """Exception raised when token validation fails."""
    pass


class PasswordValidationError(SecurityError):
    """Exception raised when password validation fails."""
    pass


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


def verify_access_token(token: str) -> Optional[dict]:
    """
    Verify access token and return payload.
    
    Args:
        token: JWT access token
        
    Returns:
        Token payload if valid, None otherwise
    """
    return verify_token(token, "access")


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key for webhook authentication.
    
    Args:
        api_key: API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    # In production, this would check against a database
    # For now, check against settings or a hardcoded value
    valid_keys = getattr(settings, 'VALID_API_KEYS', [])
    return api_key in valid_keys


def require_permission(permission: str) -> Callable:
    """
    Decorator to require specific permission for endpoint access.
    
    Args:
        permission: Required permission string
        
    Returns:
        Decorator function
    """
    def decorator(func):
        func._required_permission = permission
        return func
    return decorator


def validate_password_strength(password: str) -> List[str]:
    """
    Validate password strength and return list of issues.
    
    Args:
        password: Password to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("Password must contain at least one special character")
    
    return errors


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded secure token
    """
    return secrets.token_hex(length)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


# Ensure verify_access_token is available at module level
def verify_access_token(token: str) -> Optional[dict]:
    """
    Verify access token and return payload.
    
    Args:
        token: JWT access token
        
    Returns:
        Token payload if valid, None otherwise
    """
    return verify_token(token, "access")
