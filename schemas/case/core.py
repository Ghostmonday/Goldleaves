# schemas/case/core.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from ..base.responses import PaginatedResponse
from ..client.core import ClientSummary


class CaseType(str, Enum):
    """Case type enumeration."""
    CONSULTATION = "consultation"
    LITIGATION = "litigation"
    TRANSACTION = "transaction"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    DISPUTE = "dispute"
    CONTRACT = "contract"
    IMMIGRATION = "immigration"
    FAMILY = "family"
    CRIMINAL = "criminal"
    CORPORATE = "corporate"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    REAL_ESTATE = "real_estate"
    EMPLOYMENT = "employment"
    BANKRUPTCY = "bankruptcy"
    TAX = "tax"
    PERSONAL_INJURY = "personal_injury"
    OTHER = "other"


class CaseStatus(str, Enum):
    """Case status enumeration."""
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    PENDING_REVIEW = "pending_review"
    SETTLED = "settled"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CLOSED_DISMISSED = "closed_dismissed"
    CLOSED_WITHDRAWN = "closed_withdrawn"
    ARCHIVED = "archived"


class CasePriority(str, Enum):
    """Case priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class CaseStage(str, Enum):
    """Case stage enumeration."""
    INTAKE = "intake"
    INVESTIGATION = "investigation"
    DISCOVERY = "discovery"
    NEGOTIATION = "negotiation"
    MEDIATION = "mediation"
    LITIGATION = "litigation"
    TRIAL = "trial"
    APPEAL = "appeal"
    SETTLEMENT = "settlement"
    CLOSING = "closing"
    COMPLETED = "completed"


class BillingType(str, Enum):
    """Billing type enumeration."""
    HOURLY = "hourly"
    FLAT_FEE = "flat_fee"
    CONTINGENCY = "contingency"
    RETAINER = "retainer"
    HYBRID = "hybrid"
    PRO_BONO = "pro_bono"


class CaseBase(BaseModel):
    """Base case schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255, description="Case title")
    description: Optional[str] = Field(None, description="Case description")
    case_type: CaseType = Field(..., description="Type of case")
    status: CaseStatus = Field(CaseStatus.DRAFT, description="Case status")
    priority: CasePriority = Field(CasePriority.MEDIUM, description="Priority level")
    stage: CaseStage = Field(CaseStage.INTAKE, description="Current stage")

    # Dates
    deadline_date: Optional[datetime] = Field(None, description="Case deadline")
    statute_of_limitations: Optional[datetime] = Field(None, description="Statute of limitations")
    next_court_date: Optional[datetime] = Field(None, description="Next court date")

    # Court information
    court_name: Optional[str] = Field(None, max_length=200, description="Court name")
    judge_name: Optional[str] = Field(None, max_length=200, description="Judge name")
    jurisdiction: Optional[str] = Field(None, max_length=200, description="Jurisdiction")
    case_number_court: Optional[str] = Field(None, max_length=100, description="Court case number")
    opposing_party: Optional[str] = Field(None, max_length=255, description="Opposing party")
    opposing_counsel: Optional[str] = Field(None, max_length=255, description="Opposing counsel")

    # Financial information
    billing_type: BillingType = Field(BillingType.HOURLY, description="Billing type")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="Hourly rate")
    flat_fee_amount: Optional[Decimal] = Field(None, ge=0, description="Flat fee amount")
    contingency_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Contingency percentage")
    retainer_amount: Optional[Decimal] = Field(None, ge=0, description="Retainer amount")
    estimated_value: Optional[Decimal] = Field(None, description="Estimated case value")
    estimated_hours: Optional[Decimal] = Field(None, ge=0, description="Estimated hours")

    # Metadata
    notes: Optional[str] = Field(None, description="Case notes")
    external_case_id: Optional[str] = Field(None, max_length=100, description="External case ID")
    matter_number: Optional[str] = Field(None, max_length=100, description="Matter number")
    practice_area: Optional[str] = Field(None, max_length=100, description="Practice area")
    is_confidential: bool = Field(True, description="Is case confidential")


class CaseCreate(CaseBase):
    """Schema for creating a new case."""
    client_id: int = Field(..., description="Client ID")
    assigned_to_id: Optional[int] = Field(None, description="Assigned attorney ID")
    supervising_attorney_id: Optional[int] = Field(None, description="Supervising attorney ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="Case tags")

    class Config:
        schema_extra = {
            "example": {
                "title": "Contract Dispute - Smith vs. ABC Corp",
                "description": "Contract dispute regarding breach of service agreement",
                "case_type": "litigation",
                "status": "open",
                "priority": "high",
                "stage": "investigation",
                "client_id": 1,
                "billing_type": "hourly",
                "hourly_rate": 350.00,
                "estimated_hours": 40.0,
                "deadline_date": "2025-12-31T23:59:59Z",
                "practice_area": "Commercial Litigation",
                "tags": ["contract", "commercial", "urgent"]
            }
        }


class CaseUpdate(BaseModel):
    """Schema for updating a case."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_type: Optional[CaseType] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    stage: Optional[CaseStage] = None
    deadline_date: Optional[datetime] = None
    statute_of_limitations: Optional[datetime] = None
    next_court_date: Optional[datetime] = None
    court_name: Optional[str] = Field(None, max_length=200)
    judge_name: Optional[str] = Field(None, max_length=200)
    jurisdiction: Optional[str] = Field(None, max_length=200)
    case_number_court: Optional[str] = Field(None, max_length=100)
    opposing_party: Optional[str] = Field(None, max_length=255)
    opposing_counsel: Optional[str] = Field(None, max_length=255)
    billing_type: Optional[BillingType] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    flat_fee_amount: Optional[Decimal] = Field(None, ge=0)
    contingency_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    retainer_amount: Optional[Decimal] = Field(None, ge=0)
    estimated_value: Optional[Decimal] = None
    actual_settlement: Optional[Decimal] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    outcome_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    external_case_id: Optional[str] = Field(None, max_length=100)
    matter_number: Optional[str] = Field(None, max_length=100)
    practice_area: Optional[str] = Field(None, max_length=100)
    is_confidential: Optional[bool] = None
    assigned_to_id: Optional[int] = None
    supervising_attorney_id: Optional[int] = None
    tags: Optional[List[str]] = None


class CaseResponse(CaseBase):
    """Schema for case response."""
    id: int
    case_number: str
    slug: str
    client_id: int
    organization_id: int
    created_by_id: Optional[int]
    assigned_to_id: Optional[int]
    supervising_attorney_id: Optional[int]
    opened_date: datetime
    closed_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Financial computed fields
    actual_hours: Decimal = Field(default=Decimal('0.00'))
    billable_hours: Decimal = Field(default=Decimal('0.00'))
    actual_settlement: Optional[Decimal] = None
    billable_amount: Optional[Decimal] = Field(None, description="Calculated billable amount")

    # Additional fields
    tags: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    outcome_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    share_slug: Optional[str] = None
    share_expires_at: Optional[datetime] = None

    # Computed fields
    is_overdue: Optional[bool] = False
    days_until_deadline: Optional[int] = None
    is_share_valid: Optional[bool] = False
    document_count: Optional[int] = 0
    task_count: Optional[int] = 0
    event_count: Optional[int] = 0

    # Related data
    client: Optional[ClientSummary] = None

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "case_number": "CASE-2025-000001",
                "slug": "contract-dispute-smith-vs-abc-corp",
                "title": "Contract Dispute - Smith vs. ABC Corp",
                "case_type": "litigation",
                "status": "in_progress",
                "priority": "high",
                "stage": "discovery",
                "billing_type": "hourly",
                "hourly_rate": 350.00,
                "actual_hours": 25.5,
                "billable_hours": 24.0,
                "billable_amount": 8400.00,
                "client_id": 1,
                "organization_id": 1,
                "opened_date": "2025-08-01T09:00:00Z",
                "deadline_date": "2025-12-31T23:59:59Z",
                "is_overdue": False,
                "days_until_deadline": 151,
                "document_count": 15,
                "task_count": 8,
                "event_count": 3
            }
        }


class CaseSummary(BaseModel):
    """Simplified case schema for lists and references."""
    id: int
    case_number: str
    slug: str
    title: str
    case_type: CaseType
    status: CaseStatus
    priority: CasePriority
    stage: CaseStage
    client_id: int
    billable_amount: Optional[Decimal] = None
    deadline_date: Optional[datetime] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True


class CaseListResponse(PaginatedResponse):
    """Paginated list of cases."""
    items: List[CaseResponse]

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "case_number": "CASE-2025-000001",
                        "title": "Contract Dispute - Smith vs. ABC Corp",
                        "case_type": "litigation",
                        "status": "in_progress",
                        "priority": "high",
                        "client_id": 1,
                        "billable_amount": 8400.00
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
        }


class CaseFilter(BaseModel):
    """Case filtering parameters."""
    search: Optional[str] = Field(None, description="Search in title, description, case number")
    case_type: Optional[CaseType] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    stage: Optional[CaseStage] = None
    client_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    supervising_attorney_id: Optional[int] = None
    practice_area: Optional[str] = None
    billing_type: Optional[BillingType] = None
    tags: Optional[List[str]] = None
    opened_after: Optional[datetime] = None
    opened_before: Optional[datetime] = None
    deadline_after: Optional[datetime] = None
    deadline_before: Optional[datetime] = None
    overdue_only: Optional[bool] = False

    class Config:
        schema_extra = {
            "example": {
                "search": "contract",
                "case_type": "litigation",
                "status": "in_progress",
                "priority": "high",
                "client_id": 1,
                "practice_area": "Commercial Litigation",
                "overdue_only": False
            }
        }


class CaseStats(BaseModel):
    """Case statistics schema."""
    total_cases: int = 0
    open_cases: int = 0
    closed_cases: int = 0
    overdue_cases: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_stage: Dict[str, int] = Field(default_factory=dict)
    total_billable_amount: Decimal = Field(default=Decimal('0.00'))
    average_case_value: Decimal = Field(default=Decimal('0.00'))
    recent_cases: int = 0  # Last 30 days

    class Config:
        schema_extra = {
            "example": {
                "total_cases": 125,
                "open_cases": 85,
                "closed_cases": 40,
                "overdue_cases": 5,
                "by_type": {
                    "litigation": 45,
                    "contract": 30,
                    "consultation": 25,
                    "other": 25
                },
                "by_status": {
                    "in_progress": 50,
                    "open": 35,
                    "closed_won": 20,
                    "closed_lost": 15,
                    "on_hold": 5
                },
                "total_billable_amount": 2500000.00,
                "average_case_value": 20000.00,
                "recent_cases": 8
            }
        }


class CaseCloseRequest(BaseModel):
    """Schema for closing a case."""
    status: CaseStatus = Field(..., description="Closing status")
    outcome_summary: Optional[str] = Field(None, description="Summary of case outcome")
    actual_settlement: Optional[Decimal] = Field(None, ge=0, description="Final settlement amount")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned from case")

    @validator('status')
    def validate_closing_status(cls, v):
        """Ensure status is a valid closing status."""
        valid_closing_statuses = [
            CaseStatus.CLOSED_WON, CaseStatus.CLOSED_LOST,
            CaseStatus.CLOSED_DISMISSED, CaseStatus.CLOSED_WITHDRAWN,
            CaseStatus.SETTLED, CaseStatus.ARCHIVED
        ]
        if v not in valid_closing_statuses:
            raise ValueError(f"Status must be one of: {[s.value for s in valid_closing_statuses]}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "status": "closed_won",
                "outcome_summary": "Successfully negotiated favorable settlement for client",
                "actual_settlement": 150000.00,
                "lessons_learned": "Early mediation was key to successful resolution"
            }
        }


class CaseShareRequest(BaseModel):
    """Schema for creating a case share link."""
    expires_in_days: Optional[int] = Field(30, ge=1, le=365, description="Days until link expires")

    class Config:
        schema_extra = {
            "example": {
                "expires_in_days": 30
            }
        }


class CaseShareResponse(BaseModel):
    """Schema for case share link response."""
    share_slug: str
    share_url: str
    expires_at: datetime
    is_valid: bool = True

    class Config:
        schema_extra = {
            "example": {
                "share_slug": "case-abc123def456ghi789",
                "share_url": "https://app.goldleaves.com/shared/cases/case-abc123def456ghi789",
                "expires_at": "2025-09-01T23:59:59Z",
                "is_valid": True
            }
        }


class CaseBulkAction(BaseModel):
    """Case bulk action schema."""
    case_ids: List[int] = Field(..., description="List of case IDs to update")
    action: str = Field(..., description="Action to perform: update_status, update_priority, assign_to, add_tags, remove_tags")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")

    class Config:
        schema_extra = {
            "example": {
                "case_ids": [1, 2, 3],
                "action": "update_status",
                "parameters": {"status": "active"}
            }
        }


class CaseBulkResult(BaseModel):
    """Case bulk action result schema."""
    success_count: int = Field(default=0, description="Number of successfully updated cases")
    error_count: int = Field(default=0, description="Number of cases that failed to update")
    updated_cases: List[int] = Field(default_factory=list, description="List of successfully updated case IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")

    class Config:
        schema_extra = {
            "example": {
                "success_count": 2,
                "error_count": 1,
                "updated_cases": [1, 2],
                "errors": [{"case_id": 3, "error": "Case not found"}]
            }
        }
