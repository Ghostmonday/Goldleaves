"""Stub of DocumentCollaborationService with minimal methods used in tests.
This provides data objects but does not implement full business logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from models.document import (
	Document, DocumentVersion, DocumentVersionDiff, DocumentAuditEvent,
	SecureSharePermission, DocumentSecureShare, DocumentShareAccessLog,
)


@dataclass
class VersionHistory:
	document_id: int
	current_version: int
	total_versions: int
	versions: List[DocumentVersion] = field(default_factory=list)


@dataclass
class VersionDiff:
	document_id: int
	from_version: int
	to_version: int
	total_changes: int
	field_diffs: List[DocumentVersionDiff] = field(default_factory=list)
	content_diff: Optional[str] = None
	diff_summary: Optional[str] = None


@dataclass
class ShareAccess:
	success: bool
	document_title: Optional[str] = None
	permission_level: Optional[SecureSharePermission] = None
	remaining_views: Optional[int] = None


class DocumentCollaborationService:
	@staticmethod
	def get_version_history(db: Session, document_id: int, organization_id: Optional[int], limit: int = 50) -> VersionHistory:
		versions = (
			db.query(DocumentVersion)
			.filter(DocumentVersion.document_id == document_id)
			.order_by(DocumentVersion.version_number.desc())
			.limit(limit)
			.all()
		)
		current_version = versions[0].version_number if versions else 0
		return VersionHistory(
			document_id=document_id,
			current_version=current_version,
			total_versions=len(versions),
			versions=versions,
		)

	@staticmethod
	def compare_versions(db: Session, document_id: int, comparison_request, organization_id: Optional[int], user_id: Optional[int]):
		# Simplified diff: compare titles of versions
		from_v = comparison_request.from_version
		to_v = comparison_request.to_version
		v_from = (
			db.query(DocumentVersion)
			.filter(DocumentVersion.document_id == document_id, DocumentVersion.version_number == from_v)
			.first()
		)
		v_to = (
			db.query(DocumentVersion)
			.filter(DocumentVersion.document_id == document_id, DocumentVersion.version_number == to_v)
			.first()
		)
		diffs: List[DocumentVersionDiff] = []
		total_changes = 0
		if v_from and v_to and v_from.title != v_to.title:
			d = DocumentVersionDiff(
				document_id=document_id,
				from_version=from_v,
				to_version=to_v,
				field_path="title",
				old_value=v_from.title,
				new_value=v_to.title,
				change_type="modified",
			)
			db.add(d)
			db.commit()
			diffs.append(d)
			total_changes += 1
		return VersionDiff(
			document_id=document_id,
			from_version=from_v,
			to_version=to_v,
			total_changes=total_changes,
			field_diffs=diffs,
			content_diff="",
			diff_summary=f"{total_changes} changes",
		)

	@staticmethod
	def create_secure_share(db: Session, document_id: int, share_data, organization_id: Optional[int], user_id: Optional[int], base_url: str = "https://example.com") -> DocumentSecureShare:
		import secrets
		share = DocumentSecureShare(
			document_id=document_id,
			recipient_email=getattr(share_data, "recipient_email", "recipient@example.com"),
			recipient_name=getattr(share_data, "recipient_name", None),
			permission_level=(getattr(share_data, "permission_level", SecureSharePermission.VIEW_ONLY)).value
			if hasattr(getattr(share_data, "permission_level", None), "value") else str(getattr(share_data, "permission_level", SecureSharePermission.VIEW_ONLY)),
			allowed_views=getattr(share_data, "allowed_views", 0) or 0,
			allowed_downloads=getattr(share_data, "allowed_downloads", 0) or 0,
			requires_authentication=getattr(share_data, "requires_authentication", False) or False,
			track_access=getattr(share_data, "track_access", True) or True,
		)
		share.share_slug = secrets.token_hex(16)
		share.share_url = f"{base_url}/share/{share.share_slug}"
		# Optional features
		if getattr(share_data, "requires_access_code", False):
			share.access_code = secrets.token_hex(3)
		if getattr(share_data, "expires_at", None):
			share.expires_at = share_data.expires_at
		db.add(share)
		db.commit()
		db.refresh(share)
		return share

	@staticmethod
	def access_secure_share(db: Session, share_slug: str, access_request, ip_address: str | None = None, user_agent: str | None = None):
		share = db.query(DocumentSecureShare).filter(DocumentSecureShare.share_slug == share_slug).first()
		if not share or not share.is_active:
			return ShareAccess(success=False)
		# Expiry check
		if share.expires_at and share.expires_at < datetime.utcnow():
			from core.exceptions import ValidationError
			raise ValidationError("Share has expired")
		# Access code if required
		if share.access_code and getattr(access_request, "access_code", None) != share.access_code:
			from core.exceptions import ValidationError
			raise ValidationError("Invalid access code")
		share.view_count = (share.view_count or 0) + 1
		db.add(DocumentShareAccessLog(share_slug=share_slug, ip_address=ip_address, user_agent=user_agent, success=True))
		db.commit()
		# Get document title if exists
		doc = db.query(Document).filter(Document.id == share.document_id).first()
		return ShareAccess(success=True, document_title=getattr(doc, "title", None), permission_level=SecureSharePermission(share.permission_level), remaining_views=max(0, (share.allowed_views or 0) - (share.view_count or 0)))

	@staticmethod
	def revoke_secure_share(db: Session, share_id: int, organization_id: Optional[int], user_id: Optional[int], revocation_reason: str | None = None) -> bool:
		share = db.query(DocumentSecureShare).filter(DocumentSecureShare.id == share_id).first()
		if not share:
			return False
		share.is_active = False
		share.revoked_by_id = user_id
		share.revocation_reason = revocation_reason
		share.revoked_at = datetime.utcnow()
		db.commit()
		return True

	@staticmethod
	def get_document_audit_trail(db: Session, document_id: int, organization_id: Optional[int], limit: int = 100):
		events = (
			db.query(DocumentAuditEvent)
			.filter(DocumentAuditEvent.document_id == document_id)
			.order_by(DocumentAuditEvent.created_at.desc())
			.limit(limit)
			.all()
		)
		summary = {"created": 0, "viewed": 0, "modified": 0}
		for e in events:
			et = (e.event_type or "").lower()
			if et in summary:
				summary[et] += 1
		return type("AuditTrail", (), {
			"document_id": document_id,
			"total_events": len(events),
			"events": events,
			"event_types_summary": summary,
		})


