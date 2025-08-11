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
Base schema module exports.
Provides foundational schemas for responses, pagination, and error handling.
"""

# Response schemas
# Error schemas
from .errors import (
    BusinessError,
    ErrorCode,
    ErrorDetail,
    ErrorSeverity,
    FieldError,
    RateLimitError,
    SystemError,
    ValidationError,
    create_business_error,
    create_field_error,
    create_rate_limit_error,
    create_system_error,
    create_validation_error,
)
from .errors import (
    ErrorResponse as DetailedErrorResponse,
)

# Pagination schemas
from .pagination import (
    CursorPaginatedResponse,
    CursorPaginationMeta,
    CursorPaginationParams,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    SearchParams,
    calculate_offset,
    create_pagination_links,
    validate_pagination_params,
)
from .responses import (
    BaseResponse,
    ConflictResponse,
    ErrorResponse,
    ForbiddenResponse,
    NotFoundResponse,
    RateLimitResponse,
    ServerErrorResponse,
    SuccessResponse,
    UnauthorizedResponse,
    ValidationErrorResponse,
    create_error_response,
    create_not_found_response,
    create_success_response,
    create_validation_error_response,
)

__all__ = [
    # Response schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "NotFoundResponse", 
    "UnauthorizedResponse",
    "ForbiddenResponse",
    "ConflictResponse",
    "RateLimitResponse",
    "ServerErrorResponse",
    "create_success_response",
    "create_error_response",
    "create_validation_error_response",
    "create_not_found_response",
    
    # Pagination schemas
    "PaginationParams",
    "SearchParams",
    "PaginationMeta",
    "PaginatedResponse",
    "CursorPaginationParams",
    "CursorPaginationMeta",
    "CursorPaginatedResponse",
    "calculate_offset",
    "validate_pagination_params",
    "create_pagination_links",
    
    # Error schemas
    "ErrorCode",
    "ErrorSeverity",
    "FieldError",
    "ErrorDetail",
    "ValidationError",
    "BusinessError",
    "SystemError",
    "RateLimitError",
    "DetailedErrorResponse",
    "create_validation_error",
    "create_field_error",
    "create_business_error",
    "create_system_error",
    "create_rate_limit_error",
]
