"""
Phase 12: Form API Routes
FastAPI routes for form crowdsourcing system
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.dependencies import get_current_admin_user, get_current_user
from models.user import User
from schemas.forms import (
    ContributorRewardRequest,
    ContributorRewardStatus,
    ContributorType,
    FeedbackStatsResponse,
    FormDetailResponse,
    FormFeedbackRequest,
    FormFeedbackResponse,
    FormFilters,
    FormLanguage,
    FormListItem,
    FormReviewRequest,
    FormReviewResponse,
    FormSearchRequest,
    FormStatsResponse,
    FormStatus,
    FormType,
    FormUploadRequest,
    FormUploadResponse,
    PaginatedFormResponse,
)
from services.forms import FormService

router = APIRouter(prefix="/api/v1/forms", tags=["forms"])
security = HTTPBearer()


@router.post("/upload", response_model=FormUploadResponse)
async def upload_form(
    form_request: FormUploadRequest,
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new form for review.
    
    - **form_request**: Form metadata and structure
    - **file**: Optional form file (PDF, Word, etc.)
    - **current_user**: Authenticated user (contributor)
    """
    form_service = FormService(db)
    
    try:
        form = form_service.create_form(
            form_request=form_request,
            contributor_id=current_user.id,
            file_data=file
        )
        
        # Check for similar forms
        similar_forms = form_service._check_duplicates(form_request)
        is_potential_duplicate = len(similar_forms) > 0
        
        # Generate upload URL if file upload needed
        upload_url = None
        expires_at = None
        if file:
            # TODO: Generate presigned URL for file storage
            upload_url = f"/api/v1/forms/{form.form_id}/upload"
        
        return FormUploadResponse(
            form_id=form.form_id,
            title=form.title,
            status=form.status,
            contributor_id=form.contributor_id,
            upload_url=upload_url,
            expires_at=expires_at,
            similar_forms=[
                {
                    "form_id": f.form_id,
                    "title": f.title,
                    "similarity_score": 0.8  # TODO: Calculate actual similarity
                }
                for f in similar_forms[:3]
            ],
            is_potential_duplicate=is_potential_duplicate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading form: {str(e)}"
        )


@router.get("/search", response_model=PaginatedFormResponse)
async def search_forms(
    query: Optional[str] = Query(None, description="Search query"),
    form_type: Optional[FormType] = Query(None, description="Filter by form type"),
    form_status: Optional[FormStatus] = Query(None, description="Filter by status"),
    language: Optional[FormLanguage] = Query(None, description="Filter by language"),
    contributor_type: Optional[ContributorType] = Query(None, description="Filter by contributor type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    county: Optional[str] = Query(None, description="Filter by county"),
    form_number: Optional[str] = Query(None, description="Filter by form number"),
    is_featured: Optional[bool] = Query(None, description="Filter featured forms"),
    has_feedback: Optional[bool] = Query(None, description="Filter forms with feedback"),
    min_score: Optional[float] = Query(None, description="Minimum review score"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search and filter forms with pagination.
    
    - **query**: Text search across title, description, form number
    - **form_type**: Filter by specific form type
    - **form_status**: Filter by form status
    - **language**: Filter by form language
    - **state**: Filter by jurisdiction state
    - **sort_by**: Field to sort by (created_at, title, review_score, etc.)
    - **page**: Page number for pagination
    - **per_page**: Number of items per page
    """
    form_service = FormService(db)
    
    # Build filters
    filters = FormFilters(
        form_type=form_type,
        status=form_status,
        language=language,
        contributor_type=contributor_type,
        state=state,
        county=county,
        form_number=form_number,
        is_featured=is_featured,
        has_feedback=has_feedback,
        min_score=min_score
    )
    
    # Build search request
    search_request = FormSearchRequest(
        query=query,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )
    
    try:
        forms, pagination = form_service.search_forms(search_request)
        
        # Convert to list items
        form_items = []
        for form in forms:
            jurisdiction_display = "Unknown"
            if form.jurisdiction:
                jurisdiction_display = f"{form.jurisdiction.state}"
                if form.jurisdiction.county:
                    jurisdiction_display += f" - {form.jurisdiction.county}"
            
            form_items.append(FormListItem(
                form_id=form.form_id,
                title=form.title,
                form_number=form.form_number,
                form_type=form.form_type,
                status=form.status,
                contributor_type=form.contributor_type,
                contributor_name=form.contributor.full_name if form.contributor else None,
                language=form.language,
                jurisdiction_display=jurisdiction_display,
                version=form.version,
                created_at=form.created_at,
                reviewed_at=form.reviewed_at,
                review_score=form.review_score,
                download_count=form.download_count,
                is_featured=form.is_featured,
                is_current_version=form.is_current_version,
                has_feedback=form.feedback_count > 0
            ))
        
        return PaginatedFormResponse(
            forms=form_items,
            pagination=pagination,
            filters_applied=filters.dict(exclude_none=True),
            sort_by=sort_by,
            sort_order=sort_order
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching forms: {str(e)}"
        )


@router.get("/{form_id}", response_model=FormDetailResponse)
async def get_form_details(
    form_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific form.
    
    - **form_id**: Unique form identifier
    """
    form_service = FormService(db)
    
    try:
        form = form_service.get_form_details(
            form_id=form_id,
            user_id=current_user.id if current_user else None
        )
        
        # Build jurisdiction display
        jurisdiction_display = "Unknown"
        if form.jurisdiction:
            jurisdiction_display = f"{form.jurisdiction.state}"
            if form.jurisdiction.county:
                jurisdiction_display += f" - {form.jurisdiction.county}"
        
        # Build metadata
        metadata_dict = form.metadata or {}
        
        # Build file info
        file_info = {}
        if form.file_path:
            file_info = {
                'file_path': form.file_path,
                'file_size': form.file_size,
                'content_type': form.content_type,
                'page_count': form.page_count,
                'word_count': form.word_count
            }
        
        # Build field definitions
        fields = []
        for field in form.fields:
            fields.append({
                'field_name': field.field_name,
                'field_label': field.field_label,
                'field_type': field.field_type,
                'field_order': field.field_order,
                'is_required': field.is_required,
                'is_repeatable': field.is_repeatable,
                'max_length': field.max_length,
                'min_length': field.min_length,
                'section_name': field.section_name,
                'group_name': field.group_name,
                'validation_rules': field.validation_rules,
                'default_value': field.default_value,
                'placeholder_text': field.placeholder_text,
                'help_text': field.help_text,
                'ai_field_category': field.ai_field_category
            })
        
        return FormDetailResponse(
            form_id=form.form_id,
            title=form.title,
            description=form.description,
            form_number=form.form_number,
            form_type=form.form_type,
            status=form.status,
            contributor_type=form.contributor_type,
            contributor_id=form.contributor_id,
            contributor_name=form.contributor.full_name if form.contributor else None,
            contributor_tier=form.contributor.contributor_stats.contributor_tier if form.contributor and form.contributor.contributor_stats else None,
            metadata={
                'jurisdiction': {
                    'state': form.jurisdiction.state if form.jurisdiction else None,
                    'county': form.jurisdiction.county if form.jurisdiction else None,
                    'court_type': form.jurisdiction.court_type if form.jurisdiction else None
                },
                'form_number': form.form_number,
                'language': form.language.value,
                'effective_date': form.effective_date,
                'expiration_date': form.expiration_date,
                'version': form.version,
                **metadata_dict
            },
            tags=form.tags or [],
            fields=fields,
            file_info=file_info,
            download_url=f"/api/v1/forms/{form_id}/download" if form.file_path else None,
            reviewed_at=form.reviewed_at,
            reviewed_by=form.reviewed_by.full_name if form.reviewed_by else None,
            review_comments=form.review_comments,
            review_score=form.review_score,
            review_checklist=form.review_checklist,
            view_count=form.view_count,
            download_count=form.download_count,
            feedback_count=form.feedback_count,
            completeness_score=form.completeness_score,
            accuracy_verified=form.accuracy_verified,
            last_verified_date=form.last_verified_date,
            related_forms=[],  # TODO: Implement related forms logic
            available_versions=[],  # TODO: Implement version history
            available_languages=[form.language],  # TODO: Implement translations
            created_at=form.created_at,
            updated_at=form.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving form: {str(e)}"
        )


@router.post("/{form_id}/review", response_model=FormReviewResponse)
async def review_form(
    form_id: str,
    review_request: FormReviewRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Review a form (admin/reviewer only).
    
    - **form_id**: Form to review
    - **review_request**: Review decision and comments
    """
    form_service = FormService(db)
    
    try:
        form = form_service.review_form(
            form_id=form_id,
            review_request=review_request,
            reviewer_id=current_user.id
        )
        
        # Check if reward was granted
        reward_granted = None
        reward_details = None
        if form.status == FormStatus.APPROVED:
            # TODO: Get latest reward for this form
            reward_granted = True
            reward_details = {
                'reward_type': 'free_week',
                'amount': 1,
                'reason': 'Form approved'
            }
        
        return FormReviewResponse(
            form_id=form.form_id,
            status=form.status,
            reviewed_by=current_user.full_name,
            reviewed_at=form.reviewed_at,
            review_score=form.review_score,
            review_comments=form.review_comments,
            review_checklist=form.review_checklist,
            requested_changes=review_request.requested_changes,
            revision_deadline=review_request.revision_deadline,
            contributor_notified=True,  # TODO: Implement notification
            reward_granted=reward_granted,
            reward_details=reward_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reviewing form: {str(e)}"
        )


@router.post("/feedback", response_model=FormFeedbackResponse)
async def submit_feedback(
    feedback_request: FormFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a form.
    
    - **feedback_request**: Feedback details and issue description
    """
    form_service = FormService(db)
    
    try:
        feedback = form_service.submit_feedback(
            feedback_request=feedback_request,
            user_id=current_user.id
        )
        
        return FormFeedbackResponse(
            feedback_id=feedback.feedback_id,
            form_id=feedback_request.form_id,
            status=feedback.status,
            ticket_number=feedback.ticket_number,
            priority=feedback.priority,
            estimated_response_time="2-3 business days" if feedback.priority == "normal" else "1 business day",
            assigned_to=feedback.assigned_to.full_name if feedback.assigned_to else None,
            current_votes={'up': feedback.upvotes, 'down': feedback.downvotes}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/contributor/{contributor_id}/stats", response_model=ContributorRewardStatus)
async def get_contributor_stats(
    contributor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get contributor statistics and reward status.
    
    - **contributor_id**: ID of contributor (must be current user or admin)
    """
    # Check permissions
    if current_user.id != contributor_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own contributor stats"
        )
    
    form_service = FormService(db)
    
    try:
        stats = form_service.get_contributor_stats(contributor_id)
        
        # Calculate available weeks
        free_weeks_available = stats.free_weeks_earned - stats.free_weeks_used
        
        # Get recent contributions
        recent_contributions = []
        # TODO: Implement recent contributions query
        
        # Get achievements
        achievements = []
        # TODO: Implement achievements system
        
        # Get next milestone
        next_milestone = None
        if stats.approved_forms < 10:
            next_milestone = {
                'type': '10_forms',
                'progress': stats.approved_forms,
                'target': 10,
                'reward': '2 free weeks'
            }
        elif stats.approved_forms < 25:
            next_milestone = {
                'type': '25_forms',
                'progress': stats.approved_forms,
                'target': 25,
                'reward': '3 free weeks'
            }
        
        # Get active rewards
        active_rewards = []
        # TODO: Implement active rewards query
        
        return ContributorRewardStatus(
            contributor_id=contributor_id,
            contributor_name=stats.contributor.full_name if stats.contributor else None,
            contributor_tier=stats.contributor_tier,
            total_forms_submitted=stats.total_forms_submitted,
            approved_forms=stats.approved_forms,
            rejected_forms=stats.rejected_forms,
            pending_forms=stats.pending_forms,
            approval_rate=stats.accuracy_rate,
            unique_pages_contributed=stats.unique_pages_contributed,
            free_weeks_earned=stats.free_weeks_earned,
            free_weeks_used=stats.free_weeks_used,
            free_weeks_available=free_weeks_available,
            average_review_score=stats.average_review_score,
            current_streak=stats.current_streak,
            best_streak=stats.best_streak,
            last_contribution=stats.last_contribution,
            last_approval=stats.last_approval,
            recent_contributions=recent_contributions,
            achievements=achievements,
            next_milestone=next_milestone,
            active_rewards=active_rewards
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contributor stats: {str(e)}"
        )


@router.post("/contributor/reward", response_model=dict)
async def grant_manual_reward(
    reward_request: ContributorRewardRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manually grant reward to contributor (admin only).
    
    - **reward_request**: Reward details and reason
    """
    form_service = FormService(db)
    
    try:
        reward = form_service.grant_manual_reward(
            reward_request=reward_request,
            admin_id=current_user.id
        )
        
        return {
            'success': True,
            'message': f'Reward granted successfully',
            'reward_id': reward.ledger_id,
            'contributor_id': reward.contributor_id,
            'reward_type': reward.reward_type,
            'reward_amount': reward.reward_amount,
            'reason': reward.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error granting reward: {str(e)}"
        )


@router.get("/stats", response_model=FormStatsResponse)
async def get_form_statistics(
    db: Session = Depends(get_db)
):
    """
    Get overall form system statistics.
    
    Public endpoint for system overview.
    """
    try:
        # TODO: Implement comprehensive statistics gathering
        from sqlalchemy import func

        from models.forms import ContributorStats, Form
        
        # Basic counts
        total_forms = db.query(func.count(Form.id)).scalar() or 0
        total_contributors = db.query(func.count(ContributorStats.id)).scalar() or 0
        
        # Status breakdown
        status_counts = db.query(
            Form.status,
            func.count(Form.id)
        ).group_by(Form.status).all()
        
        status_breakdown = {status.value: count for status, count in status_counts}
        
        # Form type breakdown
        type_counts = db.query(
            Form.form_type,
            func.count(Form.id)
        ).group_by(Form.form_type).all()
        
        forms_by_type = {form_type.value: count for form_type, count in type_counts}
        
        return FormStatsResponse(
            total_forms=total_forms,
            total_contributors=total_contributors,
            total_jurisdictions=0,  # TODO: Implement
            total_languages=0,  # TODO: Implement
            status_breakdown=status_breakdown,
            forms_by_type=forms_by_type,
            forms_by_language={},  # TODO: Implement
            forms_by_state={},  # TODO: Implement
            contributions_today=0,  # TODO: Implement
            contributions_this_week=0,  # TODO: Implement
            contributions_this_month=0,  # TODO: Implement
            average_review_time=None,  # TODO: Implement
            average_review_score=None,  # TODO: Implement
            pending_reviews=0,  # TODO: Implement
            overall_accuracy_rate=None,  # TODO: Implement
            feedback_resolution_rate=None,  # TODO: Implement
            average_completeness_score=None,  # TODO: Implement
            top_contributors=[],  # TODO: Implement
            featured_forms=[],  # TODO: Implement
            contribution_trend=[],  # TODO: Implement
            quality_trend=[]  # TODO: Implement
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_statistics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get feedback system statistics (admin only).
    
    - Returns comprehensive feedback metrics and trends
    """
    try:
        from models.forms import FormFeedback
        
        # Basic counts
        total_feedback = db.query(func.count(FormFeedback.id)).scalar() or 0
        open_tickets = db.query(func.count(FormFeedback.id)).filter(
            FormFeedback.status.in_(['received', 'triaged', 'in_progress'])
        ).scalar() or 0
        resolved_tickets = db.query(func.count(FormFeedback.id)).filter(
            FormFeedback.status == 'resolved'
        ).scalar() or 0
        
        # Type breakdown
        type_counts = db.query(
            FormFeedback.feedback_type,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.feedback_type).all()
        
        feedback_by_type = {feedback_type: count for feedback_type, count in type_counts}
        
        # Severity breakdown
        severity_counts = db.query(
            FormFeedback.severity,
            func.count(FormFeedback.id)
        ).group_by(FormFeedback.severity).all()
        
        feedback_by_severity = {f"severity_{severity}": count for severity, count in severity_counts}
        
        return FeedbackStatsResponse(
            total_feedback=total_feedback,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            average_resolution_time=None,  # TODO: Calculate
            feedback_by_type=feedback_by_type,
            feedback_by_severity=feedback_by_severity,
            feedback_by_status={},  # TODO: Implement
            user_satisfaction=None,  # TODO: Implement
            resolution_rate=None,  # TODO: Calculate
            feedback_today=0,  # TODO: Implement
            feedback_this_week=0,  # TODO: Implement
            trending_issues=[],  # TODO: Implement
            most_reported_forms=[],  # TODO: Implement
            most_common_issues=[]  # TODO: Implement
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving feedback statistics: {str(e)}"
        )


# File download endpoint
@router.get("/{form_id}/download")
async def download_form_file(
    form_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download form file.
    
    - **form_id**: Form identifier
    """
    form_service = FormService(db)
    
    try:
        form = form_service.get_form_details(
            form_id=form_id,
            user_id=current_user.id if current_user else None
        )
        
        if not form.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No file available for this form"
            )
        
        # Increment download count
        form.download_count += 1
        db.commit()
        
        # TODO: Implement actual file serving
        # For now, return file information
        return {
            'download_url': f'/files/{form.file_path}',
            'file_name': f'{form.title}.pdf',
            'content_type': form.content_type,
            'file_size': form.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )
