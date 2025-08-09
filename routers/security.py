# === AGENT CONTEXT: ROUTERS AGENT ===
# Shim module: re-exports from core.security for router-specific security functions
# This maintains existing imports while consolidating security logic

"""
Security utilities for authentication and authorization.
"""
import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.security import verify_token

from .constants import ErrorMessages

# Set up logging
logger = logging.getLogger(__name__)

# OAuth2 scheme for token handling - endpoint used to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validates the JWT token and returns the current user.
    
    Args:
        token: The JWT token from the Authorization header.
        
    Returns:
        The user data from the token.
        
    Raises:
        HTTPException: If the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ErrorMessages.INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token, "access")
    if payload is None:
        logger.warning("Invalid or expired token")
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning("Token missing 'sub' claim")
        raise credentials_exception
        
    # In a real application, you would validate the user exists in your database
    # For this example, we'll just return the payload
    return payload

# Re-export common functions from core.security
from core.security import (
    create_access_token,
    create_refresh_token,
    generate_secure_token,
    get_password_hash,
    verify_password,
)

__all__ = [
    "get_current_user",
    "oauth2_scheme", 
    "create_access_token",
    "create_refresh_token",
    "verify_password",
    "get_password_hash",
    "generate_secure_token",
]
