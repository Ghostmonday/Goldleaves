# routers/document_collaboration.py

"""Phase 6: Document collaboration router for version control, diffing, and secure sharing."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime

from core.db.session import get_db
from core.dependencies import get_current_user
from core.security import verify_api_key, require_permission
from models.user import User
from models.document import AuditEventType, SecureSharePermission
from services.document_collaboration import DocumentCollaborationService
from schemas.document.collaboration import (
    VersionComparisonRequest, VersionDiffResponse, VersionHistoryResponse,
    SecureShareCreate, SecureShareResponse, ShareAccessRequest, ShareAccessResponse,
    DocumentAuditTrailResponse, CollaborationStats
)
from core.exceptions import NotFoundError, ValidationError, PermissionError
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Document Collaboration"])
security = HTTPBearer()


# Version History and Comparison Endpoints

@router.get("/{document_id}/versions", response_model=VersionHistoryResponse)
async def get_document_version_history(
    document_id: int,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of versions to return"),
    include_metadata: bool = Query(True, description="Include metadata in version entries"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive version history for a document.
    
    This endpoint provides detailed version history including:
    - Version metadata and change summaries
    - User information for each change
    - Prediction scores and status progression
    - Change counts between versions
    - Major version identification
    """
    try:
        # Check document access permission
        await require_permission(db, current_user.id, document_id, "read")
        
        version_history = DocumentCollaborationService.get_version_history(
            db=db,
            document_id=document_id,
            organization_id=current_user.organization_id,
            limit=limit,
            include_metadata=include_metadata
        )
        
        logger.info(
            f"Retrieved version history for document {document_id} "
            f"by user {current_user.id} ({len(version_history.versions)} versions)"
        )
        
        return version_history
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving version history for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{document_id}/compare", response_model=VersionDiffResponse)
async def compare_document_versions(
    document_id: int,
    comparison_request: VersionComparisonRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare two versions of a document with detailed field-level diffing.
    
    This endpoint provides:
    - Field-by-field difference analysis
    - Content diffing in multiple formats
    - Metadata change tracking
    - Statistical change summaries
    - Cached diff results for performance
    """
    try:
        # Check document access permission
        await require_permission(db, current_user.id, document_id, "read")
        
        # Get client IP for audit logging
        client_ip = request.client.host if request.client else None
        
        version_diff = DocumentCollaborationService.compare_versions(
            db=db,
            document_id=document_id,
            comparison_request=comparison_request,
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        logger.info(
            f"Compared versions {comparison_request.from_version} to "
            f"{comparison_request.to_version} for document {document_id} "
            f"by user {current_user.id} ({version_diff.total_changes} changes)"
        )
        
        return version_diff
        
    except NotFoundError as e:
        logger.warning(f"Version comparison failed for document {document_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid version comparison request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing versions for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Secure Sharing Endpoints

@router.post("/{document_id}/share", response_model=SecureShareResponse)
async def create_secure_document_share(
    document_id: int,
    share_data: SecureShareCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a secure shareable link for a document.
    
    This endpoint provides:
    - Secure slug-based sharing URLs
    - Granular permission controls
    - Access limitations (views, downloads, time)
    - IP whitelisting and access codes
    - Comprehensive access tracking
    """
    try:
        # Check document share permission
        await require_permission(db, current_user.id, document_id, "share")
        
        # Validate expiration date
        if share_data.expires_at and share_data.expires_at <= datetime.utcnow():
            raise ValidationError("Expiration date must be in the future")
        
        # Get base URL for share links
        base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost')}"
        
        secure_share = DocumentCollaborationService.create_secure_share(
            db=db,
            document_id=document_id,
            share_data=share_data,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            base_url=base_url
        )
        
        # Send notification email if requested (background task)
        if share_data.recipient_email and share_data.notify_on_access:
            background_tasks.add_task(
                send_share_notification_email,
                share_data.recipient_email,
                secure_share.share_url,
                current_user.full_name,
                share_data.recipient_name
            )
        
        logger.info(
            f"Created secure share {secure_share.id} for document {document_id} "
            f"by user {current_user.id} (recipient: {share_data.recipient_email or 'anonymous'})"
        )
        
        return secure_share
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for sharing by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid share request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for sharing document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating secure share for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/share/{share_slug}", response_model=ShareAccessResponse)
async def access_secure_document_share(
    share_slug: str,
    request: Request,
    access_code: Optional[str] = Query(None, description="Access code if required"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Access a secure document share using a share slug.
    
    This endpoint provides:
    - Secure document access validation
    - IP and access code verification
    - View/download tracking
    - Watermarking support
    - Audit trail logging
    """
    try:
        # Build access request
        access_request = ShareAccessRequest(access_code=access_code)
        
        # Get client information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        authenticated_user_id = current_user.id if current_user else None
        
        share_access = DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=share_slug,
            access_request=access_request,
            ip_address=client_ip,
            user_agent=user_agent,
            authenticated_user_id=authenticated_user_id
        )
        
        logger.info(
            f"Accessed secure share {share_slug} from IP {client_ip} "
            f"(authenticated: {authenticated_user_id is not None})"
        )
        
        return share_access
        
    except NotFoundError as e:
        logger.warning(f"Share {share_slug} not found")
        raise HTTPException(status_code=404, detail="Share not found or has expired")
    except ValidationError as e:
        logger.warning(f"Invalid access attempt for share {share_slug}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for share {share_slug}: {e}")
        raise HTTPException(status_code=401, detail="Authentication required")
    except Exception as e:
        logger.error(f"Error accessing secure share {share_slug}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/share/{share_slug}/download")
async def download_shared_document(
    share_slug: str,
    request: Request,
    access_code: Optional[str] = Query(None, description="Access code if required"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a document through a secure share.
    
    This endpoint provides:
    - Secure download authorization
    - Download count tracking
    - Watermarking application
    - Access audit logging
    """
    try:
        # This would be implemented with actual file serving logic
        # For now, return a placeholder response
        
        # First validate access (similar to access_secure_document_share)
        access_request = ShareAccessRequest(access_code=access_code)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        authenticated_user_id = current_user.id if current_user else None
        
        # Validate download permission
        share_access = DocumentCollaborationService.access_secure_share(
            db=db,
            share_slug=share_slug,
            access_request=access_request,
            ip_address=client_ip,
            user_agent=user_agent,
            authenticated_user_id=authenticated_user_id
        )
        
        if not share_access.download_url:
            raise PermissionError("Download not permitted")
        
        # Log download event (would increment download count in actual implementation)
        logger.info(
            f"Downloaded document via secure share {share_slug} from IP {client_ip}"
        )
        
        # In a real implementation, this would return a FileResponse or streamed content
        return {"message": "Download authorized", "expires_at": share_access.download_expires_at}
        
    except (NotFoundError, ValidationError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading from secure share {share_slug}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/shares/{share_id}")
async def revoke_secure_share(
    share_id: int,
    revocation_reason: Optional[str] = Query(None, description="Reason for revocation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a secure document share.
    
    This endpoint provides:
    - Share revocation capabilities
    - Audit trail logging
    - Access prevention
    """
    try:
        success = DocumentCollaborationService.revoke_secure_share(
            db=db,
            share_id=share_id,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            revocation_reason=revocation_reason
        )
        
        logger.info(
            f"Revoked secure share {share_id} by user {current_user.id} "
            f"(reason: {revocation_reason or 'None provided'})"
        )
        
        return {"success": success, "message": "Share revoked successfully"}
        
    except NotFoundError as e:
        logger.warning(f"Share {share_id} not found for revocation by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error revoking secure share {share_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Audit Trail Endpoints

@router.get("/{document_id}/audit", response_model=DocumentAuditTrailResponse)
async def get_document_audit_trail(
    document_id: int,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events to return"),
    event_types: Optional[List[str]] = Query(None, description="Filter by event types"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive audit trail for a document.
    
    This endpoint provides:
    - Complete event history
    - User activity tracking
    - Compliance metrics
    - Event type filtering
    - Statistical summaries
    """
    try:
        # Check document audit permission
        await require_permission(db, current_user.id, document_id, "audit")
        
        # Parse event types if provided
        parsed_event_types = None
        if event_types:
            try:
                parsed_event_types = [AuditEventType(et) for et in event_types]
            except ValueError as e:
                raise ValidationError(f"Invalid event type: {e}")
        
        audit_trail = DocumentCollaborationService.get_document_audit_trail(
            db=db,
            document_id=document_id,
            organization_id=current_user.organization_id,
            limit=limit,
            event_types=parsed_event_types
        )
        
        logger.info(
            f"Retrieved audit trail for document {document_id} by user {current_user.id} "
            f"({audit_trail.total_events} events)"
        )
        
        return audit_trail
        
    except NotFoundError as e:
        logger.warning(f"Document {document_id} not found for audit by user {current_user.id}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Invalid audit trail request for document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for audit access to document {document_id} by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving audit trail for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Organization Statistics Endpoints

@router.get("/collaboration/stats", response_model=CollaborationStats)
async def get_collaboration_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization-wide collaboration statistics.
    
    This endpoint provides:
    - Document and version counts
    - Sharing activity metrics
    - Collaboration patterns
    - Recent activity summaries
    - Most active documents and users
    """
    try:
        # Check organization admin permission
        if not current_user.is_admin:
            raise PermissionError("Organization admin access required")
        
        collaboration_stats = DocumentCollaborationService.get_collaboration_stats(
            db=db,
            organization_id=current_user.organization_id
        )
        
        logger.info(
            f"Retrieved collaboration stats for organization {current_user.organization_id} "
            f"by user {current_user.id}"
        )
        
        return collaboration_stats
        
    except PermissionError as e:
        logger.warning(f"Permission denied for collaboration stats by user {current_user.id}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving collaboration stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Helper functions

async def send_share_notification_email(
    recipient_email: str,
    share_url: str,
    sender_name: str,
    recipient_name: str = None
):
    """Send notification email for document share (background task)."""
    try:
        # This would integrate with your email service
        # For now, just log the action
        logger.info(
            f"Would send share notification to {recipient_email} "
            f"from {sender_name} with URL {share_url}"
        )
        
        # Example email content:
        # Subject: "{sender_name} shared a document with you"
        # Body: "Hi {recipient_name}, {sender_name} has shared a document with you. 
        #        Access it here: {share_url}"
        
    except Exception as e:
        logger.error(f"Failed to send share notification email: {e}")


# Additional utility endpoints

@router.get("/{document_id}/share-links")
async def list_document_shares(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active shares for a document."""
    try:
        await require_permission(db, current_user.id, document_id, "share")
        
        # Query active shares for the document
        from models.document import DocumentSecureShare
        shares = db.query(DocumentSecureShare).filter(
            DocumentSecureShare.document_id == document_id,
            DocumentSecureShare.organization_id == current_user.organization_id,
            DocumentSecureShare.is_active == True
        ).all()
        
        share_list = []
        for share in shares:
            share_list.append({
                "id": share.id,
                "share_slug": share.share_slug,
                "recipient_email": share.recipient_email,
                "permission_level": share.permission_level.value,
                "created_at": share.created_at,
                "expires_at": share.expires_at,
                "view_count": share.view_count,
                "is_expired": share.is_expired()
            })
        
        return {"shares": share_list, "total": len(share_list)}
        
    except (NotFoundError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing shares for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recent-activity")
async def get_recent_collaboration_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent collaboration activity across the organization."""
    try:
        from models.document import DocumentAuditEvent
        from sqlalchemy import desc
        
        # Get recent audit events
        recent_events = db.query(DocumentAuditEvent).filter(
            DocumentAuditEvent.organization_id == current_user.organization_id
        ).order_by(desc(DocumentAuditEvent.created_at)).limit(limit).all()
        
        activity_list = []
        for event in recent_events:
            activity_list.append({
                "event_type": event.event_type.value,
                "description": event.event_description,
                "document_id": event.document_id,
                "user_id": event.user_id,
                "created_at": event.created_at
            })
        
        return {"recent_activity": activity_list, "total": len(activity_list)}
        
    except Exception as e:
        logger.error(f"Error retrieving recent collaboration activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
