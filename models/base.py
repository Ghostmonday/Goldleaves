"""
Base model classes and mixins for all database models.
Provides common functionality like timestamps, soft deletes, and audit trails.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from core.database import Base


class TimestampMixin:
    """Mixin for automatic timestamp fields."""

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            comment="Record creation timestamp"
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
            comment="Record last update timestamp"
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    @declared_attr
    def is_deleted(cls):
        return Column(
            Boolean,
            nullable=False,
            default=False,
            index=True,
            comment="Soft delete flag"
        )

    @declared_attr
    def deleted_at(cls):
        return Column(
            DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp"
        )

    @declared_attr
    def deleted_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who performed the soft delete"
        )

    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """Mark record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class AuditMixin:
    """Mixin for audit trail fields."""

    @declared_attr
    def created_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who created the record"
        )

    @declared_attr
    def updated_by(cls):
        return Column(
            String(255),
            nullable=True,
            comment="User who last updated the record"
        )

    @declared_attr
    def version(cls):
        return Column(
            Integer,
            nullable=False,
            default=1,
            comment="Record version for optimistic locking"
        )


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary keys."""

    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid4,
            nullable=False,
            comment="Unique identifier"
        )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Base model with all common mixins."""

    __abstract__ = True

    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """Convert model to dictionary."""
        exclude = exclude or set()
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }

    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None) -> None:
        """Update model from dictionary."""
        exclude = exclude or set()
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_by_id(cls, db: Session, id: Any):
        """Get record by ID."""
        return db.query(cls).filter(
            cls.id == id,
            cls.is_deleted == False
        ).first()

    @classmethod
    def get_all(cls, db: Session, skip: int = 0, limit: int = 100):
        """Get all non-deleted records with pagination."""
        return db.query(cls).filter(
            cls.is_deleted == False
        ).offset(skip).limit(limit).all()

    @classmethod
    def count(cls, db: Session) -> int:
        """Count non-deleted records."""
        return db.query(cls).filter(
            cls.is_deleted == False
        ).count()

    def save(self, db: Session) -> None:
        """Save the current instance."""
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session, hard: bool = False, deleted_by: Optional[str] = None) -> None:
        """Delete the record (soft delete by default)."""
        if hard:
            db.delete(self)
        else:
            self.soft_delete(deleted_by)
        db.commit()

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class IntegerPrimaryKeyMixin:
    """Mixin for integer primary keys (alternative to UUID)."""

    @declared_attr
    def id(cls):
        return Column(
            Integer,
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment="Unique identifier"
        )


class NamedModelMixin:
    """Mixin for models with name field."""

    @declared_attr
    def name(cls):
        return Column(
            String(255),
            nullable=False,
            index=True,
            comment="Name"
        )

    @declared_attr
    def description(cls):
        return Column(
            String(1000),
            nullable=True,
            comment="Description"
        )


class SlugMixin:
    """Mixin for models with slug field."""

    @declared_attr
    def slug(cls):
        return Column(
            String(255),
            nullable=False,
            unique=True,
            index=True,
            comment="URL-friendly identifier"
        )


# Event listeners for automatic audit fields
@event.listens_for(BaseModel, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    """Set audit fields before insert."""
    # This would be set from the request context in a real application
    # For now, we'll leave it as a placeholder
    if hasattr(target, 'created_by') and target.created_by is None:
        target.created_by = 'system'
    if hasattr(target, 'updated_by'):
        target.updated_by = target.created_by


@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update audit fields before update."""
    if hasattr(target, 'updated_by') and target.updated_by is None:
        target.updated_by = 'system'
    if hasattr(target, 'version'):
        target.version += 1
