"""
Phase 11: Frontend Sync Service Layer
Provides business logic for frontend API integration
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from models.user import User, Organization, UserStatus
from models.document import Document, DocumentStatus
from schemas.frontend.user_profile import UserProfileResponse, UserStats, UserPreferences
from schemas.frontend.documents import DocumentListResponse, DocumentListItem, DocumentFilter
from schemas.frontend.dashboard import DashboardStatsResponse, DashboardStats, DashboardWidget
from schemas.frontend.forms import FormMetadataResponse, FormSection, FormFieldResponse
from schemas.frontend.notifications import NotificationFeedResponse, NotificationItemResponse


class FrontendSyncService:
    """Service for handling frontend API operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_profile_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user profile data."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get user statistics
        stats = self._get_user_stats(user_id)
        
        # Get user preferences (mock for now)
        preferences = UserPreferences(
            theme="light",
            timezone="UTC",
            language="en",
            email_notifications=True,
            push_notifications=False,
            dashboard_layout="grid"
        )
        
        return {
            "id": user.id,
            "email": user.email,
            "first_name": "John",  # Mock data - extend User model later
            "last_name": "Doe",
            "full_name": "John Doe",
            "avatar_url": None,
            "role": user.role.value,
            "organization_id": user.organization_id,
            "organization_name": user.organization.name if user.organization else None,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "stats": stats,
            "preferences": preferences
        }
    
    def _get_user_stats(self, user_id: int) -> UserStats:
        """Calculate user statistics."""
        # Get document statistics
        documents_created = self.db.query(func.count(Document.id))\
            .filter(Document.created_by_id == user_id)\
            .scalar() or 0
            
        documents_edited = self.db.query(func.count(Document.id))\
            .filter(Document.edited_by_id == user_id)\
            .scalar() or 0
        
        # Mock additional stats
        return UserStats(
            login_count=0,  # From user.login_count if available
            documents_created=documents_created,
            documents_edited=documents_edited,
            cases_created=0,  # Add Case model integration later
            total_activity_score=documents_created + documents_edited
        )
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Update allowed fields (extend as needed)
        if "email" in profile_data:
            user.email = profile_data["email"]
        
        self.db.commit()
        return self.get_user_profile_data(user_id)
    
    def get_documents_list(self, user_id: int, filters: DocumentFilter, 
                          page: int = 1, limit: int = 20) -> DocumentListResponse:
        """Get paginated documents list with filtering."""
        query = self.db.query(Document)\
            .filter(Document.created_by_id == user_id)
        
        # Apply filters
        if filters.status:
            query = query.filter(Document.status == filters.status)
        
        if filters.document_type:
            query = query.filter(Document.document_type == filters.document_type)
        
        if filters.search:
            query = query.filter(
                func.lower(Document.title).contains(filters.search.lower())
            )
        
        if filters.date_from:
            query = query.filter(Document.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Document.created_at <= filters.date_to)
        
        # Pagination
        total = query.count()
        offset = (page - 1) * limit
        documents = query.order_by(desc(Document.updated_at))\
            .offset(offset).limit(limit).all()
        
        # Convert to response format
        items = [self._document_to_list_item(doc) for doc in documents]
        
        return DocumentListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit,
            has_next=page * limit < total,
            has_previous=page > 1,
            total_size_bytes=sum(item.size_bytes for item in items)
        )
    
    def _document_to_list_item(self, document) -> DocumentListItem:
        """Convert Document model to DocumentListItem."""
        return DocumentListItem(
            id=document.id,
            title=document.title,
            document_type=document.document_type or "unknown",
            status=document.status.value,
            created_at=document.created_at,
            updated_at=document.updated_at,
            created_by_name="User",  # Extend with actual user name
            size_bytes=0,  # Add size field to Document model
            version=1,  # Add version field to Document model
            is_shared=False,  # Add sharing logic
            has_comments=False,  # Add comments integration
            tags=[]  # Add tags integration
        )
    
    def get_dashboard_stats(self, user_id: int) -> DashboardStatsResponse:
        """Get dashboard statistics for user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Calculate basic stats
        total_documents = self.db.query(func.count(Document.id))\
            .filter(Document.created_by_id == user_id).scalar() or 0
            
        recent_activity = self.db.query(func.count(Document.id))\
            .filter(
                and_(
                    Document.created_by_id == user_id,
                    Document.updated_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).scalar() or 0
        
        stats = DashboardStats(
            total_documents=total_documents,
            total_cases=0,  # Add Case model integration
            active_cases=0,
            pending_tasks=0,
            recent_activity=recent_activity,
            storage_used_mb=0.0,  # Add storage calculation
            storage_limit_mb=1000.0
        )
        
        # Mock widgets for now
        widgets = [
            DashboardWidget(
                id="recent_documents",
                type="list",
                title="Recent Documents",
                data={
                    "items": [
                        {"title": "Contract Draft", "date": datetime.utcnow().isoformat()},
                        {"title": "Client Agreement", "date": (datetime.utcnow() - timedelta(days=1)).isoformat()}
                    ]
                },
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                is_visible=True,
                last_updated=datetime.utcnow()
            )
        ]
        
        return DashboardStatsResponse(
            stats=stats,
            widgets=widgets,
            last_updated=datetime.utcnow()
        )
    
    def get_form_metadata(self, form_id: str, user_id: int) -> FormMetadataResponse:
        """Get form metadata and structure."""
        # Mock form data for now - integrate with actual form system later
        sections = [
            FormSection(
                id="section_basic",
                title="Basic Information",
                description="Essential client and case details",
                order=1,
                collapsible=False,
                required_fields_count=3,
                total_fields_count=5
            )
        ]
        
        fields = [
            FormFieldResponse(
                id="field_client_name",
                name="client_name",
                label="Client Name",
                field_type="text",
                placeholder="Enter client name",
                help_text="Full legal name of the client",
                validation={
                    "required": True,
                    "min_length": 2,
                    "max_length": 100
                },
                order=1,
                section="section_basic",
                column_span=6,
                jurisdiction_specific=False
            )
        ]
        
        return FormMetadataResponse(
            id=form_id,
            title="Client Intake Form",
            description="Standard client intake and case setup form",
            version="1.0",
            jurisdiction="US",
            practice_area="general",
            document_type="intake",
            complexity_level="medium",
            sections=sections,
            fields=fields,
            estimated_time_minutes=15,
            required_fields_count=3,
            total_fields_count=5,
            completion_rate=0.0
        )
    
    def get_notifications_feed(self, user_id: int, page: int = 1, 
                             limit: int = 20) -> NotificationFeedResponse:
        """Get user notifications feed."""
        # Mock notifications for now - integrate with actual notification system
        notifications = [
            NotificationItemResponse(
                id="notif_1",
                type="document_shared",
                title="Document Shared",
                message="John Doe shared 'Contract Draft.pdf' with you",
                is_read=False,
                priority="normal",
                created_at=datetime.utcnow() - timedelta(hours=2),
                action_url="/documents/123",
                metadata={
                    "document_id": "123",
                    "shared_by": "John Doe"
                }
            ),
            NotificationItemResponse(
                id="notif_2",
                type="system",
                title="System Maintenance",
                message="Scheduled maintenance tonight from 2-4 AM EST",
                is_read=True,
                priority="low",
                created_at=datetime.utcnow() - timedelta(days=1),
                metadata={}
            )
        ]
        
        return NotificationFeedResponse(
            notifications=notifications,
            total=len(notifications),
            unread_count=sum(1 for n in notifications if not n.is_read),
            page=page,
            limit=limit,
            has_next=False
        )
