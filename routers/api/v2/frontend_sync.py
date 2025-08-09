# routers/api/v2/frontend_sync.py
"""
Frontend-facing API v2 router with optimized endpoints for UI consumption.
Implements aggregated, simplified responses with proper caching and pagination.
"""

import json
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from core.database import get_db

# Import database and dependencies
from core.dependencies import get_current_active_user
from models.user import User
from schemas.frontend.dashboard import DashboardStatsResponse
from schemas.frontend.documents import (
    DocumentFilter,
    DocumentListResponse,
    DocumentStatus,
    DocumentType,
)
from schemas.frontend.forms import FormMetadataResponse
from schemas.frontend.notifications import NotificationFeedResponse

# Import schemas
from schemas.frontend.user_profile import ProfileUpdateRequest, UserProfileResponse

# Import service
from services.frontend_sync import FrontendSyncService

# Initialize router
router = APIRouter(
    prefix="/api/v2",
    tags=["frontend"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal server error"}
    }
)


def create_error_response(error: str, status_code: int = 400) -> JSONResponse:
    """Create standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error,
            "data": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def create_success_response(data: Any, cache_seconds: Optional[int] = None) -> JSONResponse:
    """Create standardized success response with optional caching."""
    headers = {}
    if cache_seconds:
        headers["Cache-Control"] = f"public, max-age={cache_seconds}"
    
    return JSONResponse(
        content={
            "success": True,
            "error": None,
            "data": json.loads(data.model_dump_json()) if hasattr(data, 'model_dump_json') else data,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=headers
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    include_stats: bool = Query(True, description="Include usage statistics"),
    include_preferences: bool = Query(True, description="Include UI preferences")
) -> JSONResponse:
    """
    Get current user's profile with UI-optimized data.
    
    Returns comprehensive user profile including preferences, permissions,
    organization info, and usage statistics.
    """
    try:
        service = FrontendSyncService(db)
        profile_data = service.get_user_profile_data(current_user.id)
        
        # Add capabilities based on user role and permissions
        profile_data["capabilities"] = {
            "can_create_documents": True,
            "can_delete_documents": getattr(current_user, 'is_admin', False),
            "can_manage_users": getattr(current_user, 'is_admin', False),
            "can_access_billing": getattr(current_user, 'is_admin', False),
            "can_export_data": True,
            "can_use_ai_features": True,
            "can_create_templates": getattr(current_user, 'is_admin', False),
            "is_admin": getattr(current_user, 'is_admin', False),
            "is_verified": getattr(current_user, 'is_verified', False)
        }
        
        response = UserProfileResponse(**profile_data)
        
        # Cache for 5 minutes
        return create_success_response(response, cache_seconds=300)
        
    except ValueError as e:
        return create_error_response(str(e), 404)
    except Exception as e:
        return create_error_response(f"Failed to load profile: {str(e)}", 500)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> JSONResponse:
    """Update user profile information."""
    try:
        service = FrontendSyncService(db)
        
        # Convert request to dict for service
        update_data = profile_update.dict(exclude_unset=True)
        
        # Update profile through service
        updated_profile = service.update_user_profile(current_user.id, update_data)
        
        response = UserProfileResponse(**updated_profile)
        return create_success_response(response)
        
    except ValueError as e:
        return create_error_response(str(e), 404)
    except Exception as e:
        return create_error_response(f"Failed to update profile: {str(e)}", 500)


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Filters
    search: Optional[str] = Query(None, description="Search query"),
    type: Optional[List[DocumentType]] = Query(None, description="Filter by document types"),
    status: Optional[List[DocumentStatus]] = Query(None, description="Filter by status"),
    created_by: Optional[List[str]] = Query(None, description="Filter by creator IDs"),
    tags: Optional[List[str]] = Query(None, description="Filter by tag IDs"),
    case_id: Optional[str] = Query(None, description="Filter by case"),
    client_id: Optional[str] = Query(None, description="Filter by client"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites only"),
    shared_with_me: Optional[bool] = Query(None, description="Filter shared documents"),
    
    # Sorting
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> JSONResponse:
    """
    Get paginated document list with filters and sorting.
    
    Supports advanced filtering, sorting, pagination, and sparse fieldsets
    for optimal performance.
    """
    try:
        service = FrontendSyncService(db)
        
        # Build filter object
        filters = DocumentFilter(
            search=search,
            document_type=type[0] if type else None,  # Convert to single type for now
            status=status[0] if status else None,  # Convert to single status for now
            case_id=case_id,
            client_id=client_id,
            is_favorite=is_favorite,
            shared_with_me=shared_with_me
        )
        
        # Get documents through service
        response = service.get_documents_list(
            user_id=current_user.id,
            filters=filters,
            page=page,
            limit=per_page
        )
        
        return create_success_response(response, cache_seconds=60)
        
    except Exception as e:
        return create_error_response(f"Failed to load documents: {str(e)}", 500)


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    date_range: str = Query("30d", description="Date range for stats (7d, 30d, 90d)")
) -> JSONResponse:
    """Get dashboard statistics and overview data."""
    try:
        # Get dashboard stats through service
        db = next(get_db())
        service = FrontendSyncService(db)
        
        response = service.get_dashboard_stats(
            user_id=current_user.id,
            date_range=date_range
        )
        
        return create_success_response(response, cache_seconds=300)
        
    except Exception as e:
        return create_error_response(f"Failed to load dashboard: {str(e)}", 500)


@router.get("/forms/{form_id}", response_model=FormMetadataResponse)
async def get_form_metadata(
    form_id: str,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """Get form metadata and structure."""
    try:
        # Get form metadata through service
        db = next(get_db())
        service = FrontendSyncService(db)
        
        response = service.get_form_metadata(
            form_id=form_id,
            user_id=current_user.id
        )
        
        return create_success_response(response, cache_seconds=600)
        
    except Exception as e:
        return create_error_response(f"Failed to load form: {str(e)}", 500)


@router.get("/notifications", response_model=NotificationFeedResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """Get user notifications with pagination."""
    try:
        # Get notifications through service
        db = next(get_db())
        service = FrontendSyncService(db)
        
        response = service.get_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            cursor=cursor
        )
        
        # No caching for notifications
        return create_success_response(response)
        
    except Exception as e:
        return create_error_response(f"Failed to load notifications: {str(e)}", 500)


# Health check endpoint
@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return create_success_response({
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.utcnow().isoformat()
    })


# Register the router with the contract system
def _register_frontend_sync_router():
    """Register the Phase 11 frontend sync router."""
    try:
        from ...contract import RouterContract, RouterTags, register_router
        
        frontend_sync_contract = RouterContract(
            name="frontend_sync",
            router=router,
            prefix="/api/v2",
            tags=[RouterTags.USERS, RouterTags.DOCUMENTS],
            dependencies=[],
            metadata={
                "description": "Phase 11: Frontend API Integration & Sync Layer",
                "version": "1.0.0",
                "features": [
                    "Frontend-optimized response schemas",
                    "Unified API layer with caching",
                    "User profile and preferences management", 
                    "Document listing with advanced filtering",
                    "Dashboard statistics and widgets",
                    "Form metadata and structure",
                    "Real-time notifications feed"
                ]
            }
        )
        register_router("frontend_sync", frontend_sync_contract)
        
    except ImportError:
        # Contract system not available
        pass

# Auto-register on import
_register_frontend_sync_router()
