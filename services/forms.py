"""
Phase 12: Form Services
Business logic for form crowdsourcing system
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from core.logging import get_logger
from models.forms import (
    ContributorStats,
    Form,
    FormFeedback,
    FormField,
    FormStatus,
    Jurisdiction,
    RewardLedger,
)
from models.user import User
from schemas.forms import (
    ContributorRewardRequest,
    FormFeedbackRequest,
    FormFilters,
    FormReviewRequest,
    FormSearchRequest,
    FormUploadRequest,
)

logger = get_logger(__name__)


class FormService:
    """Service for managing forms and crowdsourcing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_form(
        self, 
        form_request: FormUploadRequest, 
        contributor_id: int,
        file_data: Optional[UploadFile] = None
    ) -> Form:
        """Create a new form submission."""
        try:
            # Generate unique form ID
            form_id = self._generate_form_id()
            
            # Check for potential duplicates
            similar_forms = self._check_duplicates(form_request)
            
            # Create jurisdiction if needed
            jurisdiction = self._get_or_create_jurisdiction(form_request.metadata.jurisdiction)
            
            # Create form record
            form = Form(
                form_id=form_id,
                title=form_request.title,
                description=form_request.description,
                form_type=form_request.form_type,
                contributor_type=form_request.contributor_type,
                contributor_id=contributor_id,
                jurisdiction_id=jurisdiction.id if jurisdiction else None,
                form_number=form_request.metadata.form_number,
                version=form_request.metadata.version,
                effective_date=form_request.metadata.effective_date,
                expiration_date=form_request.metadata.expiration_date,
                language=form_request.metadata.language,
                metadata=self._prepare_metadata(form_request.metadata),
                tags=form_request.tags,
                status=FormStatus.PENDING
            )
            
            # Handle file upload if provided
            if file_data:
                file_info = self._process_file_upload(file_data)
                form.file_path = file_info['file_path']
                form.file_size = file_info['file_size']
                form.file_hash = file_info['file_hash']
                form.content_type = file_info['content_type']
                form.page_count = file_info.get('page_count')
                form.word_count = file_info.get('word_count')
            
            self.db.add(form)
            self.db.flush()
            
            # Create form fields if provided
            if form_request.fields:
                self._create_form_fields(form.id, form_request.fields)
            
            # Update contributor stats
            self._update_contributor_stats(contributor_id, 'form_submitted')
            
            # Check for automatic rewards
            self._check_contribution_rewards(contributor_id, form)
            
            self.db.commit()
            
            logger.info(f"Form created: {form_id} by contributor {contributor_id}")
            return form
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating form: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating form")
    
    def review_form(
        self, 
        form_id: str, 
        review_request: FormReviewRequest,
        reviewer_id: int
    ) -> Form:
        """Review and update form status."""
        try:
            form = self.db.query(Form).filter(Form.form_id == form_id).first()
            if not form:
                raise HTTPException(status_code=404, detail="Form not found")
            
            if form.status not in [FormStatus.PENDING, FormStatus.UNDER_REVIEW]:
                raise HTTPException(status_code=400, detail="Form is not in reviewable state")
            
            # Update form with review
            form.reviewed_by_id = reviewer_id
            form.reviewed_at = datetime.utcnow()
            form.review_comments = review_request.review_comments
            form.review_score = review_request.review_score
            
            # Set status based on review decision
            if review_request.status == "approve":
                form.status = FormStatus.APPROVED
                form.is_public = True
                form.accuracy_verified = review_request.accuracy_verified or False
                form.lock_form()
                
                # Grant rewards for approved form
                self._grant_approval_reward(form.contributor_id, form)
                
            elif review_request.status == "reject":
                form.status = FormStatus.REJECTED
                
            elif review_request.status == "request_revision":
                form.status = FormStatus.NEEDS_REVISION
                # Set revision deadline if provided
                if review_request.revision_deadline:
                    form.metadata = form.metadata or {}
                    form.metadata['revision_deadline'] = review_request.revision_deadline.isoformat()
            
            # Update review checklist
            checklist_items = [
                review_request.accuracy_verified,
                review_request.formatting_correct,
                review_request.fields_complete,
                review_request.metadata_accurate
            ]
            if [item for item in checklist_items if item is not None]:
                form.review_checklist = {
                    'accuracy_verified': review_request.accuracy_verified,
                    'formatting_correct': review_request.formatting_correct,
                    'fields_complete': review_request.fields_complete,
                    'metadata_accurate': review_request.metadata_accurate
                }
            
            # Update contributor stats
            self._update_contributor_stats(
                form.contributor_id, 
                'form_reviewed',
                form.status.value,
                review_request.review_score
            )
            
            self.db.commit()
            
            logger.info(f"Form {form_id} reviewed by {reviewer_id}: {review_request.status}")
            return form
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reviewing form {form_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error reviewing form")
    
    def submit_feedback(
        self,
        feedback_request: FormFeedbackRequest,
        user_id: int
    ) -> FormFeedback:
        """Submit feedback on a form."""
        try:
            form = self.db.query(Form).filter(Form.form_id == feedback_request.form_id).first()
            if not form:
                raise HTTPException(status_code=404, detail="Form not found")
            
            # Generate unique feedback ID and ticket number
            feedback_id = self._generate_feedback_id()
            ticket_number = self._generate_ticket_number()
            
            # Determine priority based on feedback type and severity
            priority = self._calculate_feedback_priority(
                feedback_request.feedback_type, 
                feedback_request.severity
            )
            
            feedback = FormFeedback(
                feedback_id=feedback_id,
                form_id=form.id,
                user_id=user_id,
                feedback_type=feedback_request.feedback_type.value,
                title=feedback_request.title,
                content=feedback_request.content,
                severity=feedback_request.severity,
                field_name=feedback_request.field_name,
                suggested_correction=feedback_request.suggested_correction,
                contact_email=feedback_request.contact_email,
                ticket_number=ticket_number,
                priority=priority,
                status="received"
            )
            
            self.db.add(feedback)
            
            # Update form feedback count
            form.feedback_count += 1
            
            # Auto-assign if high priority
            if priority in ["high", "urgent", "critical"]:
                self._auto_assign_feedback(feedback)
            
            self.db.commit()
            
            logger.info(f"Feedback submitted: {feedback_id} for form {feedback_request.form_id}")
            return feedback
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting feedback: {str(e)}")
            raise HTTPException(status_code=500, detail="Error submitting feedback")
    
    def search_forms(self, search_request: FormSearchRequest) -> Tuple[List[Form], Dict[str, Any]]:
        """Search forms with filters and pagination."""
        try:
            query = self.db.query(Form)
            
            # Apply text search
            if search_request.query:
                search_term = f"%{search_request.query}%"
                query = query.filter(
                    or_(
                        Form.title.ilike(search_term),
                        Form.description.ilike(search_term),
                        Form.form_number.ilike(search_term)
                    )
                )
            
            # Apply filters
            if search_request.filters:
                query = self._apply_form_filters(query, search_request.filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            if search_request.sort_by:
                sort_column = Form.created_at  # Default
                try:
                    if search_request.sort_by in Form.__dict__:
                        sort_column = Form.__dict__[search_request.sort_by]
                except (AttributeError, KeyError):
                    pass  # Use default
                    
                if search_request.sort_order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            
            # Apply pagination
            offset = (search_request.page - 1) * search_request.per_page
            forms = query.offset(offset).limit(search_request.per_page).all()
            
            # Build pagination metadata
            total_pages = (total_count + search_request.per_page - 1) // search_request.per_page
            pagination = {
                'page': search_request.page,
                'per_page': search_request.per_page,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': search_request.page < total_pages,
                'has_prev': search_request.page > 1
            }
            
            return forms, pagination
            
        except Exception as e:
            logger.error(f"Error searching forms: {str(e)}")
            raise HTTPException(status_code=500, detail="Error searching forms")
    
    def get_form_details(self, form_id: str, user_id: Optional[int] = None) -> Form:
        """Get detailed form information."""
        try:
            form = self.db.query(Form).filter(Form.form_id == form_id).first()
            if not form:
                raise HTTPException(status_code=404, detail="Form not found")
            
            # Check access permissions
            if not form.is_public and (not user_id or form.contributor_id != user_id):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Increment view count
            form.view_count += 1
            self.db.commit()
            
            return form
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting form details: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving form")
    
    def get_contributor_stats(self, contributor_id: int) -> ContributorStats:
        """Get contributor statistics and rewards."""
        try:
            stats = self.db.query(ContributorStats).filter(
                ContributorStats.contributor_id == contributor_id
            ).first()
            
            if not stats:
                # Create initial stats record
                stats = ContributorStats(contributor_id=contributor_id)
                self.db.add(stats)
                self.db.commit()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting contributor stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving contributor stats")
    
    def grant_manual_reward(
        self,
        reward_request: ContributorRewardRequest,
        admin_id: int
    ) -> RewardLedger:
        """Manually grant reward to contributor (admin only)."""
        try:
            # Verify contributor exists
            contributor = self.db.query(User).filter(User.id == reward_request.contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            # Calculate expiration date
            expires_at = None
            if reward_request.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=reward_request.expires_in_days)
            
            # Create reward record
            reward = RewardLedger(
                ledger_id=self._generate_reward_id(),
                contributor_id=reward_request.contributor_id,
                reward_type=reward_request.reward_type,
                reward_amount=reward_request.reward_amount,
                reason=reward_request.reason,
                granted_by_id=admin_id,
                expires_at=expires_at,
                milestone_type="manual_grant"
            )
            
            self.db.add(reward)
            
            # Update contributor stats
            stats = self.get_contributor_stats(reward_request.contributor_id)
            if reward_request.reward_type == "free_week":
                stats.free_weeks_earned += reward_request.reward_amount
            else:
                stats.bonus_rewards_earned += reward_request.reward_amount
            
            stats.last_reward_granted = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Manual reward granted: {reward_request.reward_type} x{reward_request.reward_amount} to contributor {reward_request.contributor_id}")
            return reward
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error granting manual reward: {str(e)}")
            raise HTTPException(status_code=500, detail="Error granting reward")
    
    # Private helper methods
    
    def _generate_form_id(self) -> str:
        """Generate unique form ID."""
        return f"form_{uuid.uuid4().hex[:12]}"
    
    def _generate_feedback_id(self) -> str:
        """Generate unique feedback ID."""
        return f"fb_{uuid.uuid4().hex[:12]}"
    
    def _generate_reward_id(self) -> str:
        """Generate unique reward ID."""
        return f"rwd_{uuid.uuid4().hex[:12]}"
    
    def _generate_ticket_number(self) -> str:
        """Generate unique ticket number."""
        # Format: FB-YYYYMMDD-XXXX
        date_str = datetime.utcnow().strftime("%Y%m%d")
        sequence = self.db.query(func.count(FormFeedback.id)).scalar() + 1
        return f"FB-{date_str}-{sequence:04d}"
    
    def _check_duplicates(self, form_request: FormUploadRequest) -> List[Form]:
        """Check for potential duplicate forms."""
        similar_forms = self.db.query(Form).filter(
            and_(
                Form.title.ilike(f"%{form_request.title}%"),
                Form.form_type == form_request.form_type,
                Form.status != FormStatus.REJECTED
            )
        ).limit(5).all()
        
        return similar_forms
    
    def _get_or_create_jurisdiction(self, jurisdiction_info) -> Optional[Jurisdiction]:
        """Get or create jurisdiction record."""
        if not jurisdiction_info:
            return None
        
        # Try to find existing jurisdiction
        existing = self.db.query(Jurisdiction).filter(
            and_(
                Jurisdiction.state == jurisdiction_info.state,
                Jurisdiction.county == jurisdiction_info.county,
                Jurisdiction.court_type == jurisdiction_info.court_type
            )
        ).first()
        
        if existing:
            return existing
        
        # Create new jurisdiction
        code = f"{jurisdiction_info.state}_{jurisdiction_info.county or 'STATE'}_{jurisdiction_info.court_type or 'GENERAL'}"
        code = code.replace(" ", "_").upper()
        
        jurisdiction = Jurisdiction(
            code=code,
            name=f"{jurisdiction_info.court_name or jurisdiction_info.court_type or 'Court'} - {jurisdiction_info.county or jurisdiction_info.state}",
            state=jurisdiction_info.state,
            county=jurisdiction_info.county,
            court_type=jurisdiction_info.court_type
        )
        
        self.db.add(jurisdiction)
        return jurisdiction
    
    def _prepare_metadata(self, metadata) -> Dict[str, Any]:
        """Prepare metadata for storage."""
        meta_dict = {
            'source_url': metadata.source_url,
            'case_types': metadata.case_types,
            'filing_fee': metadata.filing_fee,
            'processing_time': metadata.processing_time,
            'required_copies': metadata.required_copies,
            'related_forms': metadata.related_forms
        }
        
        # Remove None values
        return {k: v for k, v in meta_dict.items() if v is not None}
    
    def _process_file_upload(self, file_data: UploadFile) -> Dict[str, Any]:
        """Process uploaded file and extract metadata."""
        # Read file content
        content = file_data.file.read()
        file_data.file.seek(0)  # Reset for potential re-reading
        
        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Basic file info
        content_size = 0
        if content:
            content_size = content.__len__()
            
        file_info = {
            'file_path': f"forms/{file_hash[:2]}/{file_hash}.{file_data.filename.split('.')[-1]}",
            'file_size': content_size,
            'file_hash': file_hash,
            'content_type': file_data.content_type
        }
        
        # TODO: Add file processing logic for PDF/Word documents
        # - Extract page count
        # - Extract word count
        # - Extract text for search indexing
        # - Generate thumbnails
        
        return file_info
    
    def _create_form_fields(self, form_id: int, fields: List) -> None:
        """Create form field definitions."""
        for field_def in fields:
            field = FormField(
                form_id=form_id,
                field_name=field_def.field_name,
                field_label=field_def.field_label,
                field_type=field_def.field_type,
                field_order=field_def.field_order,
                is_required=field_def.is_required,
                is_repeatable=field_def.is_repeatable,
                max_length=field_def.max_length,
                min_length=field_def.min_length,
                validation_rules=field_def.validation_rules,
                default_value=field_def.default_value,
                placeholder_text=field_def.placeholder_text,
                help_text=field_def.help_text,
                section_name=field_def.section_name,
                group_name=field_def.group_name,
                ai_field_category=field_def.ai_field_category
            )
            self.db.add(field)
    
    def _update_contributor_stats(
        self, 
        contributor_id: int, 
        action: str, 
        status: Optional[str] = None,
        score: Optional[float] = None
    ) -> None:
        """Update contributor statistics."""
        stats = self.get_contributor_stats(contributor_id)
        
        if action == 'form_submitted':
            stats.total_forms_submitted += 1
            stats.pending_forms += 1
            stats.last_contribution = datetime.utcnow()
            
        elif action == 'form_reviewed':
            stats.pending_forms = max(0, stats.pending_forms - 1)
            
            if status == FormStatus.APPROVED.value:
                stats.approved_forms += 1
                stats.last_approval = datetime.utcnow()
                # Update streak
                stats.current_streak += 1
                stats.best_streak = max(stats.best_streak, stats.current_streak)
                
            elif status == FormStatus.REJECTED.value:
                stats.rejected_forms += 1
                stats.current_streak = 0  # Break streak
                
            elif status == FormStatus.NEEDS_REVISION.value:
                stats.revision_requests += 1
            
            # Update review score
            if score:
                stats.update_average_score(score)
            
            # Calculate accuracy rate
            stats.calculate_accuracy_rate()
            
            # Check for tier upgrade
            stats.check_tier_upgrade()
    
    def _check_contribution_rewards(self, contributor_id: int, form: Form) -> None:
        """Check and grant automatic rewards based on contributions."""
        stats = self.get_contributor_stats(contributor_id)
        
        # Milestone rewards
        milestones = [
            (1, "first_form", 1),
            (5, "5_forms", 1),
            (10, "10_forms", 2),
            (25, "25_forms", 3),
            (50, "50_forms", 5),
            (100, "100_forms", 10)
        ]
        
        for threshold, milestone_type, reward_amount in milestones:
            if stats.total_forms_submitted == threshold:
                self._grant_milestone_reward(
                    contributor_id, 
                    form.id, 
                    milestone_type, 
                    reward_amount,
                    threshold
                )
    
    def _grant_approval_reward(self, contributor_id: int, form: Form) -> None:
        """Grant reward for approved form."""
        stats = self.get_contributor_stats(contributor_id)
        
        # Base reward for approval
        base_reward = 1
        
        # Bonus for high quality
        quality_bonus = 0
        if form.review_score and form.review_score >= 9.0:
            quality_bonus = 1
        
        # Streak bonus
        streak_bonus = 0
        if stats.current_streak >= 10:
            streak_bonus = 1
        elif stats.current_streak >= 5:
            streak_bonus = 0  # No bonus yet
        
        total_reward = base_reward + quality_bonus + streak_bonus
        
        if total_reward > 0:
            reward = RewardLedger(
                ledger_id=self._generate_reward_id(),
                contributor_id=contributor_id,
                form_id=form.id,
                reward_type="free_week",
                reward_amount=total_reward,
                reason=f"Form approved (quality: {form.review_score}, streak: {stats.current_streak})",
                milestone_type="approval_reward"
            )
            
            self.db.add(reward)
            stats.free_weeks_earned += total_reward
    
    def _grant_milestone_reward(
        self, 
        contributor_id: int, 
        form_id: int, 
        milestone_type: str,
        reward_amount: int,
        milestone_value: int
    ) -> None:
        """Grant milestone reward."""
        reward = RewardLedger(
            ledger_id=self._generate_reward_id(),
            contributor_id=contributor_id,
            form_id=form_id,
            reward_type="free_week",
            reward_amount=reward_amount,
            reason=f"Milestone reached: {milestone_type}",
            milestone_type=milestone_type,
            milestone_value=milestone_value
        )
        
        self.db.add(reward)
        
        stats = self.get_contributor_stats(contributor_id)
        stats.free_weeks_earned += reward_amount
    
    def _calculate_feedback_priority(self, feedback_type: str, severity: int) -> str:
        """Calculate feedback priority based on type and severity."""
        critical_types = ["field_error", "content_issue", "jurisdiction_wrong"]
        high_types = ["parsing_issue", "incorrect_format", "outdated_form"]
        
        if feedback_type in critical_types and severity >= 4:
            return "critical"
        elif feedback_type in critical_types and severity >= 3:
            return "high"
        elif feedback_type in high_types and severity >= 4:
            return "high"
        elif severity >= 4:
            return "high"
        elif severity >= 3:
            return "normal"
        else:
            return "low"
    
    def _auto_assign_feedback(self, feedback: FormFeedback) -> None:
        """Auto-assign high priority feedback to available reviewers."""
        # TODO: Implement auto-assignment logic
        # - Find available reviewers
        # - Consider workload balancing
        # - Assign based on expertise
        pass
    
    def _apply_form_filters(self, query, filters: FormFilters):
        """Apply search filters to query."""
        if filters.form_type:
            query = query.filter(Form.form_type == filters.form_type)
        
        if filters.status:
            query = query.filter(Form.status == filters.status)
        
        if filters.language:
            query = query.filter(Form.language == filters.language)
        
        if filters.contributor_type:
            query = query.filter(Form.contributor_type == filters.contributor_type)
        
        if filters.state:
            query = query.join(Jurisdiction).filter(Jurisdiction.state == filters.state)
        
        if filters.county:
            query = query.join(Jurisdiction).filter(Jurisdiction.county == filters.county)
        
        if filters.form_number:
            query = query.filter(Form.form_number.ilike(f"%{filters.form_number}%"))
        
        if filters.date_from:
            query = query.filter(Form.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Form.created_at <= filters.date_to)
        
        if filters.min_score:
            query = query.filter(Form.review_score >= filters.min_score)
        
        if filters.is_featured is not None:
            query = query.filter(Form.is_featured == filters.is_featured)
        
        if filters.has_feedback is not None:
            if filters.has_feedback:
                query = query.filter(Form.feedback_count > 0)
            else:
                query = query.filter(Form.feedback_count == 0)
        
        return query
