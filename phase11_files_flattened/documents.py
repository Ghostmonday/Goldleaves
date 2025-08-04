# schemas/frontend/documents.py
"""
Frontend-optimized document response schemas.
Provides clean, UI-ready data structures for document listings and details.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration."""
    FORM = "form"
    TEMPLATE = "template"
    CONTRACT = "contract"
    LETTER = "letter"
    REPORT = "report"
    MEMO = "memo"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SIGNED = "signed"
    ARCHIVED = "archived"


class DocumentPermissions(BaseModel):
    """Document-specific permissions for current user."""
    model_config = ConfigDict(from_attributes=True)
    
    can_view: bool = Field(default=True)
    can_edit: bool = Field(default=False)
    can_delete: bool = Field(default=False)
    can_share: bool = Field(default=False)
    can_download: bool = Field(default=True)
    can_comment: bool = Field(default=True)
    can_sign: bool = Field(default=False)


class DocumentAuthor(BaseModel):
    """Simplified author information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Author user ID")
    name: str = Field(description="Author display name")
    email: str = Field(description="Author email")
    avatar_url: Optional[str] = Field(default=None, description="Author avatar URL")


class DocumentTag(BaseModel):
    """Document tag/label."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Tag ID")
    name: str = Field(description="Tag name")
    color: str = Field(default="#6B7280", description="Tag color hex code")


class DocumentVersion(BaseModel):
    """Document version information."""
    model_config = ConfigDict(from_attributes=True)
    
    version_number: int = Field(description="Version number")
    created_at: datetime = Field(description="Version creation timestamp")
    created_by: DocumentAuthor = Field(description="Version creator")
    change_summary: Optional[str] = Field(default=None, description="Summary of changes")
    size_bytes: int = Field(description="Version size in bytes")


class DocumentListItem(BaseModel):
    """Simplified document item for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Document ID")
    title: str = Field(description="Document title")
    type: DocumentType = Field(description="Document type")
    status: DocumentStatus = Field(description="Document status")
    
    # Key metadata
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    created_by: DocumentAuthor = Field(description="Document creator")
    
    # Quick stats
    size_bytes: int = Field(description="Document size in bytes")
    page_count: Optional[int] = Field(default=None, description="Number of pages")
    version_count: int = Field(default=1, description="Number of versions")
    
    # UI helpers
    thumbnail_url: Optional[str] = Field(default=None, description="Document thumbnail URL")
    preview_text: Optional[str] = Field(default=None, description="Preview text snippet")
    tags: List[DocumentTag] = Field(default_factory=list, description="Document tags")
    
    # Collaboration info
    shared_with_count: int = Field(default=0, description="Number of users with access")
    comment_count: int = Field(default=0, description="Number of comments")
    is_favorite: bool = Field(default=False, description="Favorited by current user")
    
    # Permissions
    permissions: DocumentPermissions = Field(description="Current user permissions")
    
    # Related entities
    case_id: Optional[str] = Field(default=None, description="Associated case ID")
    client_id: Optional[str] = Field(default=None, description="Associated client ID")


class DocumentFilter(BaseModel):
    """Document filter options."""
    model_config = ConfigDict(from_attributes=True)
    
    search: Optional[str] = Field(default=None, description="Search query")
    type: Optional[List[DocumentType]] = Field(default=None, description="Filter by types")
    status: Optional[List[DocumentStatus]] = Field(default=None, description="Filter by status")
    created_by: Optional[List[str]] = Field(default=None, description="Filter by creator IDs")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tag IDs")
    case_id: Optional[str] = Field(default=None, description="Filter by case")
    client_id: Optional[str] = Field(default=None, description="Filter by client")
    date_from: Optional[datetime] = Field(default=None, description="Filter by date range start")
    date_to: Optional[datetime] = Field(default=None, description="Filter by date range end")
    is_favorite: Optional[bool] = Field(default=None, description="Filter favorites only")
    shared_with_me: Optional[bool] = Field(default=None, description="Filter shared documents")


class DocumentSort(BaseModel):
    """Document sort options."""
    model_config = ConfigDict(from_attributes=True)
    
    field: Literal["title", "created_at", "updated_at", "size_bytes", "type", "status"] = Field(
        default="updated_at",
        description="Sort field"
    )
    order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Has next page")
    has_previous: bool = Field(description="Has previous page")


class DocumentListResponse(BaseModel):
    """Document list response with pagination and metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    documents: List[DocumentListItem] = Field(description="List of documents")
    pagination: PaginationMeta = Field(description="Pagination information")
    
    # Applied filters (for UI state)
    applied_filters: DocumentFilter = Field(description="Currently applied filters")
    applied_sort: DocumentSort = Field(description="Currently applied sort")
    
    # Quick stats
    total_size_bytes: int = Field(default=0, description="Total size of all documents")
    type_breakdown: Dict[DocumentType, int] = Field(
        default_factory=dict,
        description="Document count by type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "doc_abc123",
                        "title": "Employment Agreement - John Smith",
                        "type": "contract",
                        "status": "in_review",
                        "created_at": "2024-03-15T09:30:00Z",
                        "updated_at": "2024-03-19T16:45:00Z",
                        "created_by": {
                            "id": "usr_123",
                            "name": "Jane Doe",
                            "email": "jane.doe@example.com",
                            "avatar_url": "https://api.example.com/avatars/usr_123.jpg"
                        },
                        "size_bytes": 245760,
                        "page_count": 8,
                        "version_count": 3,
                        "thumbnail_url": "https://api.example.com/thumbnails/doc_abc123.jpg",
                        "preview_text": "This Employment Agreement is entered into as of...",
                        "tags": [
                            {"id": "tag_1", "name": "Employment", "color": "#10B981"},
                            {"id": "tag_2", "name": "Urgent", "color": "#EF4444"}
                        ],
                        "shared_with_count": 3,
                        "comment_count": 5,
                        "is_favorite": True,
                        "permissions": {
                            "can_view": True,
                            "can_edit": True,
                            "can_delete": False,
                            "can_share": True,
                            "can_download": True,
                            "can_comment": True,
                            "can_sign": False
                        },
                        "case_id": "case_xyz789",
                        "client_id": "client_def456"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 142,
                    "total_pages": 8,
                    "has_next": True,
                    "has_previous": False
                },
                "applied_filters": {
                    "search": None,
                    "type": ["contract"],
                    "status": ["draft", "in_review"],
                    "is_favorite": None
                },
                "applied_sort": {
                    "field": "updated_at",
                    "order": "desc"
                },
                "total_size_bytes": 52428800,
                "type_breakdown": {
                    "contract": 45,
                    "form": 38,
                    "letter": 29,
                    "template": 20,
                    "report": 10
                }
            }
        }


class DocumentDetailResponse(DocumentListItem):
    """Detailed document response with full content."""
    model_config = ConfigDict(from_attributes=True)
    
    # Additional detail fields
    content_url: Optional[str] = Field(default=None, description="URL to fetch document content")
    download_url: Optional[str] = Field(default=None, description="Direct download URL")
    
    # Full version history
    versions: List[DocumentVersion] = Field(default_factory=list, description="Version history")
    
    # Sharing details
    shared_with: List[DocumentAuthor] = Field(default_factory=list, description="Users with access")
    public_link: Optional[str] = Field(default=None, description="Public sharing link")
    
    # Metadata
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    
    # Related documents
    related_documents: List[DocumentListItem] = Field(
        default_factory=list,
        description="Related documents"
    )
