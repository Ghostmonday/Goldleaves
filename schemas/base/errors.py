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
Error schemas and exception handling for consistent error responses.
Provides standardized error formats and validation error patterns.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ErrorCode(str, Enum):
    """Standard error codes."""
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Authorization errors
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCESS_DENIED = "ACCESS_DENIED"
    
    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # System errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FieldError(BaseModel):
    """Individual field validation error."""
    
    field: str = Field(
        description="Name of the field with error",
        example="email"
    )
    
    code: str = Field(
        description="Error code for this field",
        example="INVALID_FORMAT"
    )
    
    message: str = Field(
        description="Human-readable error message",
        example="Invalid email format"
    )
    
    value: Optional[Any] = Field(
        default=None,
        description="The invalid value that caused the error"
    )
    
    constraint: Optional[str] = Field(
        default=None,
        description="The validation constraint that was violated",
        example="email_format"
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    code: ErrorCode = Field(
        description="Specific error code"
    )
    
    message: str = Field(
        description="Human-readable error message"
    )
    
    severity: ErrorSeverity = Field(
        default=ErrorSeverity.MEDIUM,
        description="Error severity level"
    )
    
    source: Optional[str] = Field(
        default=None,
        description="Source component that generated the error",
        example="user_service"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )


class ValidationError(BaseModel):
    """Validation error with field-specific details."""
    
    code: ErrorCode = Field(
        default=ErrorCode.VALIDATION_ERROR,
        
    )
    
    message: str = Field(
        default="Validation failed",
        description="General validation error message"
    )
    
    field_errors: List[FieldError] = Field(
        description="List of field-specific errors"
    )
    
    total_errors: int = Field(
        description="Total number of validation errors",
        example=2
    )
    
    @validator('total_errors', always=True)
    def calculate_total_errors(cls, v, values):
        """Calculate total errors from field_errors."""
        field_errors = values.get('field_errors', [])
        return len(field_errors)


class BusinessError(BaseModel):
    """Business logic error."""
    
    code: ErrorCode = Field(
        description="Business error code"
    )
    
    message: str = Field(
        description="Business error message"
    )
    
    rule: str = Field(
        description="Business rule that was violated",
        example="max_organizations_per_user"
    )
    
    current_value: Optional[Any] = Field(
        default=None,
        description="Current value that caused the violation"
    )
    
    allowed_value: Optional[Any] = Field(
        default=None,
        description="Maximum allowed value"
    )


class SystemError(BaseModel):
    """System/infrastructure error."""
    
    code: ErrorCode = Field(
        description="System error code"
    )
    
    message: str = Field(
        description="System error message"
    )
    
    component: Optional[str] = Field(
        default=None,
        description="System component that failed",
        example="database"
    )
    
    operation: Optional[str] = Field(
        default=None,
        description="Operation that was being performed",
        example="user_creation"
    )
    
    error_id: Optional[str] = Field(
        default=None,
        description="Internal error ID for debugging"
    )


class RateLimitError(BaseModel):
    """Rate limiting error."""
    
    code: ErrorCode = Field(
        default=ErrorCode.RATE_LIMIT_EXCEEDED,
        
    )
    
    message: str = Field(
        default="Rate limit exceeded",
        description="Rate limit error message"
    )
    
    limit: int = Field(
        description="Rate limit threshold",
        example=100
    )
    
    window_seconds: int = Field(
        description="Rate limit window in seconds",
        example=3600
    )
    
    retry_after_seconds: int = Field(
        description="Seconds to wait before retrying",
        example=1800
    )
    
    requests_made: int = Field(
        description="Number of requests made in current window",
        example=101
    )


class ErrorResponse(BaseModel):
    """Comprehensive error response."""
    
    success: bool = Field(
        default=False,
        
        description="Always false for error responses"
    )
    
    error: ErrorDetail = Field(
        description="Primary error information"
    )
    
    validation_errors: Optional[List[FieldError]] = Field(
        default=None,
        description="Validation errors (if applicable)"
    )
    
    business_errors: Optional[List[BusinessError]] = Field(
        default=None,
        description="Business rule violations (if applicable)"
    )
    
    system_errors: Optional[List[SystemError]] = Field(
        default=None,
        description="System errors (if applicable)"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracing"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error response timestamp"
    )
    
    help_url: Optional[str] = Field(
        default=None,
        description="URL to documentation for this error",
        example="https://docs.example.com/errors/validation"
    )


# === ERROR HELPER FUNCTIONS ===

def create_validation_error(
    field_errors: List[FieldError],
    message: str = "Validation failed"
) -> ValidationError:
    """Create a validation error response."""
    return ValidationError(
        message=message,
        field_errors=field_errors
    )

def create_field_error(
    field: str,
    code: str,
    message: str,
    value: Any = None,
    constraint: Optional[str] = None
) -> FieldError:
    """Create a field validation error."""
    return FieldError(
        field=field,
        code=code,
        message=message,
        value=value,
        constraint=constraint
    )

def create_business_error(
    code: ErrorCode,
    message: str,
    rule: str,
    current_value: Any = None,
    allowed_value: Any = None
) -> BusinessError:
    """Create a business logic error."""
    return BusinessError(
        code=code,
        message=message,
        rule=rule,
        current_value=current_value,
        allowed_value=allowed_value
    )

def create_system_error(
    code: ErrorCode,
    message: str,
    component: Optional[str] = None,
    operation: Optional[str] = None,
    error_id: Optional[str] = None
) -> SystemError:
    """Create a system error."""
    return SystemError(
        code=code,
        message=message,
        component=component,
        operation=operation,
        error_id=error_id
    )

def create_rate_limit_error(
    limit: int,
    window_seconds: int,
    retry_after_seconds: int,
    requests_made: int
) -> RateLimitError:
    """Create a rate limit error."""
    return RateLimitError(
        limit=limit,
        window_seconds=window_seconds,
        retry_after_seconds=retry_after_seconds,
        requests_made=requests_made
    )
