

"""Document models and enums for tests (collaboration, prediction, storage)."""
from __future__ import annotations

from enum import Enum
from sqlalchemy import (
	Column,
	Integer,
	String,
	Text,
	DateTime,
	Boolean,
	ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .dependencies import Base


class PredictionStatus(str, Enum):
	PENDING = "pending"
	PROCESSING = "processing"
	COMPLETED = "completed"
	FAILED = "failed"


class DocumentType(str, Enum):
	CONTRACT = "contract"
	INVOICE = "invoice"
	LEGAL_BRIEF = "legal_brief"
	AGREEMENT = "agreement"
	GENERIC = "generic"


class DocumentStatus(str, Enum):
	DRAFT = "draft"
	FINAL = "final"


class DocumentConfidentiality(str, Enum):
	PUBLIC = "public"
	CONFIDENTIAL = "confidential"
	INTERNAL = "internal"


class Document(Base):
	__tablename__ = "documents"
	id = Column(Integer, primary_key=True, autoincrement=True)
	title = Column(String(255))
	document_type = Column(String(50), default=DocumentType.GENERIC.value)
	file_path = Column(String(512), nullable=True)
	file_size = Column(Integer, nullable=True)
	organization_id = Column(Integer, nullable=True)
	created_by_id = Column(Integer, nullable=True)
	uploaded_by_id = Column(Integer, nullable=True)
	version = Column(Integer, default=1)
	status = Column(String(20), default=DocumentStatus.DRAFT.value)
	confidentiality = Column(String(20), default=DocumentConfidentiality.INTERNAL.value)
	content = Column(Text, nullable=True)
	case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
	client_id = Column(Integer, nullable=True)
	ai_predictions = Column(Text, nullable=True)  # store as JSON string in tests
	prediction_score = Column(Integer, nullable=True)

	# Relationships
	case = relationship("Case", back_populates="prediction_documents")


class DocumentVersion(Base):
	__tablename__ = "document_versions"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, ForeignKey("documents.id"))
	version_number = Column(Integer, nullable=False)
	title = Column(String(255), nullable=True)
	content = Column(Text, nullable=True)
	change_summary = Column(String(255), nullable=True)
	change_reason = Column(String(255), nullable=True)
	prediction_status = Column(String(20), default=PredictionStatus.PENDING.value)
	prediction_score = Column(Integer, nullable=True)
	changed_by_id = Column(Integer, nullable=True)
	organization_id = Column(Integer, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentVersionDiff(Base):
	__tablename__ = "document_version_diffs"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, nullable=False)
	from_version = Column(Integer, nullable=False)
	to_version = Column(Integer, nullable=False)
	field_path = Column(String(255), nullable=True)
	old_value = Column(Text, nullable=True)
	new_value = Column(Text, nullable=True)
	change_type = Column(String(50), nullable=True)
	diff_summary = Column(Text, nullable=True)
	content_diff = Column(Text, nullable=True)


class AuditEventType(str, Enum):
	CREATED = "created"
	VIEWED = "viewed"
	MODIFIED = "modified"


class DocumentAuditEvent(Base):
	__tablename__ = "document_audit_events"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, nullable=False)
	event_type = Column(String(50))
	event_description = Column(Text, nullable=True)
	user_id = Column(Integer, nullable=True)
	organization_id = Column(Integer, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())


class SecureSharePermission(str, Enum):
	VIEW_ONLY = "view_only"
	COMMENT = "comment"
	EDIT = "edit"


class DocumentSecureShare(Base):
	__tablename__ = "document_secure_shares"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, nullable=False)
	recipient_email = Column(String(255), nullable=False)
	recipient_name = Column(String(255), nullable=True)
	permission_level = Column(String(50), default=SecureSharePermission.VIEW_ONLY.value)
	share_slug = Column(String(64), nullable=True)
	share_url = Column(String(512), nullable=True)
	access_code = Column(String(64), nullable=True)
	allowed_views = Column(Integer, default=0)
	allowed_downloads = Column(Integer, default=0)
	view_count = Column(Integer, default=0)
	download_count = Column(Integer, default=0)
	is_active = Column(Boolean, default=True)
	requires_authentication = Column(Boolean, default=False)
	track_access = Column(Boolean, default=True)
	expires_at = Column(DateTime(timezone=True), nullable=True)
	revoked_at = Column(DateTime(timezone=True), nullable=True)
	revoked_by_id = Column(Integer, nullable=True)
	revocation_reason = Column(String(255), nullable=True)


class DocumentShareAccessLog(Base):
	__tablename__ = "document_share_access_logs"
	id = Column(Integer, primary_key=True, autoincrement=True)
	share_slug = Column(String(64), nullable=False)
	ip_address = Column(String(64), nullable=True)
	user_agent = Column(String(255), nullable=True)
	success = Column(Boolean, default=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentCorrection(Base):
	__tablename__ = "document_corrections"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, nullable=False)
	field_path = Column(String(255), nullable=False)
	original_value = Column(Text, nullable=True)
	corrected_value = Column(Text, nullable=True)
	confidence_before = Column(Integer, nullable=True)
	confidence_after = Column(Integer, nullable=True)
	correction_reason = Column(String(255), nullable=True)
	correction_type = Column(String(50), nullable=True)
	corrected_by_id = Column(Integer, nullable=True)
	review_status = Column(String(50), nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentShare(Base):
	__tablename__ = "document_shares"
	id = Column(Integer, primary_key=True, autoincrement=True)
	document_id = Column(Integer, nullable=False)
	shared_with = Column(String(255), nullable=True)
	permission = Column(String(50), default=SecureSharePermission.VIEW_ONLY.value)
	created_at = Column(DateTime(timezone=True), server_default=func.now())


