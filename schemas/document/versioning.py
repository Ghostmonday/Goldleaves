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
Document versioning and history schemas.
Provides schemas for document versions, history tracking, and revision management.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID



class VersionType(str, Enum):
    """Type of version."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    DRAFT = "draft"
    SNAPSHOT = "snapshot"
    BACKUP = "backup"


class VersionStatus(str, Enum):
    """Version status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChangeType(str, Enum):
    """Type of change made."""
    CONTENT = "content"
    METADATA = "metadata"
    PERMISSIONS = "permissions"
    STRUCTURE = "structure"
    FORMATTING = "formatting"
    COMMENTS = "comments"


class MergeConflictType(str, Enum):
    """Type of merge conflict."""
    CONTENT = "content"
    METADATA = "metadata"
    PERMISSIONS = "permissions"
    STRUCTURE = "structure"


class DocumentVersionCreate(BaseModel):
    """Schema for creating a new document version."""
    
    version_type: VersionType = Field(
        default=VersionType.MINOR,
        title="Version Type", description="Type of version being created"
    )
    
    version_label: Optional[str] = Field(
        default=None,
        max_length=50,
        title="Version Label", description="Custom label for the version (e.g., 'Release Candidate', 'Beta')"
    )
    
    changelog: Optional[str] = Field(
        default=None,
        max_length=2000,
        title="Changelog", description="Description of changes in this version"
    )
    
    is_major: Optional[bool] = Field(
        default=None,
        title="Is Major", description="Whether this is a major version (auto-detected if not specified)"
    )
    
    tags: Optional[List[str]] = Field(
        default=None,
        title="Tags", description="Optional tags for the version"
    )
    
    copy_permissions: bool = Field(
        default=True,
        title="Copy Permissions", description="Whether to copy permissions from the current version"
    )
    
    publish_immediately: bool = Field(
        default=False,
        title="Publish Immediately", description="Whether to publish the version immediately"
    )


class DocumentVersionUpdate(BaseModel):
    """Schema for updating a document version."""
    
    version_label: Optional[str] = Field(
        default=None,
        max_length=50
    )
    
    changelog: Optional[str] = Field(
        default=None,
        max_length=2000
    )
    
    status: Optional[VersionStatus] = Field(
        default=None
    )
    
    tags: Optional[List[str]] = Field(
        default=None
    )


class DocumentVersionResponse(BaseModel):
    """Schema for document version response."""
    
    id: UUID = Field(
        description="Unique version identifier"
    )
    
    document_id: UUID = Field(
        description="Document ID"
    )
    
    version_number: str = Field(
        title="Version Number", description="Semantic version number (e.g., '1.2.3')", example="1.2.3"
    )
    
    version_type: VersionType = Field(
        title="Version Type", description="Type of version"
    )
    
    version_label: Optional[str] = Field(
        default=None,
        title="Version Label", description="Custom label for the version"
    )
    
    status: VersionStatus = Field(
        title="Status", description="Current version status"
    )
    
    title: str = Field(
        title="Title", description="Document title at this version"
    )
    
    content_hash: str = Field(
        title="Content Hash", description="Hash of the document content for integrity checking"
    )
    
    file_size: Optional[int] = Field(
        default=None,
        title="File Size", description="Size of the document in bytes"
    )
    
    changelog: Optional[str] = Field(
        default=None,
        title="Changelog", description="Description of changes in this version"
    )
    
    changes_summary: Optional[Dict[str, int]] = Field(
        default=None,
        title="Changes Summary", description="Summary of changes by type"
    )
    
    created_by: UUID = Field(
        description="User who created this version"
    )
    
    created_by_name: str = Field(
        title="Created By Name", description="Display name of user who created this version"
    )
    
    parent_version_id: Optional[UUID] = Field(
        default=None,
        description="Parent version ID"
    )
    
    is_current: bool = Field(
        title="Is Current", description="Whether this is the current version"
    )
    
    is_published: bool = Field(
        title="Is Published", description="Whether this version is published"
    )
    
    download_count: int = Field(
        default=0,
        title="Download Count", description="Number of times this version has been downloaded"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        title="Tags", description="Version tags"
    )
    
    created_at: datetime = Field(
        description="When the version was created"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When the version was last updated"
    )
    
    published_at: Optional[datetime] = Field(
        default=None,
        description="When the version was published"
    )
    
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the version expires (for drafts)"
    )


class VersionComparisonRequest(BaseModel):
    """Schema for comparing two document versions."""
    
    source_version_id: UUID = Field(
        description="Source version ID"
    )
    
    target_version_id: UUID = Field(
        description="Target version ID"
    )
    
    comparison_type: str = Field(
        default="full",
        title="Comparison Type", description="Type of comparison: 'full', 'content_only', 'metadata_only'", example="full"
    )
    
    include_formatting: bool = Field(
        default=True,
        title="Include Formatting", description="Whether to include formatting changes in comparison"
    )
    
    @validator('comparison_type')
    def validate_comparison_type(cls, v):
        """Validate comparison type."""
        allowed_types = ['full', 'content_only', 'metadata_only']
        if v not in allowed_types:
            raise ValueError(f"Comparison type must be one of: {', '.join(allowed_types)}")
        return v


class VersionDiff(BaseModel):
    """Schema for version differences."""
    
    field: str = Field(
        title="Field", description="Field that changed"
    )
    
    change_type: str = Field(
        title="Change Type", description="Type of change: 'added', 'removed', 'modified'"
    )
    
    old_value: Optional[Any] = Field(
        default=None,
        title="Old Value", description="Previous value"
    )
    
    new_value: Optional[Any] = Field(
        default=None,
        title="New Value", description="New value"
    )
    
    position: Optional[Dict[str, int]] = Field(
        default=None,
        title="Position", description="Position information for content changes"
    )


class VersionComparisonResponse(BaseModel):
    """Schema for version comparison response."""
    
    source_version: DocumentVersionResponse = Field(
        title="Source Version", description="Source version details"
    )
    
    target_version: DocumentVersionResponse = Field(
        title="Target Version", description="Target version details"
    )
    
    differences: List[VersionDiff] = Field(
        title="Differences", description="List of differences between versions"
    )
    
    changes_summary: Dict[str, int] = Field(
        title="Changes Summary", description="Summary of changes by category"
    )
    
    similarity_score: float = Field(
        title="Similarity Score", description="Similarity score between 0 and 1"
    )
    
    has_conflicts: bool = Field(
        title="Has Conflicts", description="Whether there are merge conflicts"
    )


class VersionRestoreRequest(BaseModel):
    """Schema for restoring a document version."""
    
    create_backup: bool = Field(
        default=True,
        title="Create Backup", description="Whether to create a backup of the current version"
    )
    
    restore_permissions: bool = Field(
        default=False,
        title="Restore Permissions", description="Whether to restore permissions from the target version"
    )
    
    changelog: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Changelog", description="Reason for restoring this version"
    )


class VersionMergeRequest(BaseModel):
    """Schema for merging document versions."""
    
    source_version_id: UUID = Field(
        description="Source version ID to merge from"
    )
    
    target_version_id: UUID = Field(
        description="Target version ID to merge into"
    )
    
    conflict_resolutions: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Conflict Resolutions", description="Manual resolutions for merge conflicts"
    )
    
    merge_strategy: str = Field(
        default="manual",
        title="Merge Strategy", description="Strategy for merging: 'manual', 'prefer_source', 'prefer_target'", example="manual"
    )
    
    create_new_version: bool = Field(
        default=True,
        title="Create New Version", description="Whether to create a new version for the merge result"
    )
    
    @validator('merge_strategy')
    def validate_merge_strategy(cls, v):
        """Validate merge strategy."""
        allowed_strategies = ['manual', 'prefer_source', 'prefer_target']
        if v not in allowed_strategies:
            raise ValueError(f"Merge strategy must be one of: {', '.join(allowed_strategies)}")
        return v


class MergeConflict(BaseModel):
    """Schema for merge conflicts."""
    
    field: str = Field(
        title="Field", description="Field with conflict"
    )
    
    conflict_type: MergeConflictType = Field(
        title="Conflict Type", description="Type of merge conflict"
    )
    
    source_value: Any = Field(
        title="Source Value", description="Value from source version"
    )
    
    target_value: Any = Field(
        title="Target Value", description="Value from target version"
    )
    
    position: Optional[Dict[str, int]] = Field(
        default=None,
        title="Position", description="Position information for the conflict"
    )


class VersionListParams(BaseModel):
    """Parameters for listing document versions."""
    
    status: Optional[VersionStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by version status"
    )
    
    version_type: Optional[VersionType] = Field(
        default=None,
        title="Type Filter", description="Filter by version type"
    )
    
    created_by: Optional[UUID] = Field(
        default=None,
        title="Created By Filter", description="Filter by version creator"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter versions created after this date"
    )
    
    include_drafts: bool = Field(
        default=True,
        title="Include Drafts", description="Whether to include draft versions"
    )
    
    tags: Optional[List[str]] = Field(
        default=None,
        title="Tags Filter", description="Filter by version tags"
    )


class VersionStats(BaseModel):
    """Version statistics for a document."""
    
    total_versions: int = Field(
        title="Total Versions", description="Total number of versions"
    )
    
    published_versions: int = Field(
        title="Published Versions", description="Number of published versions"
    )
    
    draft_versions: int = Field(
        title="Draft Versions", description="Number of draft versions"
    )
    
    versions_by_type: Dict[str, int] = Field(
        title="Versions by Type", description="Version count breakdown by type"
    )
    
    current_version: str = Field(
        title="Current Version", description="Current version number"
    )
    
    latest_published_version: Optional[str] = Field(
        default=None,
        title="Latest Published Version", description="Latest published version number"
    )
    
    total_downloads: int = Field(
        title="Total Downloads", description="Total downloads across all versions"
    )
    
    avg_version_size: Optional[float] = Field(
        default=None,
        title="Average Version Size", description="Average version size in bytes"
    )
    
    version_frequency_days: Optional[float] = Field(
        default=None,
        title="Version Frequency", description="Average days between versions"
    )
    
    last_version_created: Optional[datetime] = Field(
        default=None,
        description="When the last version was created"
    )


class BulkVersionAction(BaseModel):
    """Schema for bulk version operations."""
    
    version_ids: List[UUID] = Field(
        min_items=1,
        max_items=50,
        title="Version IDs", description="List of version IDs to operate on (max 50)"
    )
    
    action: str = Field(
        title="Action", description="Action to perform: 'publish', 'archive', 'delete', 'tag'"
    )
    
    # For tag action
    tags: Optional[List[str]] = Field(
        default=None,
        title="Tags", description="Tags to add (for 'tag' action)"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate bulk action."""
        allowed_actions = ['publish', 'archive', 'delete', 'tag']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v
