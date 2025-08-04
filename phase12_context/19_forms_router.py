# routers/forms.py
"""
Form management router for Phase 12 crowdsourcing.
Handles form uploads, reviews, and contributor management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from core.dependencies import get_db, get_current_active_user, get_admin_user
from services.form_registry import FormRegistryService
from services.feedback_service import FeedbackService
from models.user import User

# Initialize router
router = APIRouter(
    prefix="/api/v2/forms",
    tags=["forms"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"}
    }
)


@router.post("/upload")
async def upload_form(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    form_type: str = Form(...),
    contributor_type: str = Form("crowdsource"),
    metadata: str = Form("{}"),  # JSON string
    tags: str = Form("[]"),      # JSON string array
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Upload a new form to the registry."""
    try:
        # Validate file type
        if not file.content_type.startswith(('application/pdf', 'application/msword')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Read file data
        file_data = await file.read()
        
        # Parse JSON fields
        import json
        try:
            metadata_dict = json.loads(metadata)
            tags_list = json.loads(tags)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in metadata or tags")
        
        # Create form data object
        form_data = {
            "title": title,
            "description": description,
            "form_type": form_type,
            "contributor_type": contributor_type,
            "metadata": metadata_dict,
            "tags": tags_list
        }
        
        # Upload form
        service = FormRegistryService(db)
        result = await service.upload_form(form_data, file_data, str(current_user.id))
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Form uploaded successfully",
                "data": result
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Form upload failed")


@router.get("/")
async def list_forms(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    form_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    contributor_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get paginated list of forms."""
    try:
        # Mock implementation
        forms = []
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "forms": forms,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": len(forms),
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False
                }
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch forms")


@router.get("/{form_id}")
async def get_form_details(
    form_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get detailed information about a specific form."""
    try:
        # Mock implementation
        form_details = {
            "form_id": form_id,
            "title": "Sample Form",
            "status": "approved",
            "contributor_type": "crowdsource",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return JSONResponse(content={
            "success": True,
            "data": form_details
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch form details")


@router.post("/{form_id}/review")
async def review_form(
    form_id: str,
    review_data: Dict[str, Any],
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Review a submitted form (admin only)."""
    try:
        service = FormRegistryService(db)
        result = await service.review_form(form_id, review_data, str(current_user.id))
        
        return JSONResponse(content={
            "success": True,
            "message": "Form review completed",
            "data": result
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Form review failed")


@router.get("/stats/overview")
async def get_form_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get form registry statistics."""
    try:
        service = FormRegistryService(db)
        stats = await service.get_form_stats()
        
        return JSONResponse(content={
            "success": True,
            "data": stats
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/contributor/{contributor_id}/rewards")
async def get_contributor_rewards(
    contributor_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get contributor reward information."""
    try:
        # Check if user can access this contributor's data
        if str(current_user.id) != contributor_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        service = FormRegistryService(db)
        rewards = await service.get_contributor_rewards(contributor_id)
        
        return JSONResponse(content={
            "success": True,
            "data": rewards
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch rewards")


@router.post("/feedback")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Submit feedback about a form."""
    try:
        service = FeedbackService(db)
        result = await service.submit_feedback(
            feedback_data["form_id"],
            str(current_user.id),
            feedback_data
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Feedback submitted successfully",
            "data": result
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Feedback submission failed")


@router.get("/feedback/stats")
async def get_feedback_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get feedback statistics (admin only)."""
    try:
        service = FeedbackService(db)
        stats = await service.get_feedback_stats()
        
        return JSONResponse(content={
            "success": True,
            "data": stats
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch feedback statistics")


@router.get("/{form_id}/feedback")
async def get_form_feedback(
    form_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """Get feedback for a specific form (admin only)."""
    try:
        service = FeedbackService(db)
        feedback = await service.get_form_feedback(form_id)
        
        return JSONResponse(content={
            "success": True,
            "data": feedback
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch form feedback")
