# models/user.py

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

# Import from local dependencies
from .dependencies import Base, utcnow, create_password_constraint, create_email_constraint

# Phase 4: Define enums for schema alignment
class OrganizationPlan(PyEnum):
    """Enum for organization plan types."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class APIKeyScope(PyEnum):
    """Enum for API key scopes."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    FULL_ACCESS = "full_access"

class UserRole(PyEnum):
    """Enum for user roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"

class UserStatus(PyEnum):
    """Enum for user status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

# Phase 4: Base mixin for timestamp and soft delete functionality
class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """Model for organizations that users can belong to."""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    plan = Column(Enum(OrganizationPlan), default=OrganizationPlan.FREE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization", foreign_keys="User.organization_id")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="organization", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="organization", cascade="all, delete-orphan")
    
    # Document relationships - NEW
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")

class User(Base, TimestampMixin, SoftDeleteMixin):
    """Enhanced User model with Phase 4 contract compliance."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)  # Specified length for hash
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # Admin privilege flag
    email_verified = Column(Boolean, default=False, nullable=False)  # Email verification status
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)  # User role
    last_login = Column(DateTime, nullable=True)  # Track last login timestamp
    login_count = Column(Integer, default=0, nullable=False)  # Track total logins
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    revoked_tokens = relationship("RevokedToken", back_populates="user", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Client and Case relationships
    created_clients = relationship("Client", foreign_keys="Client.created_by_id", back_populates="created_by")
    assigned_clients = relationship("Client", foreign_keys="Client.assigned_to_id", back_populates="assigned_to")
    created_cases = relationship("Case", foreign_keys="Case.created_by_id", back_populates="created_by")
    assigned_cases = relationship("Case", foreign_keys="Case.assigned_to_id", back_populates="assigned_to")
    supervised_cases = relationship("Case", foreign_keys="Case.supervising_attorney_id", back_populates="supervising_attorney")
    
    # Document relationships - NEW
    created_documents = relationship("Document", foreign_keys="Document.created_by_id", back_populates="created_by")
    edited_documents = relationship("Document", foreign_keys="Document.edited_by_id", back_populates="edited_by")

    def update_login_timestamp(self):
        """Update the last login timestamp and increment login count."""
        self.last_login = utcnow()
        self.login_count += 1

    def activate(self):
        """Activate the user account."""
        self.is_active = True
        self.status = UserStatus.ACTIVE

    def verify_email(self):
        """Mark the user's email as verified."""
        self.email_verified = True
        self.is_verified = True
