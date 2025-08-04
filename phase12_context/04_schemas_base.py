# Base schema module exports.
# Provides foundational schemas for responses, pagination, and error handling.

from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List, Dict, Any
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class BaseResponse(BaseModel):
    """Base response schema."""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

class SuccessResponse(BaseResponse, Generic[T]):
    """Success response with data."""
    data: T
    success: bool = True

class ErrorResponse(BaseResponse):
    """Error response schema."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    per_page: int = 20
    
class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with metadata."""
    data: List[T]
    meta: PaginationMeta
    success: bool = True
