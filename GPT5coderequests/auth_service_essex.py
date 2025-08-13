# apps/backend/services/auth_service.py
"""Minimal JWT helpers for tests."""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from core.config import settings


def create_access_token(data: Dict[str, Any], expires_minutes: int = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode
        expires_minutes: Token expiration in minutes (default from settings)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_minutes is None:
        expires_minutes = settings.jwt_expiration_minutes
    
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Decoded token payload
    
    Raises:
        jwt.PyJWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.PyJWTError as e:
        raise e