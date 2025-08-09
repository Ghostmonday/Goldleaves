# models/case.py

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

# Import from local dependencies
from .dependencies import Base, utcnow
from .user import SoftDeleteMixin, TimestampMixin


class CaseType(PyEnum):
    """Enum for case types."""
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


class CaseStatus(PyEnum):
    """Enum for case status."""
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


class CasePriority(PyEnum):
    """Enum for case priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class CaseStage(PyEnum):
    """Enum for case stages."""
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


class BillingType(PyEnum):
    """Enum for billing types."""
    HOURLY = "hourly"
    FLAT_FEE = "flat_fee"
    CONTINGENCY = "contingency"
    RETAINER = "retainer"
    HYBRID = "hybrid"
    PRO_BONO = "pro_bono"


class Case(Base, TimestampMixin, SoftDeleteMixin):
    """Enhanced Case model with comprehensive legal case management."""
    __tablename__ = "cases"

    # Core fields
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, nullable=False, index=True)  # Auto-generated or manual
    slug = Column(String(150), unique=True, nullable=False, index=True)  # URL-friendly identifier
    
    # Case identification
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    case_type = Column(Enum(CaseType), nullable=False, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.DRAFT, nullable=False, index=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    stage = Column(Enum(CaseStage), default=CaseStage.INTAKE, nullable=False)
    
    # Dates and timeline
    opened_date = Column(DateTime, default=utcnow, nullable=False)
    closed_date = Column(DateTime, nullable=True)
    deadline_date = Column(DateTime, nullable=True)
    statute_of_limitations = Column(DateTime, nullable=True)
    next_court_date = Column(DateTime, nullable=True)
    
    # Court and jurisdiction information
    court_name = Column(String(200), nullable=True)
    judge_name = Column(String(200), nullable=True)
    jurisdiction = Column(String(200), nullable=True)
    case_number_court = Column(String(100), nullable=True)  # Court-assigned case number
    opposing_party = Column(String(255), nullable=True)
    opposing_counsel = Column(String(255), nullable=True)
    
    # Financial information
    billing_type = Column(Enum(BillingType), default=BillingType.HOURLY, nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    flat_fee_amount = Column(Numeric(10, 2), nullable=True)
    contingency_percentage = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    retainer_amount = Column(Numeric(10, 2), nullable=True)
    estimated_value = Column(Numeric(12, 2), nullable=True)
    actual_settlement = Column(Numeric(12, 2), nullable=True)
    
    # Time tracking
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), default=0, nullable=False)
    billable_hours = Column(Numeric(8, 2), default=0, nullable=False)
    
    # Case metadata
    tags = Column(JSON, nullable=True)  # Array of string tags
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Private notes for staff
    outcome_summary = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    
    # External references
    external_case_id = Column(String(100), nullable=True, index=True)
    matter_number = Column(String(100), nullable=True, index=True)  # Client's internal reference
    practice_area = Column(String(100), nullable=True, index=True)
    
    # Sharing and collaboration
    is_confidential = Column(Boolean, default=True, nullable=False)
    share_slug = Column(String(200), nullable=True, unique=True, index=True)  # For secure sharing
    share_expires_at = Column(DateTime, nullable=True)
    
    # Multi-tenant isolation
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Primary attorney
    supervising_attorney_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="cases")
    organization = relationship("Organization")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    supervising_attorney = relationship("User", foreign_keys=[supervising_attorney_id])
    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="case", cascade="all, delete-orphan")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan")
    tasks = relationship("CaseTask", back_populates="case", cascade="all, delete-orphan")
    
    # Document relationships - NEW (using the new Document model)
    prediction_documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    
    # Composite indexes for performance and multi-tenant isolation
    __table_args__ = (
        Index('idx_case_org_status', 'organization_id', 'status'),
        Index('idx_case_org_client', 'organization_id', 'client_id'),
        Index('idx_case_org_type', 'organization_id', 'case_type'),
        Index('idx_case_org_priority', 'organization_id', 'priority'),
        Index('idx_case_org_assigned', 'organization_id', 'assigned_to_id'),
        Index('idx_case_org_stage', 'organization_id', 'stage'),
        Index('idx_case_number_org', 'case_number', 'organization_id'),
        Index('idx_case_deadline', 'deadline_date', 'organization_id'),
        Index('idx_case_court_date', 'next_court_date', 'organization_id'),
        Index('idx_case_opened_date', 'opened_date', 'organization_id'),
        Index('idx_case_share_slug', 'share_slug'),  # For public sharing
    )

    def __repr__(self):
        return f"<Case(id={self.id}, number='{self.case_number}', title='{self.title[:50]}', status={self.status.value})>"

    def generate_case_number(self, prefix: str = "CASE") -> str:
        """Generate a case number if not provided."""
        year = datetime.now().year
        return f"{prefix}-{year}-{self.id:06d}"

    def add_tag(self, tag: str):
        """Add a tag to the case."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the case."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if case has a specific tag."""
        return self.tags is not None and tag in self.tags

    def close_case(self, status: CaseStatus, outcome_summary: str = None):
        """Close the case with a specific status."""
        if status in [CaseStatus.CLOSED_WON, CaseStatus.CLOSED_LOST, 
                      CaseStatus.CLOSED_DISMISSED, CaseStatus.CLOSED_WITHDRAWN]:
            self.status = status
            self.closed_date = utcnow()
            self.stage = CaseStage.COMPLETED
            if outcome_summary:
                self.outcome_summary = outcome_summary

    def reopen_case(self):
        """Reopen a closed case."""
        self.status = CaseStatus.OPEN
        self.closed_date = None
        self.stage = CaseStage.INVESTIGATION

    def set_priority(self, priority: CasePriority):
        """Set case priority."""
        self.priority = priority

    def advance_stage(self, new_stage: CaseStage):
        """Advance case to a new stage."""
        self.stage = new_stage

    def calculate_total_hours(self) -> Decimal:
        """Calculate total hours from time entries."""
        if self.time_entries:
            return sum(entry.hours for entry in self.time_entries if entry.hours)
        return Decimal('0.00')

    def calculate_billable_amount(self) -> Decimal:
        """Calculate total billable amount."""
        if self.billing_type == BillingType.HOURLY and self.hourly_rate:
            return self.billable_hours * self.hourly_rate
        elif self.billing_type == BillingType.FLAT_FEE and self.flat_fee_amount:
            return self.flat_fee_amount
        elif self.billing_type == BillingType.CONTINGENCY and self.contingency_percentage and self.actual_settlement:
            return self.actual_settlement * (self.contingency_percentage / 100)
        return Decimal('0.00')

    def is_overdue(self) -> bool:
        """Check if case has passed its deadline."""
        return self.deadline_date and datetime.utcnow() > self.deadline_date

    def days_until_deadline(self) -> int:
        """Calculate days until deadline."""
        if self.deadline_date:
            delta = self.deadline_date - datetime.utcnow()
            return delta.days
        return None

    def generate_share_slug(self) -> str:
        """Generate a secure slug for case sharing."""
        import secrets
        self.share_slug = f"case-{secrets.token_urlsafe(32)}"
        return self.share_slug

    def is_share_valid(self) -> bool:
        """Check if the share link is still valid."""
        if not self.share_slug:
            return False
        if self.share_expires_at and datetime.utcnow() > self.share_expires_at:
            return False
        return True


class CaseDocument(Base, TimestampMixin, SoftDeleteMixin):
    """Documents associated with cases."""
    __tablename__ = "case_documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    document_type = Column(String(100), nullable=True)  # pleading, evidence, contract, etc.
    version = Column(Integer, default=1, nullable=False)
    
    # Multi-tenant isolation
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="documents")
    organization = relationship("Organization")
    uploaded_by = relationship("User")
    
    __table_args__ = (
        Index('idx_case_doc_org', 'case_id', 'organization_id'),
        Index('idx_case_doc_type', 'case_id', 'document_type'),
    )

    def __repr__(self):
        return f"<CaseDocument(id={self.id}, name='{self.name}', case_id={self.case_id})>"


class TimeEntry(Base, TimestampMixin, SoftDeleteMixin):
    """Time tracking entries for cases."""
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=utcnow, nullable=False, index=True)
    hours = Column(Numeric(6, 2), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(100), nullable=True)  # research, writing, meeting, etc.
    billable = Column(Boolean, default=True, nullable=False)
    
    # Multi-tenant isolation
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    case = relationship("Case", back_populates="time_entries")
    organization = relationship("Organization")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_time_case_org', 'case_id', 'organization_id'),
        Index('idx_time_user_date', 'user_id', 'date'),
        Index('idx_time_billable', 'billable', 'organization_id'),
    )

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, case_id={self.case_id}, hours={self.hours}, date={self.date})>"


class CaseEvent(Base, TimestampMixin, SoftDeleteMixin):
    """Events and milestones for cases."""
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(100), nullable=True)  # hearing, filing, meeting, etc.
    location = Column(String(255), nullable=True)
    is_milestone = Column(Boolean, default=False, nullable=False)
    
    # Multi-tenant isolation
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="events")
    organization = relationship("Organization")
    created_by = relationship("User")
    
    __table_args__ = (
        Index('idx_event_case_org', 'case_id', 'organization_id'),
        Index('idx_event_date_org', 'event_date', 'organization_id'),
        Index('idx_event_type_org', 'event_type', 'organization_id'),
    )

    def __repr__(self):
        return f"<CaseEvent(id={self.id}, title='{self.title}', case_id={self.case_id}, date={self.event_date})>"


class CaseTask(Base, TimestampMixin, SoftDeleteMixin):
    """Tasks and to-dos for cases."""
    __tablename__ = "case_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    
    # Multi-tenant isolation
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="tasks")
    organization = relationship("Organization")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    __table_args__ = (
        Index('idx_task_case_org', 'case_id', 'organization_id'),
        Index('idx_task_assigned_org', 'assigned_to_id', 'organization_id'),
        Index('idx_task_due_date', 'due_date', 'organization_id'),
        Index('idx_task_completed', 'completed', 'organization_id'),
    )

    def __repr__(self):
        return f"<CaseTask(id={self.id}, title='{self.title}', case_id={self.case_id}, completed={self.completed})>"

    def complete_task(self):
        """Mark task as completed."""
        self.completed = True
        self.completed_at = utcnow()

    def reopen_task(self):
        """Reopen a completed task."""
        self.completed = False
        self.completed_at = None
