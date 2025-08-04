# services/document_collaboration.py

"""Phase 6: Document collaboration service for version control, diffing, and secure sharing."""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from datetime import datetime, timedelta
import json
import difflib
import re
from urllib.parse import urljoin

from models.document import (
    Document, DocumentVersion, DocumentSecureShare, DocumentShareAccessLog,
    DocumentAuditEvent, DocumentVersionDiff, AuditEventType, SecureSharePermission
)
from models.user import User, Organization
from core.exceptions import NotFoundError, ValidationError, PermissionError
from services.document import DocumentService
from schemas.document.collaboration import (
    VersionComparisonRequest, VersionDiffResponse, FieldDiff, ContentDiff,
    VersionHistoryResponse, VersionHistoryEntry, SecureShareCreate, SecureShareResponse,
    ShareAccessRequest, ShareAccessResponse, AuditEventResponse, DocumentAuditTrailResponse,
    CollaborationStats
)


class DocumentCollaborationService:
    """Service layer for document collaboration features."""
    
    @staticmethod
    def get_version_history(
        db: Session,
        document_id: int,
        organization_id: int,
        limit: int = 50,
        include_metadata: bool = True
    ) -> VersionHistoryResponse:
        """Get comprehensive version history for a document."""
        
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Get version history with user information
        versions_query = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).options(joinedload(DocumentVersion.changed_by)).order_by(
            desc(DocumentVersion.created_at)
        ).limit(limit)
        
        versions = versions_query.all()
        
        # Build version entries
        version_entries = []
        for i, version in enumerate(versions):
            # Calculate changes from previous version
            changes_count = None
            if i < len(versions) - 1:
                changes_count = DocumentCollaborationService._count_version_changes(
                    versions[i+1], version
                )
            
            entry = VersionHistoryEntry(
                version_number=version.version_number,
                title=version.title or "Untitled",
                change_summary=version.change_summary or "No summary available",
                change_reason=version.change_reason,
                changed_by_name=version.changed_by.full_name if version.changed_by else None,
                changed_by_id=version.changed_by_id,
                created_at=version.created_at,
                prediction_status=version.prediction_status.value if version.prediction_status else None,
                prediction_score=version.prediction_score,
                content_length=len(version.content) if version.content else 0,
                has_corrections=bool(version.corrections),
                changes_from_previous=changes_count,
                is_major_version=changes_count and changes_count > 5 if changes_count else False
            )
            version_entries.append(entry)
        
        # Calculate totals
        total_changes = sum(
            v.changes_from_previous for v in version_entries 
            if v.changes_from_previous is not None
        )
        
        return VersionHistoryResponse(
            document_id=document_id,
            current_version=document.version,
            total_versions=len(versions),
            versions=version_entries,
            first_created=document.created_at,
            last_modified=document.edited_at or document.created_at,
            total_changes=total_changes
        )
    
    @staticmethod
    def compare_versions(
        db: Session,
        document_id: int,
        comparison_request: VersionComparisonRequest,
        organization_id: int,
        user_id: int
    ) -> VersionDiffResponse:
        """Compare two versions of a document."""
        
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Get the two versions
        from_version = db.query(DocumentVersion).filter(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == comparison_request.from_version
            )
        ).first()
        
        to_version = db.query(DocumentVersion).filter(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == comparison_request.to_version
            )
        ).first()
        
        if not from_version or not to_version:
            raise NotFoundError("One or both versions not found")
        
        # Check for existing diff
        existing_diff = db.query(DocumentVersionDiff).filter(
            and_(
                DocumentVersionDiff.document_id == document_id,
                DocumentVersionDiff.from_version == comparison_request.from_version,
                DocumentVersionDiff.to_version == comparison_request.to_version
            )
        ).first()
        
        if existing_diff:
            # Return cached diff
            return DocumentCollaborationService._build_diff_response(
                existing_diff, comparison_request
            )
        
        # Generate new diff
        field_diffs = DocumentCollaborationService._generate_field_diffs(
            from_version, to_version
        )
        
        content_diff = None
        if comparison_request.include_content_diff:
            content_diff = DocumentCollaborationService._generate_content_diff(
                from_version.content or "",
                to_version.content or "",
                comparison_request.diff_format
            )
        
        metadata_changes = {}
        if comparison_request.include_metadata_diff:
            metadata_changes = DocumentCollaborationService._generate_metadata_diff(
                from_version.metadata or {},
                to_version.metadata or {}
            )
        
        # Calculate statistics
        total_changes = len(field_diffs)
        significant_changes = len([d for d in field_diffs if d.change_type != "minor"])
        
        # Generate summary
        diff_summary = DocumentCollaborationService._generate_diff_summary(
            field_diffs, content_diff
        )
        
        # Store diff for future use
        version_diff = DocumentVersionDiff(
            document_id=document_id,
            from_version=comparison_request.from_version,
            to_version=comparison_request.to_version,
            field_diffs={
                "diffs": [diff.dict() for diff in field_diffs]
            },
            content_diff=content_diff.diff_content if content_diff else None,
            diff_summary=diff_summary,
            additions_count=content_diff.additions_count if content_diff else 0,
            deletions_count=content_diff.deletions_count if content_diff else 0,
            modifications_count=total_changes,
            diff_generated_by=user_id,
            organization_id=organization_id
        )
        
        db.add(version_diff)
        db.commit()
        
        # Log audit event
        DocumentCollaborationService._log_audit_event(
            db, document_id, organization_id, user_id, 
            AuditEventType.VERSION_CREATED,
            f"Compared versions {comparison_request.from_version} to {comparison_request.to_version}",
            metadata={
                "from_version": comparison_request.from_version,
                "to_version": comparison_request.to_version,
                "total_changes": total_changes
            }
        )
        
        return VersionDiffResponse(
            document_id=document_id,
            from_version=comparison_request.from_version,
            to_version=comparison_request.to_version,
            field_diffs=field_diffs,
            content_diff=content_diff,
            metadata_changes=metadata_changes,
            total_changes=total_changes,
            significant_changes=significant_changes,
            diff_summary=diff_summary
        )
    
    @staticmethod
    def create_secure_share(
        db: Session,
        document_id: int,
        share_data: SecureShareCreate,
        organization_id: int,
        user_id: int,
        base_url: str = "https://app.goldleaves.com"
    ) -> SecureShareResponse:
        """Create a secure shareable link for a document."""
        
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Create secure share
        secure_share = DocumentSecureShare(
            document_id=document_id,
            recipient_email=share_data.recipient_email,
            recipient_name=share_data.recipient_name,
            permission_level=share_data.permission_level,
            expires_at=share_data.expires_at,
            allowed_views=share_data.allowed_views,
            allowed_downloads=share_data.allowed_downloads,
            requires_authentication=share_data.requires_authentication,
            ip_whitelist=share_data.ip_whitelist,
            watermark_text=share_data.watermark_text,
            track_access=share_data.track_access,
            notify_on_access=share_data.notify_on_access,
            share_reason=share_data.share_reason,
            internal_notes=share_data.internal_notes,
            shared_by_id=user_id,
            organization_id=organization_id
        )
        
        # Generate access code if required
        if share_data.requires_access_code:
            secure_share.access_code = DocumentSecureShare._generate_access_code()
        
        db.add(secure_share)
        db.commit()
        db.refresh(secure_share)
        
        # Log audit event
        DocumentCollaborationService._log_audit_event(
            db, document_id, organization_id, user_id,
            AuditEventType.SHARED,
            f"Created secure share for {share_data.recipient_email or 'anonymous'}",
            metadata={
                "share_id": secure_share.id,
                "permission_level": share_data.permission_level.value,
                "expires_at": share_data.expires_at.isoformat() if share_data.expires_at else None,
                "recipient_email": share_data.recipient_email
            }
        )
        
        # Build share URL
        share_url = urljoin(base_url, f"/share/{secure_share.share_slug}")
        
        return SecureShareResponse(
            id=secure_share.id,
            document_id=document_id,
            share_slug=secure_share.share_slug,
            access_code=secure_share.access_code,
            share_url=share_url,
            permission_level=secure_share.permission_level,
            expires_at=secure_share.expires_at,
            allowed_views=secure_share.allowed_views,
            view_count=secure_share.view_count,
            allowed_downloads=secure_share.allowed_downloads,
            download_count=secure_share.download_count,
            is_active=secure_share.is_active,
            is_expired=secure_share.is_expired(),
            is_valid=secure_share.is_valid(),
            created_at=secure_share.created_at,
            shared_by_name=secure_share.shared_by.full_name if secure_share.shared_by else None,
            recipient_email=secure_share.recipient_email,
            recipient_name=secure_share.recipient_name,
            share_reason=secure_share.share_reason
        )
    
    @staticmethod
    def access_secure_share(
        db: Session,
        share_slug: str,
        access_request: ShareAccessRequest,
        ip_address: str = None,
        user_agent: str = None,
        authenticated_user_id: int = None
    ) -> ShareAccessResponse:
        """Access a secure document share."""
        
        # Find the share
        secure_share = db.query(DocumentSecureShare).filter(
            DocumentSecureShare.share_slug == share_slug
        ).options(joinedload(DocumentSecureShare.document)).first()
        
        if not secure_share:
            raise NotFoundError("Share not found")
        
        # Validate access
        if not secure_share.is_valid():
            if secure_share.is_expired():
                raise ValidationError("Share has expired")
            elif not secure_share.is_active:
                raise ValidationError("Share has been revoked")
            elif secure_share.view_count >= secure_share.allowed_views:
                raise ValidationError("Maximum views exceeded")
        
        # Check access code if required
        if secure_share.access_code and access_request.access_code != secure_share.access_code:
            DocumentCollaborationService._log_share_access(
                db, secure_share.id, "denied", ip_address, user_agent,
                authenticated_user_id, False, "Invalid access code"
            )
            raise ValidationError("Invalid access code")
        
        # Check IP whitelist
        if secure_share.ip_whitelist and ip_address not in secure_share.ip_whitelist:
            DocumentCollaborationService._log_share_access(
                db, secure_share.id, "denied", ip_address, user_agent,
                authenticated_user_id, False, "IP not whitelisted"
            )
            raise ValidationError("Access denied from this IP address")
        
        # Check authentication requirement
        if secure_share.requires_authentication and not authenticated_user_id:
            raise PermissionError("Authentication required")
        
        # Update view count
        secure_share.increment_view_count()
        db.commit()
        
        # Log successful access
        DocumentCollaborationService._log_share_access(
            db, secure_share.id, "view", ip_address, user_agent, authenticated_user_id
        )
        
        # Calculate remaining access
        remaining_views = None
        if secure_share.allowed_views != -1:
            remaining_views = max(0, secure_share.allowed_views - secure_share.view_count)
        
        remaining_downloads = None
        if secure_share.can_download():
            remaining_downloads = max(0, secure_share.allowed_downloads - secure_share.download_count)
        
        # Generate download URL if permitted
        download_url = None
        download_expires_at = None
        if secure_share.can_download():
            # In a real implementation, this would be a signed URL
            download_url = f"/share/{share_slug}/download"
            download_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        return ShareAccessResponse(
            success=True,
            document_title=secure_share.document.title,
            document_type=secure_share.document.document_type.value,
            permission_level=secure_share.permission_level,
            created_at=secure_share.document.created_at,
            file_size=secure_share.document.file_size,
            watermark_text=secure_share.watermark_text,
            remaining_views=remaining_views,
            remaining_downloads=remaining_downloads,
            download_url=download_url,
            download_expires_at=download_expires_at
        )
    
    @staticmethod
    def get_document_audit_trail(
        db: Session,
        document_id: int,
        organization_id: int,
        limit: int = 100,
        event_types: List[AuditEventType] = None
    ) -> DocumentAuditTrailResponse:
        """Get comprehensive audit trail for a document."""
        
        document = DocumentService.get_document(db, document_id, organization_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Build query
        query = db.query(DocumentAuditEvent).filter(
            DocumentAuditEvent.document_id == document_id
        ).options(joinedload(DocumentAuditEvent.user))
        
        if event_types:
            query = query.filter(DocumentAuditEvent.event_type.in_(event_types))
        
        # Get events
        events = query.order_by(desc(DocumentAuditEvent.created_at)).limit(limit).all()
        
        # Build event responses
        event_responses = []
        for event in events:
            event_response = AuditEventResponse(
                id=event.id,
                event_type=event.event_type,
                event_description=event.event_description,
                user_name=event.user.full_name if event.user else None,
                user_id=event.user_id,
                created_at=event.created_at,
                ip_address=event.ip_address,
                session_id=event.session_id,
                field_changes=event.field_changes or {},
                before_data=event.before_data or {},
                after_data=event.after_data or {},
                metadata=event.metadata or {}
            )
            event_responses.append(event_response)
        
        # Calculate summary statistics
        event_types_summary = {}
        user_activity_summary = {}
        
        for event in events:
            event_type = event.event_type.value
            event_types_summary[event_type] = event_types_summary.get(event_type, 0) + 1
            
            if event.user:
                user_name = event.user.full_name
                user_activity_summary[user_name] = user_activity_summary.get(user_name, 0) + 1
        
        # Calculate compliance metrics
        total_views = len([e for e in events if e.event_type == AuditEventType.VIEWED])
        total_downloads = len([e for e in events if e.event_type == AuditEventType.DOWNLOADED])
        total_shares = len([e for e in events if e.event_type == AuditEventType.SHARED])
        total_corrections = len([e for e in events if e.event_type == AuditEventType.CORRECTION_APPLIED])
        
        # Get timeline boundaries
        first_event = events[-1].created_at if events else None
        last_event = events[0].created_at if events else None
        
        return DocumentAuditTrailResponse(
            document_id=document_id,
            current_version=document.version,
            total_events=len(events),
            events=event_responses,
            event_types_summary=event_types_summary,
            user_activity_summary=user_activity_summary,
            first_event=first_event,
            last_event=last_event,
            total_views=total_views,
            total_downloads=total_downloads,
            total_shares=total_shares,
            total_corrections=total_corrections
        )
    
    @staticmethod
    def get_collaboration_stats(
        db: Session,
        organization_id: int
    ) -> CollaborationStats:
        """Get organization collaboration statistics."""
        
        # Basic counts
        total_documents = db.query(func.count(Document.id)).filter(
            and_(Document.organization_id == organization_id, Document.is_deleted == False)
        ).scalar() or 0
        
        total_versions = db.query(func.count(DocumentVersion.id)).join(Document).filter(
            and_(Document.organization_id == organization_id, Document.is_deleted == False)
        ).scalar() or 0
        
        total_secure_shares = db.query(func.count(DocumentSecureShare.id)).filter(
            DocumentSecureShare.organization_id == organization_id
        ).scalar() or 0
        
        total_audit_events = db.query(func.count(DocumentAuditEvent.id)).filter(
            DocumentAuditEvent.organization_id == organization_id
        ).scalar() or 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_versions = db.query(func.count(DocumentVersion.id)).join(Document).filter(
            and_(
                Document.organization_id == organization_id,
                Document.is_deleted == False,
                DocumentVersion.created_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        recent_shares = db.query(func.count(DocumentSecureShare.id)).filter(
            and_(
                DocumentSecureShare.organization_id == organization_id,
                DocumentSecureShare.created_at >= thirty_days_ago
            )
        ).scalar() or 0
        
        # Active vs expired shares
        active_shares = db.query(func.count(DocumentSecureShare.id)).filter(
            and_(
                DocumentSecureShare.organization_id == organization_id,
                DocumentSecureShare.is_active == True,
                or_(
                    DocumentSecureShare.expires_at == None,
                    DocumentSecureShare.expires_at > datetime.utcnow()
                )
            )
        ).scalar() or 0
        
        expired_shares = db.query(func.count(DocumentSecureShare.id)).filter(
            and_(
                DocumentSecureShare.organization_id == organization_id,
                or_(
                    DocumentSecureShare.is_active == False,
                    and_(
                        DocumentSecureShare.expires_at != None,
                        DocumentSecureShare.expires_at <= datetime.utcnow()
                    )
                )
            )
        ).scalar() or 0
        
        # Calculate average share duration
        avg_duration_result = db.query(
            func.avg(
                func.extract('epoch', DocumentSecureShare.expires_at - DocumentSecureShare.created_at) / 86400
            )
        ).filter(
            and_(
                DocumentSecureShare.organization_id == organization_id,
                DocumentSecureShare.expires_at != None
            )
        ).scalar()
        
        average_share_duration = float(avg_duration_result) if avg_duration_result else 0.0
        
        # Most collaborated documents (by version count)
        most_collaborated = db.query(
            Document.title,
            func.count(DocumentVersion.id).label('version_count'),
            func.count(func.distinct(DocumentVersion.changed_by_id)).label('collaborator_count')
        ).join(DocumentVersion).filter(
            and_(Document.organization_id == organization_id, Document.is_deleted == False)
        ).group_by(Document.id, Document.title).order_by(
            desc('version_count')
        ).limit(5).all()
        
        most_collaborated_documents = [
            {
                "title": result.title,
                "versions": result.version_count,
                "collaborators": result.collaborator_count
            }
            for result in most_collaborated
        ]
        
        return CollaborationStats(
            total_documents=total_documents,
            total_versions=total_versions,
            total_secure_shares=total_secure_shares,
            total_audit_events=total_audit_events,
            recent_collaborations=recent_versions,
            recent_shares_created=recent_shares,
            recent_versions_created=recent_versions,
            most_collaborated_documents=most_collaborated_documents,
            most_active_collaborators=[],  # Would need user analysis
            active_shares=active_shares,
            expired_shares=expired_shares,
            average_share_duration_days=average_share_duration
        )
    
    @staticmethod
    def revoke_secure_share(
        db: Session,
        share_id: int,
        organization_id: int,
        user_id: int,
        revocation_reason: str = None
    ) -> bool:
        """Revoke a secure document share."""
        
        secure_share = db.query(DocumentSecureShare).filter(
            and_(
                DocumentSecureShare.id == share_id,
                DocumentSecureShare.organization_id == organization_id
            )
        ).first()
        
        if not secure_share:
            raise NotFoundError("Secure share not found")
        
        # Update share status
        secure_share.is_active = False
        secure_share.revoked_at = datetime.utcnow()
        secure_share.revoked_by_id = user_id
        secure_share.revocation_reason = revocation_reason
        
        db.commit()
        
        # Log audit event
        DocumentCollaborationService._log_audit_event(
            db, secure_share.document_id, organization_id, user_id,
            AuditEventType.SHARE_REVOKED,
            f"Revoked secure share: {revocation_reason or 'No reason provided'}",
            metadata={
                "share_id": share_id,
                "revocation_reason": revocation_reason
            }
        )
        
        return True
    
    # Helper methods
    
    @staticmethod
    def _count_version_changes(old_version: DocumentVersion, new_version: DocumentVersion) -> int:
        """Count changes between two versions."""
        changes = 0
        
        # Check basic fields
        if old_version.title != new_version.title:
            changes += 1
        if old_version.content != new_version.content:
            changes += 2  # Content changes are more significant
        if old_version.metadata != new_version.metadata:
            changes += 1
        if old_version.prediction_status != new_version.prediction_status:
            changes += 1
        
        return changes
    
    @staticmethod
    def _generate_field_diffs(
        from_version: DocumentVersion,
        to_version: DocumentVersion
    ) -> List[FieldDiff]:
        """Generate field-level diffs between versions."""
        
        diffs = []
        
        # Title changes
        if from_version.title != to_version.title:
            diffs.append(FieldDiff(
                field_path="title",
                field_type="text",
                old_value=from_version.title,
                new_value=to_version.title,
                change_type="modified",
                confidence=1.0
            ))
        
        # Content changes (simplified)
        if from_version.content != to_version.content:
            diffs.append(FieldDiff(
                field_path="content",
                field_type="text",
                old_value=from_version.content[:100] + "..." if from_version.content else None,
                new_value=to_version.content[:100] + "..." if to_version.content else None,
                change_type="modified",
                confidence=1.0
            ))
        
        # Metadata changes
        old_meta = from_version.metadata or {}
        new_meta = to_version.metadata or {}
        
        all_keys = set(old_meta.keys()) | set(new_meta.keys())
        for key in all_keys:
            old_val = old_meta.get(key)
            new_val = new_meta.get(key)
            
            if old_val != new_val:
                change_type = "added" if key not in old_meta else "removed" if key not in new_meta else "modified"
                diffs.append(FieldDiff(
                    field_path=f"metadata.{key}",
                    field_type="metadata",
                    old_value=old_val,
                    new_value=new_val,
                    change_type=change_type,
                    confidence=1.0
                ))
        
        return diffs
    
    @staticmethod
    def _generate_content_diff(
        old_content: str,
        new_content: str,
        diff_format: str = "unified"
    ) -> ContentDiff:
        """Generate content diff between two text strings."""
        
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        if diff_format == "unified":
            diff_lines = list(difflib.unified_diff(
                old_lines, new_lines,
                fromfile="old", tofile="new",
                lineterm=""
            ))
            diff_content = "\n".join(diff_lines)
        elif diff_format == "side_by_side":
            # Simplified side-by-side
            diff_content = "Side-by-side diff not implemented"
        else:  # json
            diff_content = json.dumps({
                "old_lines": old_lines,
                "new_lines": new_lines
            })
        
        # Count changes
        additions = len([line for line in diff_lines if line.startswith("+")])
        deletions = len([line for line in diff_lines if line.startswith("-")])
        
        return ContentDiff(
            diff_format=diff_format,
            diff_content=diff_content,
            additions_count=additions,
            deletions_count=deletions,
            modifications_count=0,  # Would need more sophisticated analysis
            context_lines=3
        )
    
    @staticmethod
    def _generate_metadata_diff(old_meta: Dict[str, Any], new_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata differences."""
        changes = {}
        
        all_keys = set(old_meta.keys()) | set(new_meta.keys())
        for key in all_keys:
            old_val = old_meta.get(key)
            new_val = new_meta.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val,
                    "change_type": "added" if key not in old_meta else "removed" if key not in new_meta else "modified"
                }
        
        return changes
    
    @staticmethod
    def _generate_diff_summary(field_diffs: List[FieldDiff], content_diff: ContentDiff = None) -> str:
        """Generate human-readable diff summary."""
        if not field_diffs and not content_diff:
            return "No changes detected"
        
        summary_parts = []
        
        if field_diffs:
            field_changes = len(field_diffs)
            summary_parts.append(f"{field_changes} field{'s' if field_changes != 1 else ''} changed")
        
        if content_diff and (content_diff.additions_count or content_diff.deletions_count):
            summary_parts.append(
                f"{content_diff.additions_count} additions, {content_diff.deletions_count} deletions"
            )
        
        return "; ".join(summary_parts)
    
    @staticmethod
    def _build_diff_response(
        existing_diff: DocumentVersionDiff,
        comparison_request: VersionComparisonRequest
    ) -> VersionDiffResponse:
        """Build diff response from cached data."""
        
        field_diffs = []
        if existing_diff.field_diffs and "diffs" in existing_diff.field_diffs:
            field_diffs = [FieldDiff(**diff) for diff in existing_diff.field_diffs["diffs"]]
        
        content_diff = None
        if existing_diff.content_diff and comparison_request.include_content_diff:
            content_diff = ContentDiff(
                diff_format="unified",
                diff_content=existing_diff.content_diff,
                additions_count=existing_diff.additions_count,
                deletions_count=existing_diff.deletions_count,
                modifications_count=existing_diff.modifications_count
            )
        
        return VersionDiffResponse(
            document_id=existing_diff.document_id,
            from_version=existing_diff.from_version,
            to_version=existing_diff.to_version,
            field_diffs=field_diffs,
            content_diff=content_diff,
            metadata_changes={},
            total_changes=existing_diff.modifications_count,
            significant_changes=existing_diff.modifications_count,
            diff_summary=existing_diff.diff_summary or "Cached diff",
            generated_at=existing_diff.created_at,
            generation_method="cached"
        )
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        document_id: int,
        organization_id: int,
        user_id: int,
        event_type: AuditEventType,
        description: str,
        before_data: Dict[str, Any] = None,
        after_data: Dict[str, Any] = None,
        field_changes: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ):
        """Log an audit event."""
        
        audit_event = DocumentAuditEvent(
            document_id=document_id,
            event_type=event_type,
            event_description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            before_data=before_data or {},
            after_data=after_data or {},
            field_changes=field_changes or {},
            metadata=metadata or {},
            organization_id=organization_id
        )
        
        db.add(audit_event)
        db.commit()
    
    @staticmethod
    def _log_share_access(
        db: Session,
        secure_share_id: int,
        access_type: str,
        ip_address: str = None,
        user_agent: str = None,
        authenticated_user_id: int = None,
        success: bool = True,
        failure_reason: str = None
    ):
        """Log access to a secure share."""
        
        access_log = DocumentShareAccessLog(
            secure_share_id=secure_share_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
            authenticated_user_id=authenticated_user_id,
            success=success,
            failure_reason=failure_reason
        )
        
        db.add(access_log)
        db.commit()
