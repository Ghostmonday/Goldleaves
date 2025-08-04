"""
Audit log schemas for compliance-grade event tracking.
Provides schemas for audit entries, filtering, and reporting.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    create_field_metadata,
    validate_non_empty_string,
    Status
)


class AuditAction(str, Enum):
    """Comprehensive audit action types for compliance tracking."""
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_SUSPEND = "user.suspend"
    USER_REACTIVATE = "user.reactivate"
    USER_PROMOTE = "user.promote"
    USER_DEMOTE = "user.demote"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_MFA_ENABLE = "user.mfa_enable"
    USER_MFA_DISABLE = "user.mfa_disable"
    
    # Organization actions
    ORG_CREATE = "org.create"
    ORG_UPDATE = "org.update"
    ORG_DELETE = "org.delete"
    ORG_TRANSFER = "org.transfer"
    ORG_BILLING_UPDATE = "org.billing_update"
    
    # Team actions
    TEAM_CREATE = "team.create"
    TEAM_UPDATE = "team.update"
    TEAM_DELETE = "team.delete"
    TEAM_MEMBER_ADD = "team.member_add"
    TEAM_MEMBER_REMOVE = "team.member_remove"
    
    # Document actions
    DOC_CREATE = "doc.create"
    DOC_READ = "doc.read"
    DOC_UPDATE = "doc.update"
    DOC_DELETE = "doc.delete"
    DOC_SHARE = "doc.share"
    DOC_UNSHARE = "doc.unshare"
    DOC_DOWNLOAD = "doc.download"
    DOC_VERSION_CREATE = "doc.version_create"
    DOC_VERSION_RESTORE = "doc.version_restore"
    
    # Permission actions
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_UNASSIGN = "role.unassign"
    
    # Security actions
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"
    SECURITY_ACCESS_DENIED = "security.access_denied"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_API_KEY_CREATE = "security.api_key_create"
    SECURITY_API_KEY_REVOKE = "security.api_key_revoke"
    
    # Admin actions
    ADMIN_CONFIG_UPDATE = "admin.config_update"
    ADMIN_MAINTENANCE_START = "admin.maintenance_start"
    ADMIN_MAINTENANCE_END = "admin.maintenance_end"
    ADMIN_BACKUP_CREATE = "admin.backup_create"
    ADMIN_BACKUP_RESTORE = "admin.backup_restore"
    
    # Data actions
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_ANONYMIZE = "data.anonymize"
    DATA_RETENTION_APPLY = "data.retention_apply"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(str, Enum):
    """Audit event categories for filtering."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    USER_MANAGEMENT = "user_management"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    SECURITY = "security"
    ADMIN = "admin"
    DATA = "data"
    SYSTEM = "system"


class ActorType(str, Enum):
    """Types of actors that can perform actions."""
    USER = "user"
    SYSTEM = "system"
    API = "api"
    ADMIN = "admin"
    SERVICE = "service"


class UserActor(BaseModel):
    """Actor information for audit entries."""
    
    actor_id: UUID = Field(
        description="Unique identifier of the actor"
    )
    
    actor_type: ActorType = Field(
        description="Type of actor performing the action"
    )
    
    actor_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable name of the actor"
    )
    
    actor_email: Optional[str] = Field(
        default=None,
        description="Email address of the actor (if user)"
    )
    
    ip_address: Optional[str] = Field(
        default=None,
        description="IP address of the request"
    )
    
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier"
    )


class AuditTarget(BaseModel):
    """Target resource information for audit entries."""
    
    target_id: UUID = Field(
        description="Unique identifier of the target resource"
    )
    
    target_type: str = Field(
        max_length=50,
        description="Type of target resource (user, document, etc.)"
    )
    
    target_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable name of the target"
    )
    
    target_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional details about the target"
    )


class AuditContext(BaseModel):
    """Context information for audit entries."""
    
    organization_id: Optional[UUID] = Field(
        default=None,
        description="Organization context"
    )
    
    team_id: Optional[UUID] = Field(
        default=None,
        description="Team context"
    )
    
    project_id: Optional[UUID] = Field(
        default=None,
        description="Project context"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request tracking ID"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Correlation ID for related events"
    )
    
    environment: Optional[str] = Field(
        default=None,
        description="Environment (production, staging, etc.)"
    )


class AuditLogEntry(BaseModel):
    """Complete audit log entry."""
    
    id: UUID = Field(
        description="Unique audit log entry ID"
    )
    
    action: AuditAction = Field(
        description="Action that was performed"
    )
    
    category: AuditCategory = Field(
        description="Category of the action"
    )
    
    severity: AuditSeverity = Field(
        default=AuditSeverity.INFO,
        description="Severity level of the event"
    )
    
    actor: UserActor = Field(
        description="Who performed the action"
    )
    
    target: Optional[AuditTarget] = Field(
        default=None,
        description="What was acted upon"
    )
    
    context: AuditContext = Field(
        description="Context of the action"
    )
    
    timestamp: datetime = Field(
        description="When the action occurred"
    )
    
    success: bool = Field(
        default=True,
        description="Whether the action succeeded"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if action failed"
    )
    
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        **create_field_metadata(
            title="Changes",
            description="Before/after values for update actions",
            example={"status": {"before": "active", "after": "suspended"}}
        )
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    retention_date: Optional[datetime] = Field(
        default=None,
        description="Date when this log can be deleted"
    )


class LogEntryCreate(BaseModel):
    """Schema for creating audit log entries."""
    
    action: AuditAction = Field(
        description="Action being performed"
    )
    
    actor_id: UUID = Field(
        description="ID of the actor"
    )
    
    actor_type: ActorType = Field(
        default=ActorType.USER,
        description="Type of actor"
    )
    
    target_id: Optional[UUID] = Field(
        default=None,
        description="ID of the target resource"
    )
    
    target_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Type of target resource"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        description="Organization context"
    )
    
    success: bool = Field(
        default=True,
        description="Whether the action succeeded"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message if failed"
    )
    
    changes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Changes made"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    ip_address: Optional[str] = Field(
        default=None,
        description="Client IP address"
    )
    
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )


class AuditFilter(BaseModel):
    """Filter criteria for querying audit logs."""
    
    actions: Optional[List[AuditAction]] = Field(
        default=None,
        description="Filter by specific actions"
    )
    
    categories: Optional[List[AuditCategory]] = Field(
        default=None,
        description="Filter by categories"
    )
    
    severity_levels: Optional[List[AuditSeverity]] = Field(
        default=None,
        description="Filter by severity levels"
    )
    
    actor_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter by actor IDs"
    )
    
    actor_types: Optional[List[ActorType]] = Field(
        default=None,
        description="Filter by actor types"
    )
    
    target_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter by target IDs"
    )
    
    target_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by target types"
    )
    
    organization_id: Optional[UUID] = Field(
        default=None,
        description="Filter by organization"
    )
    
    team_id: Optional[UUID] = Field(
        default=None,
        description="Filter by team"
    )
    
    success: Optional[bool] = Field(
        default=None,
        description="Filter by success/failure"
    )
    
    start_time: Optional[datetime] = Field(
        default=None,
        description="Filter events after this time"
    )
    
    end_time: Optional[datetime] = Field(
        default=None,
        description="Filter events before this time"
    )
    
    search_query: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Search in action descriptions and metadata"
    )
    
    ip_address: Optional[str] = Field(
        default=None,
        description="Filter by IP address"
    )
    
    correlation_id: Optional[str] = Field(
        default=None,
        description="Filter by correlation ID"
    )
    
    @validator('start_time', 'end_time')
    def validate_times(cls, v, values):
        """Ensure end_time is after start_time."""
        if 'start_time' in values and v and values['start_time']:
            if v < values['start_time']:
                raise ValueError("end_time must be after start_time")
        return v


class AuditSummary(BaseModel):
    """Summary statistics for audit logs."""
    
    total_events: int = Field(
        ge=0,
        description="Total number of events"
    )
    
    successful_events: int = Field(
        ge=0,
        description="Number of successful events"
    )
    
    failed_events: int = Field(
        ge=0,
        description="Number of failed events"
    )
    
    events_by_action: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of events by action type"
    )
    
    events_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of events by category"
    )
    
    events_by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of events by severity"
    )
    
    events_by_actor: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of events by actor"
    )
    
    time_range: Dict[str, Optional[datetime]] = Field(
        default_factory=dict,
        description="Time range of events (start, end)"
    )
    
    most_active_users: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most active users in the period"
    )
    
    suspicious_activities: int = Field(
        default=0,
        ge=0,
        description="Count of suspicious activities"
    )


class AuditExportRequest(BaseModel):
    """Request to export audit logs."""
    
    filter: AuditFilter = Field(
        description="Filter criteria for export"
    )
    
    format: str = Field(
        default="json",
        pattern="^(json|csv|pdf)$",
        description="Export format"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in export"
    )
    
    redact_sensitive: bool = Field(
        default=True,
        description="Redact sensitive information"
    )
    
    max_records: Optional[int] = Field(
        default=10000,
        ge=1,
        le=100000,
        description="Maximum records to export"
    )


class AuditRetentionPolicy(BaseModel):
    """Audit log retention policy."""
    
    default_retention_days: int = Field(
        default=2555,  # 7 years
        ge=30,
        description="Default retention period in days"
    )
    
    retention_by_category: Dict[AuditCategory, int] = Field(
        default_factory=dict,
        description="Category-specific retention periods"
    )
    
    retention_by_severity: Dict[AuditSeverity, int] = Field(
        default_factory=dict,
        description="Severity-specific retention periods"
    )
    
    permanent_actions: List[AuditAction] = Field(
        default_factory=list,
        description="Actions to retain permanently"
    )
    
    auto_delete: bool = Field(
        default=False,
        description="Automatically delete expired logs"
    )


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    
    report_id: UUID = Field(
        description="Unique report identifier"
    )
    
    period_start: datetime = Field(
        description="Report period start"
    )
    
    period_end: datetime = Field(
        description="Report period end"
    )
    
    organization_id: UUID = Field(
        description="Organization being reported on"
    )
    
    summary: AuditSummary = Field(
        description="Summary statistics"
    )
    
    compliance_violations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of compliance violations"
    )
    
    security_incidents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Security incidents in period"
    )
    
    privileged_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Privileged actions performed"
    )
    
    data_access_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of data access patterns"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Compliance recommendations"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When report was generated"
    )
    
    generated_by: UUID = Field(
        description="User who generated the report"
    )
