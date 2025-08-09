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
Pagination schemas for consistent paginated API responses.
Provides standardized pagination patterns and metadata.
"""

from math import ceil
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

# Generic type for paginated data
T = TypeVar('T')


class PaginationParams(BaseModel):
    """Request parameters for pagination."""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)",
        example=1
    )
    
    size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (1-100)",
        example=20
    )
    
    sort_by: Optional[str] = Field(
        default=None,
        description="Field name to sort by",
        example="created_at"
    )
    
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'",
        example="desc"
    )
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort field name format."""
        if v is None:
            return v
        
        # Allow alphanumeric, underscore, and dot (for nested fields)
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', v):
            raise ValueError("Invalid sort field name")
        
        return v


class SearchParams(PaginationParams):
    """Extended pagination with search functionality."""
    
    search: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Search query string",
        example="john doe"
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional filter parameters"
    )


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    current_page: int = Field(
        description="Current page number",
        example=1
    )
    
    page_size: int = Field(
        description="Number of items per page",
        example=20
    )
    
    total_items: int = Field(
        ge=0,
        description="Total number of items",
        example=150
    )
    
    total_pages: int = Field(
        ge=0,
        description="Total number of pages",
        example=8
    )
    
    has_previous: bool = Field(
        description="Whether there is a previous page",
        example=False
    )
    
    has_next: bool = Field(
        description="Whether there is a next page",
        example=True
    )
    
    previous_page: Optional[int] = Field(
        default=None,
        description="Previous page number (if exists)",
        example=None
    )
    
    next_page: Optional[int] = Field(
        default=None,
        description="Next page number (if exists)",
        example=2
    )
    
    @classmethod
    def create(
        cls,
        current_page: int,
        page_size: int,
        total_items: int
    ) -> 'PaginationMeta':
        """Create pagination metadata from basic parameters."""
        total_pages = ceil(total_items / page_size) if total_items > 0 else 0
        
        has_previous = current_page > 1
        has_next = current_page < total_pages
        
        previous_page = current_page - 1 if has_previous else None
        next_page = current_page + 1 if has_next else None
        
        return cls(
            current_page=current_page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_previous=has_previous,
            has_next=has_next,
            previous_page=previous_page,
            next_page=next_page
        )


class PaginatedResponse(GenericModel, Generic[T]):
    """Paginated response wrapper."""
    
    items: List[T] = Field(
        description="List of items for current page"
    )
    
    pagination: PaginationMeta = Field(
        description="Pagination metadata"
    )
    
    @classmethod
    def create(
        cls,
        items: List[T],
        current_page: int,
        page_size: int,
        total_items: int
    ) -> 'PaginatedResponse[T]':
        """Create a paginated response."""
        pagination = PaginationMeta.create(
            current_page=current_page,
            page_size=page_size,
            total_items=total_items
        )
        
        return cls(
            items=items,
            pagination=pagination
        )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""
    
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of items to return",
        example=20
    )
    
    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for next page",
        example="eyJpZCI6MTIzLCJjcmVhdGVkX2F0IjoiMjAyMy0xMS0xNVQxMDowMDowMFoifQ=="
    )
    
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'",
        example="desc"
    )


class CursorPaginationMeta(BaseModel):
    """Cursor pagination metadata."""
    
    has_next: bool = Field(
        description="Whether there are more items",
        example=True
    )
    
    next_cursor: Optional[str] = Field(
        default=None,
        description="Cursor for next page (if has_next is true)"
    )
    
    count: int = Field(
        ge=0,
        description="Number of items in current response",
        example=20
    )


class CursorPaginatedResponse(GenericModel, Generic[T]):
    """Cursor-based paginated response wrapper."""
    
    items: List[T] = Field(
        description="List of items"
    )
    
    pagination: CursorPaginationMeta = Field(
        description="Cursor pagination metadata"
    )


# === PAGINATION HELPER FUNCTIONS ===

def calculate_offset(page: int, page_size: int) -> int:
    """Calculate database offset from page parameters."""
    return (page - 1) * page_size

def validate_pagination_params(page: int, size: int) -> None:
    """Validate pagination parameters."""
    if page < 1:
        raise ValueError("Page must be greater than 0")
    if size < 1 or size > 100:
        raise ValueError("Page size must be between 1 and 100")

def create_pagination_links(
    base_url: str,
    current_page: int,
    total_pages: int,
    page_size: int,
    **query_params
) -> Dict[str, Optional[str]]:
    """Create pagination navigation links."""
    def build_url(page: int) -> str:
        params = {**query_params, 'page': page, 'size': page_size}
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"
    
    links = {
        'self': build_url(current_page),
        'first': build_url(1) if total_pages > 0 else None,
        'last': build_url(total_pages) if total_pages > 0 else None,
        'prev': build_url(current_page - 1) if current_page > 1 else None,
        'next': build_url(current_page + 1) if current_page < total_pages else None
    }
    
    return links


from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field("asc", pattern="^(asc|desc)$")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
