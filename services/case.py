# services/case.py

import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError, ValidationError
from models.case import (
    Case,
    CaseEvent,
    CasePriority,
    CaseStatus,
    CaseTask,
    CaseType,
    TaskStatus,
    TimeEntry,
    TimeEntryStatus,
)
from models.client import Client
from models.user import User
from schemas.case.core import (
    CaseBulkAction,
    CaseBulkResult,
    CaseCreate,
    CaseFilter,
    CaseStats,
    CaseUpdate,
)


class CaseService:
    """Service layer for case management with multi-tenant support."""
    
    @staticmethod
    def generate_case_number(organization_id: int, case_type: CaseType, year: int = None) -> str:
        """Generate a unique case number for the organization."""
        if year is None:
            year = datetime.utcnow().year
        
        # Create case type prefix (first 3 letters)
        type_prefix = case_type.value[:3].upper()
        
        # Generate random suffix for uniqueness
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        
        return f"{type_prefix}-{year}-{suffix}"
    
    @staticmethod
    def create_case(
        db: Session, 
        case_data: CaseCreate, 
        organization_id: int, 
        created_by_id: int
    ) -> Case:
        """Create a new case with organization isolation."""
        
        # Verify client exists and belongs to organization
        client = db.query(Client).filter(
            and_(
                Client.id == case_data.client_id,
                Client.organization_id == organization_id,
                Client.is_deleted == False
            )
        ).first()
        
        if not client:
            raise ValidationError("Client not found or does not belong to organization")
        
        # Generate unique case number
        case_number = CaseService.generate_case_number(
            organization_id, 
            case_data.case_type
        )
        
        # Ensure case number is unique
        while db.query(Case).filter(
            and_(
                Case.case_number == case_number,
                Case.organization_id == organization_id
            )
        ).first():
            case_number = CaseService.generate_case_number(
                organization_id, 
                case_data.case_type
            )
        
        # Create case
        case = Case(
            case_number=case_number,
            title=case_data.title,
            description=case_data.description,
            case_type=case_data.case_type,
            status=case_data.status,
            priority=case_data.priority,
            billing_type=case_data.billing_type,
            hourly_rate=case_data.hourly_rate,
            fixed_fee=case_data.fixed_fee,
            contingency_percentage=case_data.contingency_percentage,
            estimated_hours=case_data.estimated_hours,
            budget=case_data.budget,
            tags=case_data.tags or [],
            
            # Court information
            court_name=case_data.court_name,
            court_level=case_data.court_level,
            judge_name=case_data.judge_name,
            case_reference=case_data.case_reference,
            
            # Dates
            case_opened_date=case_data.case_opened_date or datetime.utcnow().date(),
            statute_of_limitations=case_data.statute_of_limitations,
            next_court_date=case_data.next_court_date,
            
            # Relationships
            client_id=case_data.client_id,
            organization_id=organization_id,
            created_by_id=created_by_id,
            assigned_to_id=case_data.assigned_to_id,
            opposing_party=case_data.opposing_party,
            opposing_counsel=case_data.opposing_counsel
        )
        
        db.add(case)
        db.commit()
        db.refresh(case)
        
        # Create initial case event
        initial_event = CaseEvent(
            case_id=case.id,
            organization_id=organization_id,
            event_type="case_created",
            title="Case Created",
            description=f"Case {case.case_number} was created",
            event_date=datetime.utcnow(),
            created_by_id=created_by_id
        )
        
        db.add(initial_event)
        db.commit()
        
        return case
    
    @staticmethod
    def get_case(db: Session, case_id: int, organization_id: int) -> Optional[Case]:
        """Get a case by ID with organization isolation."""
        return db.query(Case).filter(
            and_(
                Case.id == case_id,
                Case.organization_id == organization_id,
                Case.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def get_case_by_number(db: Session, case_number: str, organization_id: int) -> Optional[Case]:
        """Get a case by case number with organization isolation."""
        return db.query(Case).filter(
            and_(
                Case.case_number == case_number,
                Case.organization_id == organization_id,
                Case.is_deleted == False
            )
        ).first()
    
    @staticmethod
    def update_case(
        db: Session, 
        case_id: int, 
        case_update: CaseUpdate, 
        organization_id: int,
        updated_by_id: int
    ) -> Optional[Case]:
        """Update a case with organization isolation."""
        case = CaseService.get_case(db, case_id, organization_id)
        if not case:
            raise NotFoundError("Case not found")
        
        # Track what changed for event logging
        changes = []
        update_data = case_update.dict(exclude_unset=True)
        
        for field, new_value in update_data.items():
            old_value = getattr(case, field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} → {new_value}")
                setattr(case, field, new_value)
        
        if changes:
            # Update case
            db.commit()
            db.refresh(case)
            
            # Log update event
            update_event = CaseEvent(
                case_id=case.id,
                organization_id=organization_id,
                event_type="case_updated",
                title="Case Updated",
                description=f"Case updated: {', '.join(changes)}",
                event_date=datetime.utcnow(),
                created_by_id=updated_by_id
            )
            
            db.add(update_event)
            db.commit()
        
        return case
    
    @staticmethod
    def delete_case(db: Session, case_id: int, organization_id: int, deleted_by_id: int) -> bool:
        """Soft delete a case with organization isolation."""
        case = CaseService.get_case(db, case_id, organization_id)
        if not case:
            raise NotFoundError("Case not found")
        
        # Soft delete case and related records
        case.soft_delete()
        
        # Log deletion event
        delete_event = CaseEvent(
            case_id=case.id,
            organization_id=organization_id,
            event_type="case_deleted",
            title="Case Deleted",
            description=f"Case {case.case_number} was deleted",
            event_date=datetime.utcnow(),
            created_by_id=deleted_by_id
        )
        
        db.add(delete_event)
        db.commit()
        
        return True
    
    @staticmethod
    def list_cases(
        db: Session, 
        organization_id: int, 
        filters: Optional[CaseFilter] = None,
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> Tuple[List[Case], int]:
        """List cases with filtering, pagination, and organization isolation."""
        
        query = db.query(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False
            )
        )
        
        # Apply filters
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Case.case_number.ilike(search_term),
                        Case.title.ilike(search_term),
                        Case.description.ilike(search_term),
                        Case.opposing_party.ilike(search_term)
                    )
                )
            
            if filters.case_type:
                query = query.filter(Case.case_type == filters.case_type)
            
            if filters.status:
                query = query.filter(Case.status == filters.status)
            
            if filters.priority:
                query = query.filter(Case.priority == filters.priority)
            
            if filters.billing_type:
                query = query.filter(Case.billing_type == filters.billing_type)
            
            if filters.client_id:
                query = query.filter(Case.client_id == filters.client_id)
            
            if filters.assigned_to_id:
                query = query.filter(Case.assigned_to_id == filters.assigned_to_id)
            
            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Case.tags.contains([tag]))
            
            if filters.opened_after:
                query = query.filter(Case.case_opened_date >= filters.opened_after)
            
            if filters.opened_before:
                query = query.filter(Case.case_opened_date <= filters.opened_before)
            
            if filters.next_court_date_after:
                query = query.filter(Case.next_court_date >= filters.next_court_date_after)
            
            if filters.next_court_date_before:
                query = query.filter(Case.next_court_date <= filters.next_court_date_before)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        if order_direction.lower() == "desc":
            query = query.order_by(desc(getattr(Case, order_by, Case.created_at)))
        else:
            query = query.order_by(asc(getattr(Case, order_by, Case.created_at)))
        
        # Apply pagination
        cases = query.offset(skip).limit(limit).all()
        
        return cases, total
    
    @staticmethod
    def get_case_stats(db: Session, organization_id: int) -> CaseStats:
        """Get case statistics for an organization."""
        
        base_query = db.query(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False
            )
        )
        
        total_cases = base_query.count()
        active_cases = base_query.filter(Case.status == CaseStatus.ACTIVE).count()
        closed_cases = base_query.filter(Case.status == CaseStatus.CLOSED).count()
        
        # Count by type
        by_type = {}
        for case_type in CaseType:
            count = base_query.filter(Case.case_type == case_type).count()
            by_type[case_type.value] = count
        
        # Count by status
        by_status = {}
        for status in CaseStatus:
            count = base_query.filter(Case.status == status).count()
            by_status[status.value] = count
        
        # Count by priority
        by_priority = {}
        for priority in CasePriority:
            count = base_query.filter(Case.priority == priority).count()
            by_priority[priority.value] = count
        
        # Recent cases (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_cases = base_query.filter(Case.created_at >= thirty_days_ago).count()
        
        # Financial stats
        total_budget = base_query.with_entities(func.sum(Case.budget)).scalar() or 0
        total_hours = db.query(func.sum(TimeEntry.hours_worked)).join(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False,
                TimeEntry.status == TimeEntryStatus.APPROVED
            )
        ).scalar() or 0
        
        total_billed = db.query(func.sum(TimeEntry.billable_amount)).join(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False,
                TimeEntry.status == TimeEntryStatus.APPROVED
            )
        ).scalar() or Decimal('0')
        
        return CaseStats(
            total_cases=total_cases,
            active_cases=active_cases,
            closed_cases=closed_cases,
            by_type=by_type,
            by_status=by_status,
            by_priority=by_priority,
            recent_cases=recent_cases,
            total_budget=float(total_budget),
            total_hours=float(total_hours),
            total_billed=float(total_billed)
        )
    
    @staticmethod
    def close_case(
        db: Session, 
        case_id: int, 
        organization_id: int, 
        closed_by_id: int,
        closure_reason: str,
        final_notes: Optional[str] = None
    ) -> Case:
        """Close a case with proper event logging."""
        case = CaseService.get_case(db, case_id, organization_id)
        if not case:
            raise NotFoundError("Case not found")
        
        if case.status == CaseStatus.CLOSED:
            raise ValidationError("Case is already closed")
        
        # Update case status
        case.status = CaseStatus.CLOSED
        case.case_closed_date = datetime.utcnow().date()
        
        if final_notes:
            case.description = f"{case.description}\n\nFinal Notes: {final_notes}"
        
        # Create closure event
        closure_event = CaseEvent(
            case_id=case.id,
            organization_id=organization_id,
            event_type="case_closed",
            title="Case Closed",
            description=f"Case closed. Reason: {closure_reason}",
            event_date=datetime.utcnow(),
            created_by_id=closed_by_id
        )
        
        db.add(closure_event)
        db.commit()
        db.refresh(case)
        
        return case
    
    @staticmethod
    def reopen_case(
        db: Session, 
        case_id: int, 
        organization_id: int, 
        reopened_by_id: int,
        reason: str
    ) -> Case:
        """Reopen a closed case."""
        case = CaseService.get_case(db, case_id, organization_id)
        if not case:
            raise NotFoundError("Case not found")
        
        if case.status != CaseStatus.CLOSED:
            raise ValidationError("Only closed cases can be reopened")
        
        # Update case status
        case.status = CaseStatus.ACTIVE
        case.case_closed_date = None
        
        # Create reopening event
        reopen_event = CaseEvent(
            case_id=case.id,
            organization_id=organization_id,
            event_type="case_reopened",
            title="Case Reopened",
            description=f"Case reopened. Reason: {reason}",
            event_date=datetime.utcnow(),
            created_by_id=reopened_by_id
        )
        
        db.add(reopen_event)
        db.commit()
        db.refresh(case)
        
        return case
    
    @staticmethod
    def search_cases(
        db: Session, 
        organization_id: int, 
        search_term: str, 
        limit: int = 10
    ) -> List[Case]:
        """Quick search for cases (for typeahead/autocomplete)."""
        
        search_pattern = f"%{search_term}%"
        
        return db.query(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False,
                or_(
                    Case.case_number.ilike(search_pattern),
                    Case.title.ilike(search_pattern),
                    Case.opposing_party.ilike(search_pattern)
                )
            )
        ).order_by(Case.case_number).limit(limit).all()
    
    @staticmethod
    def get_upcoming_deadlines(
        db: Session, 
        organization_id: int, 
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Get upcoming case deadlines."""
        
        future_date = datetime.utcnow().date() + timedelta(days=days_ahead)
        
        # Court dates
        court_dates = db.query(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False,
                Case.next_court_date.isnot(None),
                Case.next_court_date <= future_date
            )
        ).order_by(Case.next_court_date).all()
        
        # Task deadlines
        task_deadlines = db.query(CaseTask).join(Case).filter(
            and_(
                Case.organization_id == organization_id,
                Case.is_deleted == False,
                CaseTask.due_date.isnot(None),
                CaseTask.due_date <= future_date,
                CaseTask.status != TaskStatus.COMPLETED
            )
        ).order_by(CaseTask.due_date).all()
        
        deadlines = []
        
        # Add court dates
        for case in court_dates:
            deadlines.append({
                "type": "court_date",
                "case_id": case.id,
                "case_number": case.case_number,
                "case_title": case.title,
                "date": case.next_court_date,
                "description": f"Court hearing: {case.court_name}",
                "priority": case.priority.value
            })
        
        # Add task deadlines
        for task in task_deadlines:
            deadlines.append({
                "type": "task_deadline",
                "case_id": task.case_id,
                "case_number": task.case.case_number,
                "case_title": task.case.title,
                "task_id": task.id,
                "task_title": task.title,
                "date": task.due_date,
                "description": f"Task: {task.title}",
                "priority": task.priority.value
            })
        
        # Sort by date
        deadlines.sort(key=lambda x: x["date"])
        
        return deadlines
    
    @staticmethod
    def bulk_update_cases(
        db: Session, 
        bulk_action: CaseBulkAction, 
        organization_id: int,
        updated_by_id: int
    ) -> CaseBulkResult:
        """Perform bulk operations on cases."""
        
        result = CaseBulkResult()
        
        for case_id in bulk_action.case_ids:
            try:
                case = CaseService.get_case(db, case_id, organization_id)
                if not case:
                    result.error_count += 1
                    result.errors.append({
                        "case_id": case_id,
                        "error": "Case not found"
                    })
                    continue
                
                # Perform action
                if bulk_action.action == "update_status":
                    new_status = bulk_action.parameters.get("status")
                    if new_status and new_status in [s.value for s in CaseStatus]:
                        case.status = CaseStatus(new_status)
                        result.success_count += 1
                        result.updated_cases.append(case_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "case_id": case_id,
                            "error": "Invalid status"
                        })
                
                elif bulk_action.action == "update_priority":
                    new_priority = bulk_action.parameters.get("priority")
                    if new_priority and new_priority in [p.value for p in CasePriority]:
                        case.priority = CasePriority(new_priority)
                        result.success_count += 1
                        result.updated_cases.append(case_id)
                    else:
                        result.error_count += 1
                        result.errors.append({
                            "case_id": case_id,
                            "error": "Invalid priority"
                        })
                
                elif bulk_action.action == "assign_to":
                    assigned_to_id = bulk_action.parameters.get("assigned_to_id")
                    if assigned_to_id:
                        # Verify user exists and belongs to organization
                        user = db.query(User).filter(
                            and_(
                                User.id == assigned_to_id,
                                User.organization_id == organization_id,
                                User.is_active == True
                            )
                        ).first()
                        
                        if user:
                            case.assigned_to_id = assigned_to_id
                            result.success_count += 1
                            result.updated_cases.append(case_id)
                        else:
                            result.error_count += 1
                            result.errors.append({
                                "case_id": case_id,
                                "error": "Invalid assigned user"
                            })
                    else:
                        case.assigned_to_id = None
                        result.success_count += 1
                        result.updated_cases.append(case_id)
                
                elif bulk_action.action == "add_tags":
                    tags_to_add = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_add:
                        case.add_tag(tag)
                    result.success_count += 1
                    result.updated_cases.append(case_id)
                
                elif bulk_action.action == "remove_tags":
                    tags_to_remove = bulk_action.parameters.get("tags", [])
                    for tag in tags_to_remove:
                        case.remove_tag(tag)
                    result.success_count += 1
                    result.updated_cases.append(case_id)
                
                else:
                    result.error_count += 1
                    result.errors.append({
                        "case_id": case_id,
                        "error": f"Unknown action: {bulk_action.action}"
                    })
                
            except Exception as e:
                result.error_count += 1
                result.errors.append({
                    "case_id": case_id,
                    "error": str(e)
                })
        
        if result.success_count > 0:
            db.commit()
        
        return result
