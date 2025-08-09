# models/document.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import secrets
import string

from models.user import Base, TimestampMixin, SoftDeleteMixin


class PredictionStatus(enum.Enum):
    """Document prediction status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PARTIALLY_CONFIRMED = "partially_confirmed"


class DocumentType(enum.Enum):
    """Document type enumeration."""
    CONTRACT = "contract"
    LEGAL_BRIEF = "legal_brief"
    COURT_FILING = "court_filing"
    CORRESPONDENCE = "correspondence"
    EVIDENCE = "evidence"
    MEMO = "memo"
    INVOICE = "invoice"
    AGREEMENT = "agreement"
    MOTION = "motion"
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class DocumentStatus(enum.Enum):
    """Document processing status enumeration."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    FINAL = "final"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class DocumentConfidentiality(enum.Enum):
    """Document confidentiality level enumeration."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    ATTORNEY_CLIENT_PRIVILEGED = "attorney_client_privileged"
    ATTORNEY_WORK_PRODUCT = "attorney_work_product"


class Document(Base, TimestampMixin, SoftDeleteMixin):
    """
    Document model with AI prediction support and audit trail.
    
    This model supports:
    - Document metadata and content management
    - AI prediction ingestion with confidence scoring
    - Human-in-the-loop correction tracking
    - Comprehensive audit trail for compliance
    - Multi-tenant organization isolation
    - Integration with cases and clients
    """
    
    __tablename__ = "documents"
    
    # Basic document information
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT, index=True)
    confidentiality = Column(SQLEnum(DocumentConfidentiality), default=DocumentConfidentiality.INTERNAL)
    
    # File information
    file_name = Column(String(255))
    file_path = Column(String(1000))
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    file_hash = Column(String(64))  # SHA-256 hash for integrity
    
    # Content and extracted data
    content = Column(Text)  # Extracted text content
    document_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    
    # AI Prediction fields
    prediction_status = Column(SQLEnum(PredictionStatus), default=PredictionStatus.PENDING, index=True)
    prediction_score = Column(Float, nullable=True)  # Confidence score 0.0-1.0
    ai_predictions = Column(JSON, default=dict)  # Original AI predictions
    corrections = Column(JSON, default=dict)  # Field-level corrections and diffs
    
    # Version control and audit
    version = Column(Integer, default=1, nullable=False)
    edited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    edited_at = Column(DateTime, nullable=True)
    
    # Relationships
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tags and categorization
    tags = Column(JSON, default=list)  # List of tag strings
    
    # Compliance and legal holds
    legal_hold = Column(Boolean, default=False)
    retention_date = Column(DateTime, nullable=True)
    
    # Relations
    case = relationship("Case", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    organization = relationship("Organization", back_populates="documents")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_documents")
    edited_by = relationship("User", foreign_keys=[edited_by_id], back_populates="edited_documents")
    
    # Document versions and audit trail
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    corrections_history = relationship("DocumentCorrection", back_populates="document", cascade="all, delete-orphan")
    shares = relationship("DocumentShare", back_populates="document", cascade="all, delete-orphan")
    
    # Phase 6: Enhanced audit and collaboration
    audit_events = relationship("DocumentAuditEvent", back_populates="document", cascade="all, delete-orphan")
    secure_shares = relationship("DocumentSecureShare", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', type={self.document_type.value})>"
    
    def add_tag(self, tag: str):
        """Add a tag to the document."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the document."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def get_confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.prediction_score is None:
            return "unknown"
        elif self.prediction_score >= 0.9:
            return "high"
        elif self.prediction_score >= 0.7:
            return "medium"
        elif self.prediction_score >= 0.5:
            return "low"
        else:
            return "very_low"
    
    def has_pending_corrections(self) -> bool:
        """Check if document has pending corrections."""
        return self.prediction_status == PredictionStatus.PENDING
    
    def get_correction_count(self) -> int:
        """Get number of corrections made to this document."""
        return len(self.corrections_history) if self.corrections_history else 0
    
    def increment_version(self, edited_by_id: int):
        """Increment document version and update edit metadata."""
        self.version += 1
        self.edited_by_id = edited_by_id
        self.edited_at = datetime.utcnow()


class DocumentVersion(Base, TimestampMixin):
    """
    Document version history for audit trail.
    """
    
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    
    # Snapshot of document state
    title = Column(String(500))
    content = Column(Text)
    version_metadata = Column(JSON, default=dict)
    ai_predictions = Column(JSON, default=dict)
    corrections = Column(JSON, default=dict)
    prediction_status = Column(SQLEnum(PredictionStatus))
    prediction_score = Column(Float)
    
    # Version metadata
    change_summary = Column(Text)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_reason = Column(String(500))
    
    # Relations
    document = relationship("Document", back_populates="versions")
    changed_by = relationship("User")
    
    def __repr__(self):
        return f"<DocumentVersion(document_id={self.document_id}, version={self.version_number})>"


class DocumentCorrection(Base, TimestampMixin):
    """
    Document correction tracking for human-in-the-loop validation.
    """
    
    __tablename__ = "document_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Correction details
    field_path = Column(String(255), nullable=False)  # JSON path to corrected field
    original_value = Column(JSON)  # Original AI prediction
    corrected_value = Column(JSON)  # Human-corrected value
    confidence_before = Column(Float)  # AI confidence before correction
    confidence_after = Column(Float, default=1.0)  # Human confidence (default high)
    
    # Correction metadata
    correction_reason = Column(Text)
    correction_type = Column(String(50))  # 'confirm', 'reject', 'modify'
    corrected_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Review and approval
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_status = Column(String(50), default="pending")  # pending, approved, rejected
    
    # Relations
    document = relationship("Document", back_populates="corrections_history")
    corrected_by = relationship("User", foreign_keys=[corrected_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f"<DocumentCorrection(document_id={self.document_id}, field='{self.field_path}')>"


class DocumentShare(Base, TimestampMixin):
    """
    Document sharing and access control.
    """
    
    __tablename__ = "document_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Sharing configuration
    share_token = Column(String(100), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)
    
    # Access control
    allowed_downloads = Column(Integer, default=1)
    download_count = Column(Integer, default=0)
    requires_auth = Column(Boolean, default=True)
    
    # Sharing metadata
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_email = Column(String(255), nullable=True)
    share_reason = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    document = relationship("Document")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])
    
    def is_expired(self) -> bool:
        """Check if share link is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_valid(self) -> bool:
        """Check if share link is valid and active."""
        return (
            self.is_active and 
            not self.is_expired() and 
            (self.allowed_downloads == -1 or self.download_count < self.allowed_downloads)
        )


# === Phase 6: Enhanced Collaboration Models ===

class AuditEventType(enum.Enum):
    """Document audit event types."""
    CREATED = "created"
    UPDATED = "updated"
    VIEWED = "viewed"
    DOWNLOADED = "downloaded"
    SHARED = "shared"
    SHARE_REVOKED = "share_revoked"
    PREDICTION_INGESTED = "prediction_ingested"
    CORRECTION_APPLIED = "correction_applied"
    PERMISSION_CHANGED = "permission_changed"
    STATUS_CHANGED = "status_changed"
    VERSION_CREATED = "version_created"
    COMMENT_ADDED = "comment_added"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    LEGAL_HOLD_APPLIED = "legal_hold_applied"
    LEGAL_HOLD_REMOVED = "legal_hold_removed"


class DocumentAuditEvent(Base, TimestampMixin):
    """Enhanced audit event tracking for documents."""
    
    __tablename__ = "document_audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Event information
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    event_description = Column(Text, nullable=False)
    
    # User and context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Event details
    before_data = Column(JSON, default=dict)  # State before change
    after_data = Column(JSON, default=dict)   # State after change
    field_changes = Column(JSON, default=dict)  # Field-level changes
    
    # Metadata
    event_metadata = Column(JSON, default=dict)  # Additional event context
    
    # Organization for multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relations
    document = relationship("Document", back_populates="audit_events")
    user = relationship("User")
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<DocumentAuditEvent(id={self.id}, type={self.event_type.value}, document_id={self.document_id})>"


class SecureSharePermission(enum.Enum):
    """Secure share permission levels."""
    VIEW_ONLY = "view_only"
    DOWNLOAD = "download"
    COMMENT = "comment"
    EDIT = "edit"


class DocumentSecureShare(Base, TimestampMixin):
    """Enhanced secure sharing with fine-grained permissions."""
    
    __tablename__ = "document_secure_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Secure sharing
    share_slug = Column(String(64), unique=True, nullable=False, index=True)
    access_code = Column(String(32), nullable=True)  # Optional access code
    
    # Permissions and restrictions
    permission_level = Column(SQLEnum(SecureSharePermission), default=SecureSharePermission.VIEW_ONLY)
    allowed_views = Column(Integer, default=-1)  # -1 for unlimited
    view_count = Column(Integer, default=0)
    allowed_downloads = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Time restrictions
    expires_at = Column(DateTime, nullable=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    
    # Access control
    recipient_email = Column(String(255), nullable=True)
    recipient_name = Column(String(255), nullable=True)
    requires_authentication = Column(Boolean, default=False)
    ip_whitelist = Column(JSON, default=list)  # List of allowed IPs
    
    # Watermarking and tracking
    watermark_text = Column(String(255), nullable=True)
    track_access = Column(Boolean, default=True)
    notify_on_access = Column(Boolean, default=False)
    
    # Sharing metadata
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    share_reason = Column(Text)
    internal_notes = Column(Text)
    
    # Status and revocation
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    revocation_reason = Column(Text)
    
    # Organization for multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relations
    document = relationship("Document", back_populates="secure_shares")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])
    organization = relationship("Organization")
    access_logs = relationship("DocumentShareAccessLog", back_populates="secure_share", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.share_slug:
            self.share_slug = self._generate_secure_slug()
        if self.access_code is None and kwargs.get('requires_access_code', False):
            self.access_code = self._generate_access_code()
    
    @staticmethod
    def _generate_secure_slug() -> str:
        """Generate a secure, URL-safe slug for sharing."""
        # Use a combination of letters and numbers, avoiding confusing characters
        chars = string.ascii_letters + string.digits
        # Remove potentially confusing characters
        chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('l', '').replace('I', '')
        return ''.join(secrets.choice(chars) for _ in range(32))
    
    @staticmethod
    def _generate_access_code() -> str:
        """Generate a 6-digit access code."""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self) -> bool:
        """Check if share is expired."""
        now = datetime.utcnow()
        return (self.expires_at and now > self.expires_at) or now < self.valid_from
    
    def is_valid(self) -> bool:
        """Check if share is valid and can be accessed."""
        if not self.is_active or self.is_expired():
            return False
        
        # Check view limits
        if self.allowed_views != -1 and self.view_count >= self.allowed_views:
            return False
        
        return True
    
    def can_download(self) -> bool:
        """Check if downloads are allowed."""
        return (
            self.permission_level in [SecureSharePermission.DOWNLOAD, SecureSharePermission.EDIT] and
            (self.allowed_downloads == -1 or self.download_count < self.allowed_downloads)
        )
    
    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
    
    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1


class DocumentShareAccessLog(Base, TimestampMixin):
    """Log access to secure document shares."""
    
    __tablename__ = "document_share_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    secure_share_id = Column(Integer, ForeignKey("document_secure_shares.id"), nullable=False, index=True)
    
    # Access details
    access_type = Column(String(50), nullable=False)  # view, download, denied
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Geographic data (optional)
    country = Column(String(100))
    city = Column(String(100))
    
    # Success/failure
    success = Column(Boolean, default=True)
    failure_reason = Column(String(255))
    
    # User context (if authenticated)
    authenticated_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    secure_share = relationship("DocumentSecureShare", back_populates="access_logs")
    authenticated_user = relationship("User")


class DocumentVersionDiff(Base, TimestampMixin):
    """Store computed diffs between document versions."""
    
    __tablename__ = "document_version_diffs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Version comparison
    from_version = Column(Integer, nullable=False)
    to_version = Column(Integer, nullable=False)
    
    # Diff data
    field_diffs = Column(JSON, default=dict)  # Field-by-field differences
    content_diff = Column(Text)  # Human-readable content diff
    diff_summary = Column(Text)  # Summary of changes
    
    # Statistics
    additions_count = Column(Integer, default=0)
    deletions_count = Column(Integer, default=0)
    modifications_count = Column(Integer, default=0)
    
    # Metadata
    diff_generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    generation_method = Column(String(50), default="automated")  # automated, manual
    
    # Organization for multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relations
    document = relationship("Document")
    generated_by = relationship("User")
    organization = relationship("Organization")
    
    __table_args__ = (
        Index('idx_version_diff_lookup', 'document_id', 'from_version', 'to_version'),
        Index('idx_version_diff_org', 'organization_id', 'created_at'),
    )


    __table_args__ = (
        Index('idx_version_diff_lookup', 'document_id', 'from_version', 'to_version'),
        Index('idx_version_diff_org', 'organization_id', 'created_at'),
    )
