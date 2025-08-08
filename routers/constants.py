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
Centralized constants for the application.
This module contains error messages and other constants used throughout the application.
"""

class ErrorMessages:
    """
    Centralized error messages to ensure consistency across the application.
    """
    # Authentication errors
    INVALID_CREDENTIALS = "Invalid email or password"
    REGISTRATION_FAILED = "User registration failed"
    EMAIL_ALREADY_EXISTS = "A user with this email already exists"
    USERNAME_ALREADY_EXISTS = "A user with this username already exists"
    
    # Authorization errors
    TOKEN_EXPIRED = "Token has expired"
    INVALID_TOKEN = "Could not validate credentials"
    INVALID_TOKEN_PAYLOAD = "Invalid token payload"
    NOT_AUTHENTICATED = "Not authenticated"
    INSUFFICIENT_PERMISSIONS = "You don't have permission to perform this action"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "Too many requests. Please try again later"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "Resource not found"
    RESOURCE_ALREADY_EXISTS = "Resource already exists"
