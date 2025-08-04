# routers/api/v2/frontend_sync.py
"""
Frontend-facing API v2 router with optimized endpoints for UI consumption.
Implements aggregated, simplified responses with proper caching and pagination.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

# Import database and dependencies
from core.dependencies import get_current_active_user
from core.database import get_db
from models.user import User

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


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    include_stats: bool = Query(True, description="Include usage statistics"),
    include_preferences: bool = Query(True, description="Include UI preferences")
) -> JSONResponse:
    """Get current user's profile with UI-optimized data."""
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
        }
        
        return create_success_response(profile_data, cache_seconds=300)
        
    except Exception as e:
        return create_error_response(f"Failed to fetch profile: {str(e)}", 500)


@router.get("/documents")
async def get_documents(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status")
) -> JSONResponse:
    """Get paginated list of documents for the current user."""
    try:
        service = FrontendSyncService(db)
        documents_data = service.get_user_documents(
            current_user.id,
            page=page,
            per_page=per_page,
            search=search,
            document_type=document_type,
            status=status
        )
        
        return create_success_response(documents_data, cache_seconds=60)
        
    except Exception as e:
        return create_error_response(f"Failed to fetch documents: {str(e)}", 500)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    period: str = Query("30d", description="Stats period (7d, 30d, 90d)")
) -> JSONResponse:
    """Get dashboard statistics for the current user."""
    try:
        service = FrontendSyncService(db)
        stats_data = service.get_dashboard_stats(current_user.id, period)
        
        return create_success_response(stats_data, cache_seconds=300)
        
    except Exception as e:
        return create_error_response(f"Failed to fetch stats: {str(e)}", 500)


@router.get("/forms/metadata")
async def get_form_metadata(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    form_type: Optional[str] = Query(None, description="Filter by form type")
) -> JSONResponse:
    """Get available form templates and metadata."""
    try:
        service = FrontendSyncService(db)
        metadata = service.get_form_metadata(form_type)
        
        return create_success_response(metadata, cache_seconds=600)
        
    except Exception as e:
        return create_error_response(f"Failed to fetch form metadata: {str(e)}", 500)


@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    unread_only: bool = Query(False, description="Show only unread notifications")
) -> JSONResponse:
    """Get user notifications feed."""
    try:
        service = FrontendSyncService(db)
        notifications = service.get_user_notifications(
            current_user.id,
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )
        
        return create_success_response(notifications, cache_seconds=60)
        
    except Exception as e:
        return create_error_response(f"Failed to fetch notifications: {str(e)}", 500)


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring."""
    return create_success_response({
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "frontend_api": "enabled",
            "real_time": "enabled"
        }
    })
