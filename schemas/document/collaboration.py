# schemas/document/collaboration.py

"""Phase 6: Document collaboration schemas for version control, diffing, and secure sharing."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime
from enum import Enum

from models.document import AuditEventType, SecureSharePermission


class VersionComparisonRequest(BaseModel):
    """Request schema for version comparison."""
    from_version: int = Field(..., ge=1, description="Source version number")
    to_version: int = Field(..., ge=1, description="Target version number")
    include_content_diff: bool = Field(True, description="Include content-level diff")
    include_metadata_diff: bool = Field(True, description="Include metadata changes")
    diff_format: str = Field("unified", pattern="^(unified|side_by_side|json)$", description="Diff format")
    
    @validator('to_version')
    def validate_version_order(cls, v, values):
        if 'from_version' in values and v <= values['from_version']:
            raise ValueError('to_version must be greater than from_version')
        return v


class FieldDiff(BaseModel):
    """Individual field difference."""
    field_path: str = Field(..., description="JSON path to the field")
    field_type: str = Field(..., description="Type of field (text, number, date, etc.)")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Optional[Any] = Field(None, description="New value")
    change_type: str = Field(..., pattern="^(added|modified|removed)$", description="Type of change")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in diff accuracy")
    
    class Config:
        schema_extra = {
            "example": {
                "field_path": "contract.parties.0.name",
                "field_type": "text",
                "old_value": "ACME Corp",
                "new_value": "ACME Corporation",
                "change_type": "modified",
                "confidence": 0.95
            }
        }


class ContentDiff(BaseModel):
    """Content-level difference representation."""
    diff_format: str = Field(..., description="Format of the diff")
    diff_content: str = Field(..., description="Diff content in specified format")
    additions_count: int = Field(0, ge=0, description="Number of additions")
    deletions_count: int = Field(0, ge=0, description="Number of deletions")
    modifications_count: int = Field(0, ge=0, description="Number of modifications")
    context_lines: int = Field(3, ge=0, description="Number of context lines")
    
    class Config:
        schema_extra = {
            "example": {
                "diff_format": "unified",
                "diff_content": "@@ -1,3 +1,3 @@\n This is a test\n-Old line\n+New line\n Another line",
                "additions_count": 1,
                "deletions_count": 1,
                "modifications_count": 0,
                "context_lines": 3
            }
        }


class VersionDiffResponse(BaseModel):
    """Response schema for version comparison."""
    document_id: int
    from_version: int
    to_version: int
    
    # Diff data
    field_diffs: List[FieldDiff] = Field(default_factory=list)
    content_diff: Optional[ContentDiff] = None
    metadata_changes: Dict[str, Any] = Field(default_factory=dict)
    
    # Summary statistics
    total_changes: int = Field(0, description="Total number of changes")
    significant_changes: int = Field(0, description="Number of significant changes")
    diff_summary: str = Field("", description="Human-readable summary")
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_method: str = Field("automated", description="How diff was generated")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 123,
                "from_version": 1,
                "to_version": 2,
                "field_diffs": [
                    {
                        "field_path": "title",
                        "field_type": "text",
                        "old_value": "Draft Contract",
                        "new_value": "Final Contract",
                        "change_type": "modified"
                    }
                ],
                "total_changes": 3,
                "significant_changes": 1,
                "diff_summary": "Title updated from draft to final version"
            }
        }


class VersionHistoryEntry(BaseModel):
    """Individual version history entry."""
    version_number: int
    title: str
    change_summary: str
    change_reason: Optional[str] = None
    changed_by_name: Optional[str] = None
    changed_by_id: Optional[int] = None
    created_at: datetime
    
    # Version metadata
    prediction_status: Optional[str] = None
    prediction_score: Optional[float] = None
    content_length: Optional[int] = None
    has_corrections: bool = False
    
    # Quick diff indicators
    changes_from_previous: Optional[int] = Field(None, description="Number of changes from previous version")
    is_major_version: bool = Field(False, description="Whether this is a major version change")
    
    class Config:
        schema_extra = {
            "example": {
                "version_number": 2,
                "title": "Final Service Agreement",
                "change_summary": "Updated terms and conditions, added liability clause",
                "change_reason": "Legal review completed",
                "changed_by_name": "John Doe",
                "created_at": "2025-08-02T14:30:00Z",
                "prediction_status": "confirmed",
                "prediction_score": 0.92,
                "changes_from_previous": 5,
                "is_major_version": True
            }
        }


class VersionHistoryResponse(BaseModel):
    """Response schema for version history."""
    document_id: int
    current_version: int
    total_versions: int
    
    versions: List[VersionHistoryEntry] = Field(default_factory=list)
    
    # Timeline metadata
    first_created: datetime
    last_modified: datetime
    total_changes: int = Field(0, description="Total changes across all versions")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 123,
                "current_version": 3,
                "total_versions": 3,
                "versions": [
                    {
                        "version_number": 3,
                        "title": "Final Service Agreement",
                        "change_summary": "Final approval and signature",
                        "changed_by_name": "Legal Admin",
                        "created_at": "2025-08-02T16:00:00Z"
                    }
                ],
                "first_created": "2025-08-01T10:00:00Z",
                "last_modified": "2025-08-02T16:00:00Z",
                "total_changes": 12
            }
        }


class SecureShareCreate(BaseModel):
    """Schema for creating secure document shares."""
    recipient_email: Optional[str] = Field(None, max_length=255, description="Recipient email address")
    recipient_name: Optional[str] = Field(None, max_length=255, description="Recipient name")
    
    # Permissions
    permission_level: SecureSharePermission = Field(
        SecureSharePermission.VIEW_ONLY,
        description="Permission level for the share"
    )
    
    # Access restrictions
    expires_at: Optional[datetime] = Field(None, description="Share expiration time")
    allowed_views: int = Field(-1, ge=-1, description="Maximum number of views (-1 for unlimited)")
    allowed_downloads: int = Field(0, ge=0, description="Maximum number of downloads")
    requires_access_code: bool = Field(False, description="Whether to require an access code")
    
    # Advanced security
    ip_whitelist: List[str] = Field(default_factory=list, description="Allowed IP addresses")
    requires_authentication: bool = Field(False, description="Require user authentication")
    watermark_text: Optional[str] = Field(None, max_length=255, description="Watermark text")
    
    # Notifications and tracking
    track_access: bool = Field(True, description="Track access to the share")
    notify_on_access: bool = Field(False, description="Send notifications on access")
    
    # Sharing context
    share_reason: Optional[str] = Field(None, description="Reason for sharing")
    internal_notes: Optional[str] = Field(None, description="Internal notes about the share")
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError('Expiration time must be in the future')
        return v
    
    @validator('ip_whitelist')
    def validate_ip_addresses(cls, v):
        # Simple IP validation - in production, use proper IP validation
        import re
        ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        for ip in v:
            if not re.match(ip_pattern, ip):
                raise ValueError(f'Invalid IP address: {ip}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "client@company.com",
                "recipient_name": "John Smith",
                "permission_level": "view_only",
                "expires_at": "2025-08-09T23:59:59Z",
                "allowed_views": 5,
                "requires_access_code": True,
                "track_access": True,
                "share_reason": "Client review of contract terms",
                "watermark_text": "CONFIDENTIAL - Client Review Only"
            }
        }


class SecureShareResponse(BaseModel):
    """Response schema for secure document shares."""
    id: int
    document_id: int
    share_slug: str
    access_code: Optional[str] = None
    
    # Share URL
    share_url: str = Field(..., description="Complete share URL")
    
    # Configuration
    permission_level: SecureSharePermission
    expires_at: Optional[datetime] = None
    allowed_views: int
    view_count: int
    allowed_downloads: int
    download_count: int
    
    # Status
    is_active: bool
    is_expired: bool
    is_valid: bool
    
    # Metadata
    created_at: datetime
    shared_by_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    share_reason: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "document_id": 123,
                "share_slug": "abc123def456ghi789jkl012mno345pq",
                "access_code": "789123",
                "share_url": "https://app.goldleaves.com/share/abc123def456ghi789jkl012mno345pq",
                "permission_level": "view_only",
                "expires_at": "2025-08-09T23:59:59Z",
                "allowed_views": 5,
                "view_count": 2,
                "is_active": True,
                "is_expired": False,
                "is_valid": True,
                "recipient_email": "client@company.com",
                "share_reason": "Contract review"
            }
        }


class ShareAccessRequest(BaseModel):
    """Request schema for accessing shared documents."""
    access_code: Optional[str] = Field(None, description="Access code if required")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    class Config:
        schema_extra = {
            "example": {
                "access_code": "789123"
            }
        }


class ShareAccessResponse(BaseModel):
    """Response schema for shared document access."""
    success: bool
    document_title: str
    document_type: str
    permission_level: SecureSharePermission
    
    # Document metadata (limited based on permissions)
    created_at: datetime
    file_size: Optional[int] = None
    watermark_text: Optional[str] = None
    
    # Access tracking
    remaining_views: Optional[int] = None
    remaining_downloads: Optional[int] = None
    
    # Download URL (if permitted)
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "document_title": "Service Agreement - ACME Corp",
                "document_type": "contract",
                "permission_level": "view_only",
                "created_at": "2025-08-01T10:00:00Z",
                "file_size": 245760,
                "remaining_views": 3,
                "watermark_text": "CONFIDENTIAL - Client Review Only"
            }
        }


class AuditEventResponse(BaseModel):
    """Response schema for audit events."""
    id: int
    event_type: AuditEventType
    event_description: str
    user_name: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    
    # Event context
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    
    # Change details
    field_changes: Dict[str, Any] = Field(default_factory=dict)
    before_data: Dict[str, Any] = Field(default_factory=dict)
    after_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "event_type": "correction_applied",
                "event_description": "Applied human corrections to 3 fields",
                "user_name": "Legal Expert",
                "user_id": 123,
                "created_at": "2025-08-02T14:30:00Z",
                "ip_address": "192.168.1.100",
                "field_changes": {
                    "contract_type": {
                        "old": "service_agreement",
                        "new": "consulting_agreement"
                    }
                }
            }
        }


class DocumentAuditTrailResponse(BaseModel):
    """Complete audit trail response."""
    document_id: int
    current_version: int
    total_events: int
    
    # Event timeline
    events: List[AuditEventResponse] = Field(default_factory=list)
    
    # Summary statistics
    event_types_summary: Dict[str, int] = Field(default_factory=dict)
    user_activity_summary: Dict[str, int] = Field(default_factory=dict)
    
    # Timeline boundaries
    first_event: Optional[datetime] = None
    last_event: Optional[datetime] = None
    
    # Compliance metrics
    total_views: int = 0
    total_downloads: int = 0
    total_shares: int = 0
    total_corrections: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 123,
                "current_version": 3,
                "total_events": 15,
                "events": [
                    {
                        "id": 789,
                        "event_type": "created",
                        "event_description": "Document created",
                        "user_name": "John Doe",
                        "created_at": "2025-08-01T10:00:00Z"
                    }
                ],
                "event_types_summary": {
                    "created": 1,
                    "updated": 3,
                    "shared": 2,
                    "correction_applied": 2
                },
                "total_views": 45,
                "total_shares": 2,
                "total_corrections": 5
            }
        }


class CollaborationStats(BaseModel):
    """Organization collaboration statistics."""
    total_documents: int
    total_versions: int
    total_secure_shares: int
    total_audit_events: int
    
    # Recent activity (last 30 days)
    recent_collaborations: int
    recent_shares_created: int
    recent_versions_created: int
    
    # Top collaboration metrics
    most_collaborated_documents: List[Dict[str, Any]] = Field(default_factory=list)
    most_active_collaborators: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Sharing statistics
    active_shares: int
    expired_shares: int
    average_share_duration_days: float
    
    class Config:
        schema_extra = {
            "example": {
                "total_documents": 1250,
                "total_versions": 3875,
                "total_secure_shares": 425,
                "total_audit_events": 12450,
                "recent_collaborations": 89,
                "recent_shares_created": 23,
                "active_shares": 67,
                "average_share_duration_days": 7.5,
                "most_collaborated_documents": [
                    {"title": "Master Service Agreement", "versions": 12, "collaborators": 5}
                ]
            }
        }
