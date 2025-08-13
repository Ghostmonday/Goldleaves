"""
Base schemas for API responses and common models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseSchema):
    """Standard success response schema."""

    success: bool = Field(True, description="Indicates successful operation")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")


class ErrorResponse(BaseSchema):
    """Standard error response schema."""

    success: bool = Field(False, description="Indicates failed operation")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")


class PaginationSchema(BaseSchema):
    """Pagination metadata schema."""

    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseSchema):
    """Paginated response schema."""

    items: List[Any] = Field(..., description="List of items")
    pagination: PaginationSchema = Field(..., description="Pagination metadata")


class HealthCheck(BaseSchema):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
