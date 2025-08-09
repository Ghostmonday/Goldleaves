# schemas/storage/storage.py

"""Phase 7: Document storage and export schemas for secure file management."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


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


class WatermarkPosition(str, Enum):
    """Watermark positioning options."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    DIAGONAL = "diagonal"


class DocumentUploadRequest(BaseModel):
    """Request schema for secure document file upload."""
    
    file_name: str = Field(..., description="Original filename with extension")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")
    file_format: FileFormat = Field(..., description="Detected file format")
    
    # Version linking
    version_number: Optional[int] = Field(None, description="Link to specific document version")
    is_primary_file: bool = Field(True, description="Whether this is the primary document file")
    
    # Security and integrity
    client_checksum: Optional[str] = Field(None, description="Client-calculated SHA-256 checksum")
    encryption_requested: EncryptionType = Field(EncryptionType.AES_256_GCM, description="Requested encryption method")
    
    # Metadata
    upload_reason: Optional[str] = Field(None, description="Reason for file upload")
    tags: List[str] = Field(default_factory=list, description="File classification tags")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('file_name')
    def validate_filename(cls, v):
        """Validate filename for security."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in dangerous_chars):
            raise ValueError("Filename contains invalid characters")
        
        return v.strip()
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/html',
            'application/xml',
            'application/json'
        ]
        
        if v not in allowed_types:
            raise ValueError(f"Content type {v} not allowed")
        
        return v


class DocumentExportRequest(BaseModel):
    """Request schema for document export with lineage preservation."""
    
    export_format: ExportFormat = Field(..., description="Desired export format")
    include_version_history: bool = Field(True, description="Include version lineage in export")
    include_audit_trail: bool = Field(True, description="Include audit metadata")
    include_collaboration_data: bool = Field(False, description="Include collaboration information")
    
    # Version selection
    version_range: Optional[Dict[str, int]] = Field(None, description="Version range for export (from/to)")
    specific_versions: Optional[List[int]] = Field(None, description="Specific versions to include")
    
    # Formatting options
    watermark_config: Optional['WatermarkConfig'] = Field(None, description="Watermark configuration")
    ada_compliant: bool = Field(False, description="Generate ADA-compliant output")
    include_signatures: bool = Field(True, description="Include digital signatures if present")
    
    # Output customization
    filename_template: Optional[str] = Field(None, description="Custom filename template")
    bundle_related_files: bool = Field(False, description="Bundle all related files")
    compression_level: int = Field(6, ge=0, le=9, description="Compression level for archives")
    
    # Metadata injection
    embed_metadata_in_file: bool = Field(True, description="Embed metadata directly in file")
    generate_manifest: bool = Field(True, description="Generate accompanying manifest file")
    include_provenance_chain: bool = Field(True, description="Include complete provenance information")
    
    @validator('version_range')
    def validate_version_range(cls, v):
        """Validate version range."""
        if v and ('from' not in v or 'to' not in v):
            raise ValueError("Version range must include 'from' and 'to' keys")
        if v and v['from'] > v['to']:
            raise ValueError("Version range 'from' must be less than or equal to 'to'")
        return v


class WatermarkConfig(BaseModel):
    """Watermark configuration for exported documents."""
    
    text: str = Field(..., description="Watermark text")
    position: WatermarkPosition = Field(WatermarkPosition.DIAGONAL, description="Watermark position")
    opacity: float = Field(0.3, ge=0.1, le=1.0, description="Watermark opacity")
    font_size: int = Field(12, ge=8, le=72, description="Font size for watermark")
    color: str = Field("#808080", description="Watermark color (hex)")
    rotation: int = Field(45, ge=-180, le=180, description="Rotation angle in degrees")
    
    # Advanced options
    repeat_pattern: bool = Field(True, description="Repeat watermark across page")
    include_timestamp: bool = Field(True, description="Include timestamp in watermark")
    include_user_info: bool = Field(True, description="Include user information")


class DocumentFileMeta(BaseModel):
    """Comprehensive file metadata for stored documents."""
    
    # Basic file information
    file_id: str = Field(..., description="Unique file identifier")
    document_id: int = Field(..., description="Associated document ID")
    version_number: Optional[int] = Field(None, description="Associated version number")
    
    # File properties
    original_filename: str = Field(..., description="Original uploaded filename")
    stored_filename: str = Field(..., description="Internal storage filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")
    file_format: FileFormat = Field(..., description="File format")
    
    # Storage information
    storage_provider: StorageProvider = Field(..., description="Storage backend used")
    storage_path: str = Field(..., description="Storage path or bucket key")
    storage_region: Optional[str] = Field(None, description="Storage region/zone")
    
    # Security and integrity
    checksum_sha256: str = Field(..., description="SHA-256 file checksum")
    checksum_md5: str = Field(..., description="MD5 file checksum")
    encryption_type: EncryptionType = Field(..., description="Encryption method used")
    encryption_key_id: Optional[str] = Field(None, description="Encryption key identifier")
    
    # Metadata
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    uploaded_by_id: int = Field(..., description="User who uploaded the file")
    organization_id: int = Field(..., description="Organization owner")
    
    # Access tracking
    download_count: int = Field(0, description="Number of downloads")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    access_log_enabled: bool = Field(True, description="Whether access is logged")
    
    # File validation
    virus_scan_status: Optional[str] = Field(None, description="Antivirus scan result")
    virus_scan_timestamp: Optional[datetime] = Field(None, description="Scan timestamp")
    file_integrity_verified: bool = Field(False, description="Whether integrity is verified")
    
    # Retention and lifecycle
    retention_period_days: Optional[int] = Field(None, description="Retention period in days")
    auto_delete_date: Optional[datetime] = Field(None, description="Automatic deletion date")
    is_archived: bool = Field(False, description="Whether file is archived")
    archive_timestamp: Optional[datetime] = Field(None, description="Archive timestamp")
    
    # Tags and classification
    tags: List[str] = Field(default_factory=list, description="File classification tags")
    sensitivity_level: str = Field("normal", description="Data sensitivity classification")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class ExportMetadata(BaseModel):
    """Metadata embedded in exported documents."""
    
    # Document identification
    document_id: int = Field(..., description="Source document ID")
    document_title: str = Field(..., description="Document title")
    organization_name: str = Field(..., description="Organization name")
    
    # Export information
    export_timestamp: datetime = Field(..., description="Export generation timestamp")
    export_format: ExportFormat = Field(..., description="Export format used")
    exported_by: str = Field(..., description="User who generated export")
    export_reason: Optional[str] = Field(None, description="Reason for export")
    
    # Version information
    current_version: int = Field(..., description="Current document version")
    exported_versions: List[int] = Field(..., description="Versions included in export")
    version_count: int = Field(..., description="Total number of versions")
    
    # Lineage information
    creation_date: datetime = Field(..., description="Original document creation date")
    last_modified: datetime = Field(..., description="Last modification date")
    total_collaborators: int = Field(..., description="Total number of collaborators")
    total_changes: int = Field(..., description="Total number of changes")
    
    # Audit summary
    total_audit_events: int = Field(..., description="Total audit events")
    view_count: int = Field(..., description="Total view count")
    download_count: int = Field(..., description="Total download count")
    share_count: int = Field(..., description="Total share count")
    
    # Integrity verification
    content_hash: str = Field(..., description="Content integrity hash")
    metadata_hash: str = Field(..., description="Metadata integrity hash")
    digital_signature: Optional[str] = Field(None, description="Digital signature")
    
    # Compliance information
    retention_policy: Optional[str] = Field(None, description="Applied retention policy")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")
    compliance_flags: List[str] = Field(default_factory=list, description="Compliance markers")


class FileUploadResponse(BaseModel):
    """Response for successful file upload."""
    
    file_id: str = Field(..., description="Generated file identifier")
    document_id: int = Field(..., description="Associated document ID")
    stored_filename: str = Field(..., description="Internal storage filename")
    storage_path: str = Field(..., description="Storage location")
    
    # Verification results
    checksum_verified: bool = Field(..., description="Whether checksum was verified")
    virus_scan_clean: bool = Field(..., description="Virus scan result")
    encryption_applied: bool = Field(..., description="Whether encryption was applied")
    
    # Upload statistics
    upload_duration_ms: int = Field(..., description="Upload duration in milliseconds")
    file_size: int = Field(..., description="Uploaded file size")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio if applied")
    
    upload_timestamp: datetime = Field(..., description="Upload completion timestamp")
    expires_at: Optional[datetime] = Field(None, description="File expiration if temporary")


class FileRetrievalResponse(BaseModel):
    """Response for file retrieval requests."""
    
    file_meta: DocumentFileMeta = Field(..., description="File metadata")
    download_url: Optional[str] = Field(None, description="Temporary download URL")
    access_token: Optional[str] = Field(None, description="Access token for download")
    
    # Access information
    expires_at: datetime = Field(..., description="Download URL expiration")
    access_granted: bool = Field(..., description="Whether access was granted")
    access_reason: Optional[str] = Field(None, description="Reason if access denied")
    
    # File properties for client
    content_disposition: str = Field(..., description="Content-Disposition header value")
    cache_control: str = Field("no-cache", description="Cache-Control header value")
    
    # Watermarking info
    will_be_watermarked: bool = Field(False, description="Whether download will be watermarked")
    watermark_config: Optional[WatermarkConfig] = Field(None, description="Applied watermark config")


class ExportResponse(BaseModel):
    """Response for document export operations."""
    
    export_id: str = Field(..., description="Unique export identifier")
    document_id: int = Field(..., description="Source document ID")
    export_format: ExportFormat = Field(..., description="Export format")
    
    # Export results
    files_generated: List[str] = Field(..., description="Generated file names")
    bundle_path: Optional[str] = Field(None, description="Bundle file path if created")
    manifest_path: Optional[str] = Field(None, description="Manifest file path")
    
    # Export metadata
    export_metadata: ExportMetadata = Field(..., description="Embedded export metadata")
    total_file_size: int = Field(..., description="Total size of exported files")
    generation_duration_ms: int = Field(..., description="Export generation time")
    
    # Download information
    download_urls: Dict[str, str] = Field(..., description="Download URLs for generated files")
    access_expires_at: datetime = Field(..., description="Download URL expiration")
    
    # Status and validation
    export_successful: bool = Field(..., description="Whether export completed successfully")
    validation_passed: bool = Field(..., description="Whether output validation passed")
    warnings: List[str] = Field(default_factory=list, description="Export warnings")
    
    created_at: datetime = Field(..., description="Export creation timestamp")


class StorageStats(BaseModel):
    """Storage statistics for organization."""
    
    # File counts
    total_files: int = Field(..., description="Total number of files")
    files_by_format: Dict[str, int] = Field(..., description="Files grouped by format")
    files_by_encryption: Dict[str, int] = Field(..., description="Files grouped by encryption")
    
    # Storage metrics
    total_storage_bytes: int = Field(..., description="Total storage used in bytes")
    average_file_size: float = Field(..., description="Average file size")
    largest_file_size: int = Field(..., description="Largest file size")
    
    # Activity metrics
    uploads_last_30_days: int = Field(..., description="Uploads in last 30 days")
    downloads_last_30_days: int = Field(..., description="Downloads in last 30 days")
    exports_last_30_days: int = Field(..., description="Exports in last 30 days")
    
    # Storage optimization
    compression_savings_bytes: int = Field(0, description="Bytes saved through compression")
    duplicate_files_detected: int = Field(0, description="Duplicate files detected")
    archived_files: int = Field(0, description="Number of archived files")
    
    # Compliance metrics
    encrypted_files_percent: float = Field(..., description="Percentage of encrypted files")
    files_pending_retention: int = Field(0, description="Files pending retention action")
    virus_scan_coverage_percent: float = Field(..., description="Virus scan coverage")
    
    last_updated: datetime = Field(..., description="Statistics last updated timestamp")
