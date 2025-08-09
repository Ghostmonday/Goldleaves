# schemas/document/core.py

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from models.document import (
    PredictionStatus, DocumentType, DocumentStatus, DocumentConfidentiality
)


class AddressSchema(BaseModel):
    """Address schema for document metadata."""
    line1: Optional[str] = Field(None, max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=3)


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    document_type: DocumentType = Field(..., description="Type of document")
    status: DocumentStatus = Field(DocumentStatus.DRAFT, description="Document status")
    confidentiality: DocumentConfidentiality = Field(
        DocumentConfidentiality.INTERNAL, 
        description="Confidentiality level"
    )
    
    # File information (if uploading)
    file_name: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=1000)
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100)
    file_hash: Optional[str] = Field(None, max_length=64, description="SHA-256 hash")
    
    # Content
    content: Optional[str] = Field(None, description="Extracted text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    # AI Predictions (optional for initial creation)
    ai_predictions: Dict[str, Any] = Field(default_factory=dict, description="AI predictions")
    prediction_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="AI confidence score"
    )
    
    # Relationships
    case_id: Optional[int] = Field(None, description="Associated case ID")
    client_id: Optional[int] = Field(None, description="Associated client ID") 
    
    # Tags and metadata
    tags: List[str] = Field(default_factory=list, description="Document tags")
    legal_hold: bool = Field(False, description="Legal hold status")
    retention_date: Optional[datetime] = Field(None, description="Document retention date")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        if v:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("Tags must be non-empty strings")
        return [tag.strip().lower() for tag in v] if v else []
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable (max 100MB)."""
        if v is not None and v > 100 * 1024 * 1024:  # 100MB
            raise ValueError("File size cannot exceed 100MB")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Service Agreement - Acme Corp",
                "description": "Master service agreement with Acme Corporation",
                "document_type": "contract",
                "status": "under_review",
                "confidentiality": "attorney_client_privileged",
                "file_name": "acme_service_agreement.pdf",
                "mime_type": "application/pdf",
                "content": "This Agreement is entered into...",
                "metadata": {
                    "contract_value": 250000.00,
                    "effective_date": "2025-01-01",
                    "expiration_date": "2025-12-31"
                },
                "case_id": 1,
                "client_id": 1,
                "tags": ["contract", "service", "acme"],
                "legal_hold": True
            }
        }


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None)
    document_type: Optional[DocumentType] = Field(None)
    status: Optional[DocumentStatus] = Field(None)
    confidentiality: Optional[DocumentConfidentiality] = Field(None)
    
    content: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    
    case_id: Optional[int] = Field(None)
    client_id: Optional[int] = Field(None)
    
    tags: Optional[List[str]] = Field(None)
    legal_hold: Optional[bool] = Field(None)
    retention_date: Optional[datetime] = Field(None)
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        if v is not None:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("Tags must be non-empty strings")
            return [tag.strip().lower() for tag in v]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Updated Service Agreement - Acme Corp",
                "status": "approved",
                "metadata": {
                    "contract_value": 275000.00,
                    "amended_date": "2025-02-01"
                },
                "tags": ["contract", "service", "acme", "amended"]
            }
        }


class DocumentResponse(BaseModel):
    """Schema for document responses."""
    id: int
    title: str
    description: Optional[str]
    document_type: str
    status: str
    confidentiality: str
    
    # File information
    file_name: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    file_hash: Optional[str]
    
    # Content (may be truncated)
    content: Optional[str]
    content_preview: Optional[str] = Field(None, description="First 500 characters of content")
    metadata: Dict[str, Any]
    
    # AI Prediction information
    prediction_status: str
    prediction_score: Optional[float]
    confidence_level: Optional[str] = Field(None, description="Human-readable confidence")
    ai_predictions: Dict[str, Any]
    corrections: Dict[str, Any]
    
    # Version and audit
    version: int
    edited_by_id: Optional[int]
    edited_at: Optional[datetime]
    correction_count: int = Field(0, description="Number of corrections made")
    
    # Relationships
    case_id: Optional[int]
    client_id: Optional[int]
    organization_id: int
    created_by_id: int
    
    # Metadata
    tags: List[str]
    legal_hold: bool
    retention_date: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    
    @validator('content_preview', pre=True, always=True)
    def generate_content_preview(cls, v, values):
        """Generate content preview from full content."""
        if v is None and 'content' in values and values['content']:
            return values['content'][:500] + "..." if len(values['content']) > 500 else values['content']
        return v
    
    @validator('confidence_level', pre=True, always=True)
    def generate_confidence_level(cls, v, values):
        """Generate human-readable confidence level."""
        if v is None and 'prediction_score' in values:
            score = values['prediction_score']
            if score is None:
                return "unknown"
            elif score >= 0.9:
                return "high"
            elif score >= 0.7:
                return "medium"
            elif score >= 0.5:
                return "low"
            else:
                return "very_low"
        return v
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Service Agreement - Acme Corp",
                "description": "Master service agreement",
                "document_type": "contract",
                "status": "approved",
                "confidentiality": "attorney_client_privileged",
                "file_name": "acme_service_agreement.pdf",
                "mime_type": "application/pdf",
                "content_preview": "This Agreement is entered into between...",
                "prediction_status": "confirmed",
                "prediction_score": 0.92,
                "confidence_level": "high",
                "version": 3,
                "correction_count": 2,
                "case_id": 1,
                "client_id": 1,
                "tags": ["contract", "service", "acme"],
                "legal_hold": True,
                "created_at": "2025-08-01T10:00:00Z"
            }
        }


class DocumentFilter(BaseModel):
    """Advanced filtering for document queries."""
    search: Optional[str] = Field(None, description="Search in title, content, metadata")
    document_type: Optional[DocumentType] = Field(None)
    status: Optional[DocumentStatus] = Field(None)
    confidentiality: Optional[DocumentConfidentiality] = Field(None)
    prediction_status: Optional[PredictionStatus] = Field(None)
    
    case_id: Optional[int] = Field(None)
    client_id: Optional[int] = Field(None)
    created_by_id: Optional[int] = Field(None)
    
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    legal_hold: Optional[bool] = Field(None)
    
    # Score filtering
    min_prediction_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_prediction_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Date filtering
    created_after: Optional[datetime] = Field(None)
    created_before: Optional[datetime] = Field(None)
    updated_after: Optional[datetime] = Field(None)
    updated_before: Optional[datetime] = Field(None)
    
    # Content filtering
    has_content: Optional[bool] = Field(None, description="Filter documents with/without content")
    has_predictions: Optional[bool] = Field(None, description="Filter documents with/without AI predictions")
    needs_review: Optional[bool] = Field(None, description="Documents needing human review")
    
    class Config:
        schema_extra = {
            "example": {
                "search": "acme contract",
                "document_type": "contract",
                "status": "approved",
                "prediction_status": "confirmed",
                "case_id": 1,
                "tags": ["contract", "high-value"],
                "min_prediction_score": 0.8,
                "needs_review": False,
                "created_after": "2025-01-01T00:00:00Z"
            }
        }


class DocumentStats(BaseModel):
    """Document statistics for organization."""
    total_documents: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_confidentiality: Dict[str, int] = Field(default_factory=dict)
    by_prediction_status: Dict[str, int] = Field(default_factory=dict)
    
    # Prediction accuracy metrics
    average_prediction_score: float = 0.0
    high_confidence_count: int = 0  # score >= 0.9
    medium_confidence_count: int = 0  # 0.7 <= score < 0.9
    low_confidence_count: int = 0  # score < 0.7
    
    # Correction metrics
    total_corrections: int = 0
    documents_with_corrections: int = 0
    average_corrections_per_document: float = 0.0
    
    # Content metrics
    total_file_size: int = 0  # Total size in bytes
    documents_with_content: int = 0
    documents_pending_review: int = 0
    
    # Recent activity
    recent_documents: int = 0  # Last 30 days
    recent_corrections: int = 0  # Last 30 days
    
    class Config:
        schema_extra = {
            "example": {
                "total_documents": 245,
                "by_type": {
                    "contract": 120,
                    "legal_brief": 45,
                    "correspondence": 80
                },
                "by_status": {
                    "approved": 180,
                    "under_review": 45,
                    "draft": 20
                },
                "average_prediction_score": 0.87,
                "high_confidence_count": 190,
                "total_corrections": 89,
                "documents_with_corrections": 67,
                "documents_pending_review": 23,
                "recent_documents": 15
            }
        }


class DocumentBulkAction(BaseModel):
    """Bulk action schema for documents."""
    document_ids: List[int] = Field(..., description="List of document IDs")
    action: str = Field(..., description="Action: update_status, update_confidentiality, add_tags, remove_tags, apply_legal_hold, remove_legal_hold")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "document_ids": [1, 2, 3, 4],
                "action": "update_status",
                "parameters": {"status": "approved"}
            }
        }


class DocumentBulkResult(BaseModel):
    """Result of bulk document operations."""
    success_count: int = 0
    error_count: int = 0
    updated_documents: List[int] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "success_count": 3,
                "error_count": 1,
                "updated_documents": [1, 2, 3],
                "errors": [{"document_id": 4, "error": "Document not found"}]
            }
        }


class DocumentSearchResponse(BaseModel):
    """Simplified document response for search results."""
    id: int
    title: str
    document_type: DocumentType
    status: DocumentStatus
    prediction_score: Optional[float] = None
    case_title: Optional[str] = None
    client_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 123,
                "title": "Service Agreement - ACME Corp",
                "document_type": "contract",
                "status": "final",
                "prediction_score": 0.89,
                "case_title": "ACME Corp Legal Review",
                "client_name": "ACME Corporation"
            }
        }


class DocumentPermissionCheck(BaseModel):
    """Document permission check response."""
    can_read: bool = True
    can_update: bool = False
    can_delete: bool = False
    can_share: bool = False
    can_correct: bool = False
    can_predict: bool = False
    is_owner: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "can_read": True,
                "can_update": True,
                "can_delete": False,
                "can_share": True,
                "can_correct": True,
                "can_predict": True,
                "is_owner": True
            }
        }
