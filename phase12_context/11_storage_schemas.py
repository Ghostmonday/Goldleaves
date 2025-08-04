# schemas/storage/storage.py
"""Phase 7: Document storage and export schemas for secure file management."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class FileFormat(str, Enum):
    """Supported file formats for storage and export."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    XML = "xml"
    JSON = "json"


class ExportFormat(str, Enum):
    """Available export formats with metadata embedding."""
    PDF_ANNOTATED = "pdf_annotated"
    PDF_CLEAN = "pdf_clean"
    DOCX_WITH_COMMENTS = "docx_with_comments"
    DOCX_CLEAN = "docx_clean"
    HTML_REPORT = "html_report"
    JSON_STRUCTURED = "json_structured"
    ARCHIVE_BUNDLE = "archive_bundle"


class StorageProvider(str, Enum):
    """Storage backend providers."""
    LOCAL_FILESYSTEM = "local_filesystem"
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD = "google_cloud"


class EncryptionType(str, Enum):
    """Encryption methods for file storage."""
    NONE = "none"
    AES_256_GCM = "aes_256_gcm"
    RSA_2048 = "rsa_2048"
    HYBRID_AES_RSA = "hybrid_aes_rsa"


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    document_type: str = Field(..., description="Type of document")
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    document_id: str
    title: str
    file_size: int
    file_format: FileFormat
    upload_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    success: bool = True
    message: str = "Document uploaded successfully"


class DocumentMetadata(BaseModel):
    """Document metadata schema."""
    document_id: str
    title: str
    description: Optional[str] = None
    file_name: str
    file_size: int
    file_format: FileFormat
    content_type: str
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    organization_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExportRequest(BaseModel):
    """Request schema for document export."""
    document_ids: List[str] = Field(..., min_items=1)
    export_format: ExportFormat
    include_metadata: bool = True
    include_comments: bool = True
    watermark_text: Optional[str] = None
    password_protect: bool = False


class ExportResponse(BaseModel):
    """Response schema for document export."""
    export_id: str
    status: str = "processing"
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
