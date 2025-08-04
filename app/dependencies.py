"""Shared dependencies for the application."""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from core.database import get_db
from app.config import settings
from models.user import User
from notifications import email_service, webhook_service, notification_service


security = HTTPBearer()


def get_email_service():
    """Get email service instance."""
    return email_service


def get_webhook_service():
    """Get webhook service instance."""
    return webhook_service


def get_notification_service():
    """Get notification service instance."""
    return notification_service


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return {
        "id": str(user.id),
        "email": user.email,
        "role": getattr(user, "role", "user")
    }


def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> dict:
    """Require admin user."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None
    
    return {
        "id": str(user.id),
        "email": user.email,
        "role": getattr(user, "role", "user")
    }
