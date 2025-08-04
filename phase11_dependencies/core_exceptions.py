"""
Custom exceptions for the application.
Provides specific exception types for better error handling.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class GoldleavesException(Exception):
    """Base exception class for Goldleaves application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(GoldleavesException):
    """Exception raised when a requested resource is not found."""
    pass


class ValidationError(GoldleavesException):
    """Exception raised when input validation fails."""
    pass


class PermissionError(GoldleavesException):
    """Exception raised when user lacks required permissions."""
    pass


class NotificationError(GoldleavesException):
    """Exception raised for notification-related errors."""
    pass


class AuthenticationError(GoldleavesException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(GoldleavesException):
    """Raised when authorization fails."""
    pass


class DatabaseError(GoldleavesException):
    """Raised when database operations fail."""
    pass


class EmailError(GoldleavesException):
    """Raised when email operations fail."""
    pass


def credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def not_found_exception(entity: str = "Item"):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} not found"
    )


def permission_denied_exception():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


def inactive_user_exception():
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Inactive user"
    )
