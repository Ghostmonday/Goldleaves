# schemas/document/__init__.py

from .audit import *
from .collaboration import *
from .core import *
from .correction import *
from .prediction import *

__all__ = [
    # Core document schemas
    "DocumentCreate",
    "DocumentUpdate", 
    "DocumentResponse",
    "DocumentFilter",
    "DocumentStats",
    "DocumentBulkAction",
    "DocumentBulkResult",
    "DocumentSearchResponse",
    "DocumentPermissionCheck",
    
    # Prediction schemas
    "DocumentPrediction",
    "PredictionField",
    "PredictionIngest",
    "PredictionConfirm",
    "PredictionReject",
    "PredictionBatch",
    "PredictionResult",
    "PredictionBatchResult",
    
    # Correction schemas
    "DocumentCorrection",
    "FieldCorrection", 
    "CorrectionCreate",
    "CorrectionUpdate",
    "CorrectionResponse",
    "CorrectionValidation",
    "CorrectionValidationResult",
    "CorrectionBatch",
    "CorrectionBatchResult",
    "CorrectionType",
    
    # Audit schemas
    "DocumentAudit",
    "DocumentVersion",
    "AuditEvent",
    "AuditTrail",
    "VersionHistory",
    "AuditFilter",
    "ComplianceReport",
    "AuditEventType",
    
    # Phase 6: Collaboration schemas
    "VersionComparisonRequest",
    "FieldDiff",
    "ContentDiff", 
    "VersionDiffResponse",
    "VersionHistoryEntry",
    "VersionHistoryResponse",
    "SecureShareCreate",
    "SecureShareResponse",
    "ShareAccessRequest",
    "ShareAccessResponse",
    "AuditEventResponse",
    "DocumentAuditTrailResponse",
    "CollaborationStats"
]

# Bulk operations schemas
from .bulk import (
    BulkAction,
    BulkCopyRequest,
    BulkDocumentRequest,
    BulkExportRequest,
    BulkMetadataUpdate,
    BulkMoveRequest,
    BulkOperationCancel,
    BulkOperationListParams,
    BulkOperationResponse,
    BulkOperationResult,
    BulkOperationStats,
    BulkOperationStatus,
    BulkPermissionRequest,
    BulkTagRequest,
    BulkUpdateMetadataRequest,
)

# Comments schemas
from .comments import (
    BulkCommentAction,
    CommentAnchor,
    CommentCreate,
    CommentListParams,
    CommentModerationRequest,
    CommentReaction,
    CommentReactionRequest,
    CommentResponse,
    CommentStats,
    CommentStatus,
    CommentThread,
    CommentType,
    CommentUpdate,
)

# Sharing schemas
from .sharing import (
    AccessLevel,
    BulkShareAction,
    DocumentPermissionCheck,
    DocumentPermissionResponse,
    DocumentShareCreate,
    DocumentShareResponse,
    DocumentShareUpdate,
    LinkAccess,
    ShareLinkAccessRequest,
    ShareListParams,
    ShareStats,
    ShareStatus,
    ShareType,
)

# Versioning schemas
from .versioning import (
    BulkVersionAction,
    ChangeType,
    DocumentVersionCreate,
    DocumentVersionResponse,
    DocumentVersionUpdate,
    MergeConflict,
    MergeConflictType,
    VersionComparisonRequest,
    VersionComparisonResponse,
    VersionDiff,
    VersionListParams,
    VersionMergeRequest,
    VersionRestoreRequest,
    VersionStats,
    VersionStatus,
    VersionType,
)

# Export all schemas for Phase 4 contract compliance
__all__ = [
    # Bulk operations
    "BulkAction",
    "BulkOperationStatus", 
    "BulkDocumentRequest",
    "BulkMoveRequest",
    "BulkCopyRequest",
    "BulkMetadataUpdate",
    "BulkPermissionUpdate",
    "BulkTagOperation",
    "BulkOperationResponse",
    "BulkOperationResult",
    "BulkListParams",
    "BulkOperationStats",
    "BulkStatusCheck",
    
    # Comments
    "CommentType",
    "CommentStatus",
    "CommentReaction",
    "CommentAnchor",
    "CommentCreate",
    "CommentUpdate", 
    "CommentResponse",
    "CommentThread",
    "CommentListParams",
    "CommentReactionRequest",
    "CommentModerationRequest",
    "CommentStats",
    "BulkCommentAction",
    
    # Sharing
    "ShareType",
    "AccessLevel",
    "ShareStatus",
    "LinkAccess",
    "DocumentShareCreate",
    "DocumentShareUpdate",
    "DocumentShareResponse",
    "ShareLinkAccessRequest",
    "DocumentPermissionCheck",
    "DocumentPermissionResponse",
    "ShareListParams",
    "ShareStats",
    "BulkShareAction",
    
    # Versioning
    "VersionType",
    "VersionStatus",
    "ChangeType",
    "MergeConflictType",
    "DocumentVersionCreate",
    "DocumentVersionUpdate",
    "DocumentVersionResponse",
    "VersionComparisonRequest",
    "VersionDiff",
    "VersionComparisonResponse",
    "VersionRestoreRequest",
    "VersionMergeRequest",
    "MergeConflict",
    "VersionListParams",
    "VersionStats",
    "BulkVersionAction",
]

# Phase 4 metadata for auto-documentation
DOCUMENT_SCHEMA_VERSION = "1.0.0"
DOCUMENT_SCHEMA_METADATA = {
    "module": "document",
    "version": DOCUMENT_SCHEMA_VERSION,
    "description": "Document management, collaboration, and operations schemas",
    "categories": {
        "bulk": "Bulk operations on multiple documents",
        "comments": "Document comments and collaboration",
        "sharing": "Document sharing and permissions",
        "versioning": "Document versioning and history"
    },
    "schema_count": len(__all__),
    "last_updated": "2024-01-20"
}

