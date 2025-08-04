# schemas/client/documents.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from ..base.responses import PaginatedResponse


class ClientDocumentBase(BaseModel):
    """Base client document schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Document name")
    description: Optional[str] = Field(None, description="Document description")
    document_type: Optional[str] = Field(None, max_length=100, description="Document type")


class ClientDocumentCreate(ClientDocumentBase):
    """Schema for creating a client document."""
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Driver's License Copy",
                "description": "Copy of client's driver's license for ID verification",
                "document_type": "identification",
                "mime_type": "image/jpeg"
            }
        }


class ClientDocumentUpdate(BaseModel):
    """Schema for updating a client document."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = Field(None, max_length=100)


class ClientDocumentResponse(ClientDocumentBase):
    """Schema for client document response."""
    id: int
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    client_id: int
    organization_id: int
    uploaded_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    file_size_mb: Optional[float] = Field(None, description="File size in MB")
    upload_url: Optional[str] = Field(None, description="URL for file upload")
    download_url: Optional[str] = Field(None, description="URL for file download")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Driver's License Copy",
                "description": "Copy of client's driver's license for ID verification",
                "document_type": "identification",
                "file_path": "/uploads/clients/1/documents/drivers_license.jpg",
                "file_size": 2048576,
                "file_size_mb": 2.0,
                "mime_type": "image/jpeg",
                "client_id": 1,
                "organization_id": 1,
                "uploaded_by_id": 2,
                "created_at": "2025-08-02T10:00:00Z",
                "updated_at": "2025-08-02T10:00:00Z"
            }
        }


class ClientDocumentListResponse(PaginatedResponse):
    """Paginated list of client documents."""
    items: List[ClientDocumentResponse]


class ClientDocumentFilter(BaseModel):
    """Client document filtering parameters."""
    document_type: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in name and description")
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    uploaded_by_id: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "document_type": "identification",
                "search": "license",
                "uploaded_after": "2025-01-01T00:00:00Z"
            }
        }
