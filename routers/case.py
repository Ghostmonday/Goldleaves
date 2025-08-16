# routers/case.py

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.dependencies import get_current_active_user, get_current_organization_id
from core.exceptions import NotFoundError, ValidationError
from models.user import User
from schemas.base.pagination import PaginatedResponse
from schemas.base.responses import SuccessResponse
from schemas.case.core import (
    CaseBulkAction,
    CaseBulkResult,
    CaseCreate,
    CaseFilter,
    CaseResponse,
    CaseStats,
    CaseUpdate,
)
from services.case import CaseService

router = APIRouter(
    prefix="/cases",
    tags=["cases"],
    dependencies=[Depends(get_current_active_user)]
)


@router.post("/", response_model=CaseResponse, status_code=201)
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Create a new case."""
    try:
        case = CaseService.create_case(
            db=db,
            case_data=case_data,
            organization_id=organization_id,
            created_by_id=current_user.id
        )
        return CaseResponse.from_orm(case)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create case")


@router.get("/", response_model=PaginatedResponse[CaseResponse], response_model_exclude_none=True)
def list_cases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in case number, title, description"),
    case_type: Optional[str] = Query(None, description="Filter by case type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    billing_type: Optional[str] = Query(None, description="Filter by billing type"),
    client_id: Optional[int] = Query(None, description="Filter by client"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    opened_after: Optional[date] = Query(None, description="Filter cases opened after date"),
    opened_before: Optional[date] = Query(None, description="Filter cases opened before date"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Order direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """List cases with filtering and pagination."""

    # Build filters
    filters = CaseFilter(
        search=search,
        case_type=case_type,
        status=status,
        priority=priority,
        billing_type=billing_type,
        client_id=client_id,
        assigned_to_id=assigned_to_id,
        tags=tags,
        opened_after=opened_after,
        opened_before=opened_before
    )

    cases, total = CaseService.list_cases(
        db=db,
        organization_id=organization_id,
        filters=filters,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_direction=order_direction
    )

    return PaginatedResponse(
        items=[CaseResponse.from_orm(case) for case in cases],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/search", response_model=List[CaseResponse], response_model_exclude_none=True)
def search_cases(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Quick search for cases (for autocomplete/typeahead)."""

    cases = CaseService.search_cases(
        db=db,
        organization_id=organization_id,
        search_term=q,
        limit=limit
    )

    return [CaseResponse.from_orm(case) for case in cases]


@router.get("/stats", response_model=CaseStats, response_model_exclude_none=True)
def get_case_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get case statistics for the organization."""

    return CaseService.get_case_stats(db=db, organization_id=organization_id)


@router.get("/deadlines")
def get_upcoming_deadlines(
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get upcoming case deadlines and court dates."""

    deadlines = CaseService.get_upcoming_deadlines(
        db=db,
        organization_id=organization_id,
        days_ahead=days_ahead
    )

    return deadlines


@router.get("/{case_id}", response_model=CaseResponse, response_model_exclude_none=True)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get a specific case by ID."""

    case = CaseService.get_case(db=db, case_id=case_id, organization_id=organization_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseResponse.from_orm(case)


@router.get("/number/{case_number}", response_model=CaseResponse, response_model_exclude_none=True)
def get_case_by_number(
    case_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get a specific case by case number."""

    case = CaseService.get_case_by_number(
        db=db,
        case_number=case_number,
        organization_id=organization_id
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseResponse.from_orm(case)


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Update a specific case."""

    try:
        case = CaseService.update_case(
            db=db,
            case_id=case_id,
            case_update=case_update,
            organization_id=organization_id,
            updated_by_id=current_user.id
        )
        return CaseResponse.from_orm(case)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Case not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update case")


@router.delete("/{case_id}", response_model=SuccessResponse)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Delete a specific case (soft delete)."""

    try:
        success = CaseService.delete_case(
            db=db,
            case_id=case_id,
            organization_id=organization_id,
            deleted_by_id=current_user.id
        )
        return SuccessResponse(
            success=success,
            message="Case deleted successfully"
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Case not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete case")


@router.post("/{case_id}/close", response_model=CaseResponse)
def close_case(
    case_id: int,
    closure_reason: str = Query(..., description="Reason for closing the case"),
    final_notes: Optional[str] = Query(None, description="Final notes for the case"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Close a case."""

    try:
        case = CaseService.close_case(
            db=db,
            case_id=case_id,
            organization_id=organization_id,
            closed_by_id=current_user.id,
            closure_reason=closure_reason,
            final_notes=final_notes
        )
        return CaseResponse.from_orm(case)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Case not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to close case")


@router.post("/{case_id}/reopen", response_model=CaseResponse)
def reopen_case(
    case_id: int,
    reason: str = Query(..., description="Reason for reopening the case"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Reopen a closed case."""

    try:
        case = CaseService.reopen_case(
            db=db,
            case_id=case_id,
            organization_id=organization_id,
            reopened_by_id=current_user.id,
            reason=reason
        )
        return CaseResponse.from_orm(case)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Case not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to reopen case")


@router.post("/bulk", response_model=CaseBulkResult)
def bulk_update_cases(
    bulk_action: CaseBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Perform bulk operations on cases."""

    try:
        # Import here to avoid circular imports
        from services.case import CaseService

        result = CaseService.bulk_update_cases(
            db=db,
            bulk_action=bulk_action,
            organization_id=organization_id,
            updated_by_id=current_user.id
        )
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to perform bulk operation")
