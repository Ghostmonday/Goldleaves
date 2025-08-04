# === AGENT CONTEXT: ROUTERS AGENT ===
# 🚧 TODOs for Phase 4 — Complete endpoint contracts
# - [ ] Define FastAPI routes with dependency injection
# - [ ] Enforce usage of Pydantic schemas from schemas/
# - [ ] Route all business logic to services/ layer
# - [ ] Attach rate limit, audit, and org context middleware
# - [ ] Export routers via `RouterContract` in contract.py
# - [ ] Add tag, prefix, and response model to all endpoints
# - [ ] Ensure endpoint coverage with integration tests
# - [ ] Maintain full folder isolation (no model/service import)
# - [ ] Use consistent 2xx/4xx status codes and error schemas

"""
Security utilities for authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .constants import ErrorMessages

# Set up logging
logger = logging.getLogger(__name__)

# OAuth2 scheme for token handling - endpoint used to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Mock configuration (in a real app, these would be in environment variables)
SECRET_KEY = "your_secret_key_here"  # In production, use a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided payload data.
    
    Args:
        data: The payload to encode in the token.
        expires_delta: Optional custom expiration time.
        
    Returns:
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
            
        # In a real application, you would validate the user exists in your database
        # For this example, we'll just return the payload
        return payload
        
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise credentials_exception
