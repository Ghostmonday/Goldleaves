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
Document bulk operations schemas.
Provides schemas for bulk operations on multiple documents.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    non_empty_string,
    uuid_field,
    timestamp_field,
    validate_non_empty_string,
    create_field_metadata,
    Status
)


class BulkAction(str, Enum):
    """Available bulk actions."""
    DELETE = "delete"
    ARCHIVE = "archive"
    RESTORE = "restore"
    MOVE = "move"
    COPY = "copy"
    UPDATE_METADATA = "update_metadata"
    CHANGE_OWNER = "change_owner"
    SET_PERMISSIONS = "set_permissions"
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    EXPORT = "export"


class BulkOperationStatus(str, Enum):
    """Bulk operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class BulkDocumentRequest(BaseModel):
    """Schema for bulk document operations."""
    
    document_ids: List[UUID] = Field(
        min_items=1,
        max_items=1000,
        title="Document IDs", description="List of document IDs to operate on (max 1000)"
    )
    
    action: BulkAction = Field(
        title="Action", description="Bulk action to perform"
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Parameters", description="Action-specific parameters"
    )
    
    async_operation: bool = Field(
        default=True,
        title="Async Operation", description="Whether to process operation asynchronously"
    )
    
    notify_on_completion: bool = Field(
        default=True,
        title="Notify on Completion", description="Whether to send notification when operation completes"
    )
    
    @validator('document_ids')
    def validate_unique_ids(cls, v):
        """Validate document IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Document IDs must be unique")
        return v


class BulkMoveRequest(BulkDocumentRequest):
    """Schema for bulk move operation."""
    
    action: Literal[BulkAction.MOVE] = Field(
        default=BulkAction.MOVE
    )
    
    destination_folder_id: UUID = Field(
        description="Destination folder ID"
    )
    
    preserve_structure: bool = Field(
        default=False,
        title="Preserve Structure",
        description="Whether to preserve folder structure during move"
    )


class BulkCopyRequest(BulkDocumentRequest):
    """Schema for bulk copy operation."""
    
    action: Literal[BulkAction.COPY] = Field(
        default=BulkAction.COPY
    )
    
    destination_folder_id: UUID = Field(
        description=""
    )
    
    name_pattern: Optional[str] = Field(
        default=None,
        title="Name Pattern", description="Pattern for naming copied documents (e.g., '{name} - Copy')"
    )
    
    preserve_structure: bool = Field(
        default=False,
        title="Preserve Structure", description="Whether to preserve folder structure during copy"
    )


class BulkMetadataUpdate(BaseModel):
    """Schema for bulk metadata updates."""
    
    title: Optional[str] = Field(
        default=None,
        title="Title", description="New title pattern (supports variables like {original_title})"
    )
    
    description: Optional[str] = Field(
        default=None,
        title="Description", description="New description"
    )
    
    tags: Optional[List[str]] = Field(
        default=None,
        title="Tags", description="Tags to set (replaces existing tags)"
    )
    
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Custom Fields", description="Custom metadata fields to update"
    )


class BulkUpdateMetadataRequest(BulkDocumentRequest):
    """Schema for bulk metadata update operation."""
    
    action: Literal[BulkAction.UPDATE_METADATA] = Field(
        default=BulkAction.UPDATE_METADATA
    )
    
    metadata_updates: BulkMetadataUpdate = Field(
        title="Metadata Updates", description="Metadata fields to update"
    )


class BulkPermissionRequest(BulkDocumentRequest):
    """Schema for bulk permission changes."""
    
    action: Literal[BulkAction.SET_PERMISSIONS] = Field(
        default=BulkAction.SET_PERMISSIONS
    )
    
    permissions: Dict[str, str] = Field(
        title="Permissions", description="Permission assignments (user/role ID -> permission level)"
    )
    
    replace_existing: bool = Field(
        default=False,
        title="Replace Existing", description="Whether to replace existing permissions or merge"
    )


class BulkTagRequest(BulkDocumentRequest):
    """Schema for bulk tag operations."""
    
    tags: List[str] = Field(
        min_items=1,
        title="Tags", description="Tags to add or remove"
    )


class BulkExportRequest(BulkDocumentRequest):
    """Schema for bulk document export."""
    
    action: Literal[BulkAction.EXPORT] = Field(
        default=BulkAction.EXPORT
    )
    
    format: str = Field(
        default="zip",
        title="Export Format", description="Export format: zip, pdf, docx, etc."
    )
    
    include_metadata: bool = Field(
        default=True,
        title="Include Metadata", description="Whether to include document metadata in export"
    )
    
    include_versions: bool = Field(
        default=False,
        title="Include Versions", description="Whether to include all document versions"
    )


class BulkOperationResult(BaseModel):
    """Individual operation result."""
    
    document_id: UUID = Field(
        description=""
    )
    
    success: bool = Field(
        title="Success", description="Whether the operation succeeded for this document"
    )
    
    error_code: Optional[str] = Field(
        default=None,
        title="Error Code", description="Error code if operation failed"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        title="Error Message", description="Error message if operation failed"
    )
    
    result_data: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Result Data", description="Operation-specific result data"
    )


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""
    
    operation_id: UUID = Field(
        description=""
    )
    
    status: BulkOperationStatus = Field(
        title="Status", description="Current operation status"
    )
    
    action: BulkAction = Field(
        title="Action", description="Bulk action performed"
    )
    
    total_documents: int = Field(
        title="Total Documents", description="Total number of documents in operation"
    )
    
    processed_documents: int = Field(
        default=0,
        title="Processed Documents", description="Number of documents processed so far"
    )
    
    successful_operations: int = Field(
        default=0,
        title="Successful Operations", description="Number of successful operations"
    )
    
    failed_operations: int = Field(
        default=0,
        title="Failed Operations", description="Number of failed operations"
    )
    
    results: Optional[List[BulkOperationResult]] = Field(
        default=None,
        title="Results", description="Detailed results for each document"
    )
    
    download_url: Optional[str] = Field(
        default=None,
        title="Download URL", description="Download URL for export operations"
    )
    
    started_at: datetime = Field(
        description="When the operation started"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the operation completed"
    )
    
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    
    created_by: UUID = Field(
        description=""
    )


class BulkOperationListParams(BaseModel):
    """Parameters for listing bulk operations."""
    
    status: Optional[BulkOperationStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by operation status"
    )
    
    action: Optional[BulkAction] = Field(
        default=None,
        title="Action Filter", description="Filter by operation action"
    )
    
    created_by: Optional[UUID] = Field(
        default=None,
        title="Created By", description="Filter by user who created the operation"
    )
    
    started_after: Optional[datetime] = Field(
        default=None,
        title="Started After", description="Filter operations started after this date"
    )
    
    started_before: Optional[datetime] = Field(
        default=None,
        title="Started Before", description="Filter operations started before this date"
    )


class BulkOperationCancel(BaseModel):
    """Schema for cancelling a bulk operation."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Reason for cancelling the operation"
    )


class BulkOperationStats(BaseModel):
    """Bulk operation statistics."""
    
    total_operations: int = Field(
        title="Total Operations", description="Total number of bulk operations"
    )
    
    operations_by_status: Dict[str, int] = Field(
        title="Operations by Status", description="Count of operations by status"
    )
    
    operations_by_action: Dict[str, int] = Field(
        title="Operations by Action", description="Count of operations by action type"
    )
    
    total_documents_processed: int = Field(
        title="Total Documents Processed", description="Total number of documents processed across all operations"
    )
    
    avg_processing_time_seconds: Optional[float] = Field(
        default=None,
        title="Average Processing Time", description="Average processing time per operation in seconds"
    )
    
    success_rate: float = Field(
        title="Success Rate", description="Overall success rate percentage"
    )
    
    last_7_days: Dict[str, int] = Field(
        title="Last 7 Days", description="Operation counts for the last 7 days"
    )
