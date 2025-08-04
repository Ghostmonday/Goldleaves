# models/client.py

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, Enum, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

# Import from local dependencies
from .dependencies import Base, utcnow
from .user import TimestampMixin, SoftDeleteMixin


class ClientType(PyEnum):
    """Enum for client types."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"


class ClientStatus(PyEnum):
    """Enum for client status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    FORMER = "former"
    BLOCKED = "blocked"


class ClientPriority(PyEnum):
    """Enum for client priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Language(PyEnum):
    """Enum for preferred languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"


class Client(Base, TimestampMixin, SoftDeleteMixin):
    """Enhanced Client model with multi-tenant support."""
    __tablename__ = "clients"

    # Core fields
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly identifier
    
    # Basic information
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=True, index=True)  # Computed field
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    
    # Organization/Business information
    company_name = Column(String(200), nullable=True, index=True)
    job_title = Column(String(100), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Client metadata
    client_type = Column(Enum(ClientType), default=ClientType.INDIVIDUAL, nullable=False)
    status = Column(Enum(ClientStatus), default=ClientStatus.PROSPECT, nullable=False)
    priority = Column(Enum(ClientPriority), default=ClientPriority.MEDIUM, nullable=False)
    preferred_language = Column(Enum(Language), default=Language.ENGLISH, nullable=False)
    
    # Notes and tags
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of string tags
    internal_notes = Column(Text, nullable=True)  # Private notes for staff
    
    # External references
    external_id = Column(String(100), nullable=True, index=True)  # External system reference
    source = Column(String(100), nullable=True)  # How client was acquired
    referral_source = Column(String(200), nullable=True)
    
    # Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    cases = relationship("Case", back_populates="client", cascade="all, delete-orphan")
    
    # Document relationships - NEW
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")
    
    # Composite indexes for performance and multi-tenant isolation
    __table_args__ = (
        Index('idx_client_org_status', 'organization_id', 'status'),
        Index('idx_client_org_name', 'organization_id', 'last_name', 'first_name'),
        Index('idx_client_org_type', 'organization_id', 'client_type'),
        Index('idx_client_org_priority', 'organization_id', 'priority'),
        Index('idx_client_org_assigned', 'organization_id', 'assigned_to_id'),
        Index('idx_client_email_org', 'email', 'organization_id'),
        Index('idx_client_company_org', 'company_name', 'organization_id'),
        Index('idx_client_external_id_org', 'external_id', 'organization_id'),
        Index('idx_client_slug_unique', 'slug'),  # Global unique slug
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.full_name}', org_id={self.organization_id}, status={self.status.value})>"

    def update_full_name(self):
        """Update the computed full name field."""
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name
        else:
            self.full_name = None

    def add_tag(self, tag: str):
        """Add a tag to the client."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the client."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if client has a specific tag."""
        return self.tags is not None and tag in self.tags

    def activate(self):
        """Activate the client."""
        self.status = ClientStatus.ACTIVE

    def deactivate(self):
        """Deactivate the client."""
        self.status = ClientStatus.INACTIVE

    def block(self):
        """Block the client."""
        self.status = ClientStatus.BLOCKED

    def set_priority(self, priority: ClientPriority):
        """Set client priority."""
        self.priority = priority

    def get_display_name(self) -> str:
        """Get the best display name for the client."""
        if self.full_name:
            return self.full_name
        elif self.company_name:
            return self.company_name
        elif self.email:
            return self.email
        else:
            return f"Client #{self.id}"

    def get_contact_info(self) -> dict:
        """Get consolidated contact information."""
        return {
            "email": self.email,
            "phone": self.phone,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state_province,
                "postal_code": self.postal_code,
                "country": self.country
            }
        }


class ClientDocument(Base, TimestampMixin, SoftDeleteMixin):
    """Documents associated with clients."""
    __tablename__ = "client_documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    document_type = Column(String(100), nullable=True)  # ID, contract, invoice, etc.
    
    # Multi-tenant isolation
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    client = relationship("Client")
    organization = relationship("Organization")
    uploaded_by = relationship("User")
    
    __table_args__ = (
        Index('idx_client_doc_org', 'client_id', 'organization_id'),
        Index('idx_client_doc_type', 'client_id', 'document_type'),
    )

    def __repr__(self):
        return f"<ClientDocument(id={self.id}, name='{self.name}', client_id={self.client_id})>"
