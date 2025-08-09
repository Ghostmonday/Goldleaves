# === AGENT CONTEXT: SCHEMAS AGENT ===
# 🚧 TODOs for Phase 4 — Complete schema contracts
# - [x] Define all Pydantic schemas with type-safe fields
# - [x] Add pagination, response, and error wrapper patterns
# - [x] Validate alignment with models/ and services/ usage
# - [x] Enforce exports via `schemas/contract.py`
# - [x] Ensure each schema has at least one integration test
# - [x] Maintain strict folder isolation (no model/service imports)
# - [x] Add version string and export mapping to `SchemaContract`
# - [x] Annotate fields with metadata for future auto-docs

"""
Base response wrapper schemas for consistent API responses.
Provides standardized success/error response patterns.
"""

from typing import Optional, Generic, TypeVar, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# Generic type for response data
T = TypeVar('T')


class BaseResponse(GenericModel, Generic[T]):
    """Base response wrapper for all API responses."""
    
    success: bool = Field(
        description="Whether the request was successful",
        example=True
    )
    
    data: Optional[T] = Field(
        default=None,
        description="Response data payload"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Human-readable response message"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp in UTC"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracing"
    )


class SuccessResponse(BaseResponse[T]):
    """Success response wrapper."""
    
    success: bool = Field(
        default=True,
        
        description="Always true for success responses"
    )


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    
    success: bool = Field(
        default=False,
        
        description="Always false for error responses"
    )
    
    error: str = Field(
        description="Error code or type",
        example="VALIDATION_ERROR"
    )
    
    message: str = Field(
        description="Human-readable error message",
        example="The provided data is invalid"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details and context"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp in UTC"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracing"
    )


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors."""
    
    error: str = Field(
        default="VALIDATION_ERROR",
        
    )
    
    field_errors: Dict[str, List[str]] = Field(
        description="Field-specific validation errors",
        example={
            "email": ["Invalid email format"],
            "password": ["Password too weak"]
        }
    )


class NotFoundResponse(ErrorResponse):
    """Resource not found error response."""
    
    error: str = Field(
        default="NOT_FOUND",
        
    )
    
    resource_type: str = Field(
        description="Type of resource that was not found",
        example="user"
    )
    
    resource_id: str = Field(
        description="ID of the resource that was not found",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


class UnauthorizedResponse(ErrorResponse):
    """Unauthorized access error response."""
    
    error: str = Field(
        default="UNAUTHORIZED",
        
    )
    
    required_permission: Optional[str] = Field(
        default=None,
        description="Required permission for this action"
    )


class ForbiddenResponse(ErrorResponse):
    """Forbidden access error response."""
    
    error: str = Field(
        default="FORBIDDEN",
        
    )
    
    reason: Optional[str] = Field(
        default=None,
        description="Reason for forbidden access"
    )


class ConflictResponse(ErrorResponse):
    """Resource conflict error response."""
    
    error: str = Field(
        default="CONFLICT",
        
    )
    
    conflicting_field: Optional[str] = Field(
        default=None,
        description="Field that caused the conflict"
    )
    
    conflicting_value: Optional[str] = Field(
        default=None,
        description="Value that caused the conflict"
    )


class RateLimitResponse(ErrorResponse):
    """Rate limit exceeded error response."""
    
    error: str = Field(
        default="RATE_LIMIT_EXCEEDED",
        
    )
    
    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retrying"
    )
    
    limit: Optional[int] = Field(
        default=None,
        description="Rate limit threshold"
    )
    
    window: Optional[int] = Field(
        default=None,
        description="Rate limit window in seconds"
    )


class ServerErrorResponse(ErrorResponse):
    """Internal server error response."""
    
    error: str = Field(
        default="INTERNAL_SERVER_ERROR",
        
    )
    
    error_id: Optional[str] = Field(
        default=None,
        description="Internal error identifier for debugging"
    )


# === RESPONSE HELPER FUNCTIONS ===

def create_success_response(
    data: T,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> SuccessResponse[T]:
    """Create a success response."""
    return SuccessResponse(
        data=data,
        message=message,
        request_id=request_id
    )

def create_error_response(
    error: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        error=error,
        message=message,
        details=details,
        request_id=request_id
    )

def create_validation_error_response(
    field_errors: Dict[str, List[str]],
    message: str = "Validation failed",
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Create a validation error response."""
    return ValidationErrorResponse(
        message=message,
        field_errors=field_errors,
        request_id=request_id
    )

def create_not_found_response(
    resource_type: str,
    resource_id: str,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> NotFoundResponse:
    """Create a not found error response."""
    if message is None:
        message = f"{resource_type.title()} with ID '{resource_id}' not found"
    
    return NotFoundResponse(
        message=message,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id
    )
