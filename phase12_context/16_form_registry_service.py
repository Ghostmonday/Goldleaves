# services/form_registry.py
"""
Form registry service for Phase 12 crowdsourcing.
Handles form uploads, validation, deduplication, and reward tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.user import User
from schemas.forms import (
    FormUploadRequest, FormUploadResponse, FormDetailResponse,
    FormReviewRequest, FormReviewResponse, FormStatus, ContributorReward
)


class FormRegistryService:
    """Service for managing form registry operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_form(
        self,
        form_data: FormUploadRequest,
        file_data: bytes,
        contributor_id: str
    ) -> FormUploadResponse:
        """Upload a new form to the registry."""
        # Check for duplicates
        is_duplicate = await self.check_duplicate(form_data, file_data)
        if is_duplicate:
            raise ValueError("Similar form already exists in registry")
        
        # Generate form ID
        form_id = self._generate_form_id()
        
        # Store form metadata (mock implementation)
        form_record = {
            "form_id": form_id,
            "title": form_data.title,
            "description": form_data.description,
            "form_type": form_data.form_type,
            "contributor_type": form_data.contributor_type,
            "contributor_id": contributor_id,
            "metadata": form_data.metadata.dict(),
            "tags": form_data.tags,
            "status": FormStatus.PENDING,
            "created_at": datetime.utcnow(),
            "file_size": len(file_data),
            "file_hash": self._calculate_file_hash(file_data)
        }
        
        # Store file (mock implementation)
        file_path = await self._store_file(form_id, file_data)
        
        # Update contributor stats
        await self._update_contributor_stats(contributor_id)
        
        return FormUploadResponse(
            form_id=form_id,
            title=form_data.title,
            contributor_id=contributor_id,
            message="Form uploaded successfully and queued for review"
        )
    
    async def review_form(
        self,
        form_id: str,
        review_data: FormReviewRequest,
        reviewer_id: str
    ) -> FormReviewResponse:
        """Review a submitted form."""
        # Get form record (mock implementation)
        form_record = await self._get_form_record(form_id)
        if not form_record:
            raise ValueError("Form not found")
        
        # Update form status
        form_record["status"] = review_data.status
        form_record["reviewed_by"] = reviewer_id
        form_record["reviewed_at"] = datetime.utcnow()
        form_record["review_comments"] = review_data.review_comments
        form_record["review_score"] = review_data.review_score
        
        # If approved, check for rewards
        if review_data.status == FormStatus.APPROVED:
            await self.assign_reward(form_record["contributor_id"], form_id)
        
        # Save updates (mock implementation)
        await self._save_form_record(form_record)
        
        return FormReviewResponse(
            form_id=form_id,
            status=review_data.status,
            reviewed_by=reviewer_id,
            reviewed_at=datetime.utcnow(),
            review_comments=review_data.review_comments,
            review_score=review_data.review_score
        )
    
    async def assign_reward(self, contributor_id: str, form_id: str):
        """Assign reward to contributor for approved form."""
        # Get contributor stats
        stats = await self._get_contributor_stats(contributor_id)
        
        # Check if this form contributes unique pages
        unique_pages = await self._count_unique_pages(form_id)
        
        if unique_pages > 0:
            stats["unique_pages_contributed"] += unique_pages
            stats["approved_forms"] += 1
            
            # Award free weeks (10 unique pages = 1 week free)
            new_free_weeks = stats["unique_pages_contributed"] // 10
            if new_free_weeks > stats["free_weeks_earned"]:
                weeks_to_award = new_free_weeks - stats["free_weeks_earned"]
                stats["free_weeks_earned"] = new_free_weeks
                
                # Grant access (mock implementation)
                await self._grant_free_access(contributor_id, weeks_to_award)
        
        # Update stats
        await self._save_contributor_stats(contributor_id, stats)
    
    async def check_duplicate(
        self,
        form_data: FormUploadRequest,
        file_data: bytes
    ) -> bool:
        """Check if form is a duplicate."""
        file_hash = self._calculate_file_hash(file_data)
        
        # Check for exact file matches
        existing_forms = await self._find_forms_by_hash(file_hash)
        if existing_forms:
            return True
        
        # Check for similar titles and metadata
        similar_forms = await self._find_similar_forms(form_data)
        if similar_forms:
            # Additional similarity checks could be implemented here
            return len(similar_forms) > 0
        
        return False
    
    async def get_form_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        # Mock implementation - would query actual database
        return {
            "total_forms": 150,
            "pending_review": 23,
            "approved_forms": 98,
            "rejected_forms": 29,
            "forms_by_type": {
                "court_filing": 45,
                "contract": 32,
                "motion": 28,
                "pleading": 25,
                "other": 20
            },
            "forms_by_language": {
                "en": 135,
                "es": 12,
                "fr": 3
            },
            "top_contributors": [
                {"contributor_id": "user_123", "approved_forms": 15},
                {"contributor_id": "user_456", "approved_forms": 12},
                {"contributor_id": "user_789", "approved_forms": 8}
            ],
            "recent_uploads": 7
        }
    
    async def get_contributor_rewards(self, contributor_id: str) -> ContributorReward:
        """Get contributor reward information."""
        stats = await self._get_contributor_stats(contributor_id)
        
        return ContributorReward(
            contributor_id=contributor_id,
            total_forms_submitted=stats.get("total_submitted", 0),
            approved_forms=stats.get("approved_forms", 0),
            unique_pages_contributed=stats.get("unique_pages_contributed", 0),
            free_weeks_earned=stats.get("free_weeks_earned", 0),
            current_streak=stats.get("current_streak", 0),
            last_contribution=stats.get("last_contribution")
        )
    
    # Private helper methods
    
    def _generate_form_id(self) -> str:
        """Generate unique form ID."""
        import uuid
        return f"form_{uuid.uuid4().hex[:12]}"
    
    def _calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate hash of file content."""
        import hashlib
        return hashlib.sha256(file_data).hexdigest()
    
    async def _store_file(self, form_id: str, file_data: bytes) -> str:
        """Store file and return path."""
        # Mock implementation - would store in cloud storage
        return f"/storage/forms/{form_id}.pdf"
    
    async def _get_form_record(self, form_id: str) -> Optional[Dict[str, Any]]:
        """Get form record from database."""
        # Mock implementation
        return {
            "form_id": form_id,
            "status": FormStatus.PENDING,
            "contributor_id": "user_123"
        }
    
    async def _save_form_record(self, form_record: Dict[str, Any]):
        """Save form record to database."""
        # Mock implementation
        pass
    
    async def _get_contributor_stats(self, contributor_id: str) -> Dict[str, Any]:
        """Get contributor statistics."""
        # Mock implementation
        return {
            "total_submitted": 5,
            "approved_forms": 3,
            "unique_pages_contributed": 25,
            "free_weeks_earned": 2,
            "current_streak": 1,
            "last_contribution": datetime.utcnow() - timedelta(days=2)
        }
    
    async def _save_contributor_stats(self, contributor_id: str, stats: Dict[str, Any]):
        """Save contributor statistics."""
        # Mock implementation
        pass
    
    async def _count_unique_pages(self, form_id: str) -> int:
        """Count unique pages in form."""
        # Mock implementation - would analyze form content
        return 3
    
    async def _grant_free_access(self, contributor_id: str, weeks: int):
        """Grant free access to contributor."""
        # Mock implementation - would update user access
        pass
    
    async def _find_forms_by_hash(self, file_hash: str) -> List[Dict[str, Any]]:
        """Find forms with matching file hash."""
        # Mock implementation
        return []
    
    async def _find_similar_forms(self, form_data: FormUploadRequest) -> List[Dict[str, Any]]:
        """Find forms with similar metadata."""
        # Mock implementation
        return []
    
    async def _update_contributor_stats(self, contributor_id: str):
        """Update basic contributor stats after upload."""
        # Mock implementation
        pass
