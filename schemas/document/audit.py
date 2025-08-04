# schemas/document/audit.py

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events for documents."""
    CREATED = "created"
    UPDATED = "updated"
    PREDICTION_INGESTED = "prediction_ingested"
    CORRECTION_APPLIED = "correction_applied"
    STATUS_CHANGED = "status_changed"
    REVIEWED = "reviewed"
    SHARED = "shared"
    DOWNLOADED = "downloaded"
    DELETED = "deleted"
    RESTORED = "restored"
    LEGAL_HOLD_APPLIED = "legal_hold_applied"
    LEGAL_HOLD_REMOVED = "legal_hold_removed"


class DocumentVersion(BaseModel):
    """Schema for document version information."""
    id: int
    document_id: int
    version_number: int
    
    # Version snapshot
    title: str
    content: Optional[str]
    metadata: Dict[str, Any]
    ai_predictions: Dict[str, Any]
    corrections: Dict[str, Any]
    prediction_status: str
    prediction_score: Optional[float]
    
    # Version metadata
    change_summary: Optional[str]
    change_reason: Optional[str]
    changed_by_id: int
    changed_by_name: Optional[str] = Field(None, description="Name of user who made the change")
    
    # Timestamps
    created_at: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "document_id": 1,
                "version_number": 2,
                "title": "Service Agreement - Acme Corp",
                "change_summary": "Updated contract value and terms",
                "change_reason": "Client amendment request",
                "changed_by_id": 1,
                "changed_by_name": "John Attorney",
                "prediction_status": "partially_confirmed",
                "prediction_score": 0.89,
                "created_at": "2025-08-02T10:30:00Z"
            }
        }


class AuditEvent(BaseModel):
    """Individual audit event record."""
    id: int
    document_id: int
    event_type: AuditEventType
    event_description: str
    
    # Event details
    details: Dict[str, Any] = Field(default_factory=dict, description="Event-specific details")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Values before change")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Values after change")
    
    # User and system information
    user_id: Optional[int] = Field(None, description="User who triggered the event")
    user_name: Optional[str] = Field(None, description="Name of user")
    system_triggered: bool = Field(False, description="Whether event was system-triggered")
    ip_address: Optional[str] = Field(None, description="IP address of user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    # Timestamps
    timestamp: datetime
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "document_id": 1,
                "event_type": "correction_applied",
                "event_description": "Contract value corrected from $250,000 to $275,000",
                "details": {
                    "field_path": "contract_value",
                    "correction_type": "modify",
                    "correction_reason": "Contract amendment"
                },
                "old_values": {"contract_value": 250000.00},
                "new_values": {"contract_value": 275000.00},
                "user_id": 1,
                "user_name": "John Attorney",
                "system_triggered": False,
                "timestamp": "2025-08-02T10:30:00Z"
            }
        }


class DocumentAudit(BaseModel):
    """Complete audit information for a document."""
    document_id: int
    current_version: int
    total_versions: int
    total_corrections: int
    total_events: int
    
    # Latest activity
    last_modified: Optional[datetime]
    last_modified_by: Optional[str]
    last_correction: Optional[datetime]
    last_correction_by: Optional[str]
    
    # Version history (limited)
    recent_versions: List[DocumentVersion] = Field(default_factory=list, description="Last 5 versions")
    
    # Audit events (limited)
    recent_events: List[AuditEvent] = Field(default_factory=list, description="Last 10 events")
    
    # Correction summary
    correction_summary: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Summary of corrections by field"
    )
    
    # Prediction accuracy tracking
    prediction_accuracy: Optional[Dict[str, Any]] = Field(
        None, 
        description="Accuracy metrics for AI predictions"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 1,
                "current_version": 3,
                "total_versions": 3,
                "total_corrections": 2,
                "total_events": 8,
                "last_modified": "2025-08-02T10:30:00Z",
                "last_modified_by": "John Attorney",
                "last_correction": "2025-08-02T10:30:00Z",
                "last_correction_by": "John Attorney",
                "correction_summary": {
                    "contract_value": {
                        "correction_count": 1,
                        "last_corrected": "2025-08-02T10:30:00Z",
                        "accuracy_improvement": 0.15
                    }
                },
                "prediction_accuracy": {
                    "overall_accuracy": 0.87,
                    "field_accuracy": {
                        "contract_value": 0.85,
                        "effective_date": 0.92
                    }
                }
            }
        }


class VersionHistory(BaseModel):
    """Complete version history for a document."""
    document_id: int
    versions: List[DocumentVersion] = Field(default_factory=list)
    total_versions: int
    
    # Version comparison capabilities
    has_content_changes: bool = Field(False, description="Whether content has changed between versions")
    has_metadata_changes: bool = Field(False, description="Whether metadata has changed")
    has_prediction_changes: bool = Field(False, description="Whether predictions have changed")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 1,
                "total_versions": 3,
                "has_content_changes": True,
                "has_metadata_changes": True,
                "has_prediction_changes": False,
                "versions": [
                    {
                        "version_number": 1,
                        "change_summary": "Initial creation",
                        "created_at": "2025-08-01T09:00:00Z"
                    },
                    {
                        "version_number": 2,
                        "change_summary": "AI predictions ingested",
                        "created_at": "2025-08-01T10:00:00Z"
                    }
                ]
            }
        }


class AuditTrail(BaseModel):
    """Complete audit trail for a document."""
    document_id: int
    events: List[AuditEvent] = Field(default_factory=list)
    total_events: int
    
    # Event filtering and pagination
    event_types_present: List[str] = Field(default_factory=list, description="Types of events in trail")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range of events")
    
    # Summary statistics
    events_by_type: Dict[str, int] = Field(default_factory=dict, description="Count of events by type")
    events_by_user: Dict[str, int] = Field(default_factory=dict, description="Count of events by user")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": 1,
                "total_events": 8,
                "event_types_present": ["created", "prediction_ingested", "correction_applied"],
                "date_range": {
                    "earliest": "2025-08-01T09:00:00Z",
                    "latest": "2025-08-02T10:30:00Z"
                },
                "events_by_type": {
                    "created": 1,
                    "prediction_ingested": 1,
                    "correction_applied": 2,
                    "updated": 4
                },
                "events_by_user": {
                    "John Attorney": 6,
                    "System": 2
                }
            }
        }


class AuditFilter(BaseModel):
    """Filtering options for audit queries."""
    event_types: Optional[List[AuditEventType]] = Field(None, description="Filter by event types")
    user_id: Optional[int] = Field(None, description="Filter by user")
    date_from: Optional[datetime] = Field(None, description="Filter events from date")
    date_to: Optional[datetime] = Field(None, description="Filter events to date")
    system_events: Optional[bool] = Field(None, description="Include/exclude system events")
    
    class Config:
        schema_extra = {
            "example": {
                "event_types": ["correction_applied", "reviewed"],
                "user_id": 1,
                "date_from": "2025-08-01T00:00:00Z",
                "date_to": "2025-08-02T23:59:59Z",
                "system_events": False
            }
        }


class ComplianceReport(BaseModel):
    """Compliance and audit report for documents."""
    report_id: str
    organization_id: int
    report_period: Dict[str, datetime]
    generated_at: datetime
    generated_by_id: int
    
    # Document statistics
    total_documents: int
    documents_with_predictions: int
    documents_with_corrections: int
    documents_under_legal_hold: int
    
    # Prediction accuracy metrics
    overall_prediction_accuracy: float
    accuracy_by_document_type: Dict[str, float]
    accuracy_trends: List[Dict[str, Any]]
    
    # Correction metrics
    total_corrections: int
    corrections_by_type: Dict[str, int]
    correction_response_times: Dict[str, float]  # Average time to correct by type
    
    # Compliance indicators
    documents_requiring_review: int
    overdue_reviews: int
    retention_compliance: Dict[str, Any]
    access_log_summary: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "compliance_202508_001",
                "organization_id": 1,
                "report_period": {
                    "start": "2025-08-01T00:00:00Z",
                    "end": "2025-08-31T23:59:59Z"
                },
                "generated_at": "2025-08-02T10:30:00Z",
                "total_documents": 245,
                "documents_with_predictions": 200,
                "documents_with_corrections": 67,
                "overall_prediction_accuracy": 0.87,
                "total_corrections": 89,
                "corrections_by_type": {
                    "modify": 45,
                    "confirm": 30,
                    "reject": 14
                },
                "documents_requiring_review": 12,
                "overdue_reviews": 3
            }
        }
