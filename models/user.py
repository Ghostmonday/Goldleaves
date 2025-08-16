from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy import event

# Use the same Base that tests import: models.dependencies.Base
from .dependencies import Base


class OrganizationPlan(str, Enum):
    FREE = "free"
    PRO = "pro"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Additional fields referenced by tests
    domain = Column(String(255), nullable=True)
    type = Column(String(50), nullable=True)
    plan = Column(String(50), default=OrganizationPlan.FREE.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all,delete")

    # Soft delete helpers expected by tests
    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=False, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default=UserStatus.ACTIVE.value, nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="users")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Login tracking
    login_count = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)

    # Methods required by tests
    def update_login_timestamp(self) -> None:
        self.login_count = (self.login_count or 0) + 1
        self.last_login = datetime.utcnow()

    def activate(self) -> None:
        self.is_active = True
        self.status = UserStatus.ACTIVE.value

    def deactivate(self) -> None:
        self.is_active = False
        self.status = UserStatus.INACTIVE.value

    def suspend(self) -> None:
        self.is_active = False
        self.status = UserStatus.SUSPENDED.value

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None

    def verify_email(self) -> None:
        self.email_verified = True

    # Convenience attribute used in tests
    @property
    def is_verified(self) -> bool:
        return bool(self.email_verified)

    @is_verified.setter
    def is_verified(self, value: bool) -> None:
        self.email_verified = bool(value)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email}>"

    # Test helper to set a password
    def set_password(self, raw: str) -> None:
        # Minimal implementation for tests; not secure.
        self.hashed_password = f"hashed:{raw}"


# Auto update updated_at on change
@event.listens_for(User, "before_update", propagate=True)
def _user_before_update(mapper, connection, target):  # pragma: no cover
    target.updated_at = datetime.utcnow()


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(1024), nullable=False, unique=False)
    token_type = Column(String(50), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")


class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    scope = Column(String(50), default=APIKeyScope.READ.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    user = relationship("User")
    organization = relationship("Organization")

    def update_usage(self) -> None:
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used_at = datetime.utcnow()

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < datetime.utcnow())
