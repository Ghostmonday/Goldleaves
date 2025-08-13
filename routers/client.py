# routers/client.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.dependencies import get_current_active_user, get_current_organization_id
from core.exceptions import NotFoundError, ValidationError
from models.user import User
from schemas.base.pagination import PaginatedResponse
from schemas.base.responses import SuccessResponse
from schemas.client.core import (
    ClientBulkAction,
    ClientBulkResult,
    ClientCreate,
    ClientFilter,
    ClientResponse,
    ClientStats,
    ClientUpdate,
)
from services.client import ClientService

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    dependencies=[Depends(get_current_active_user)]
)


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Create a new client."""
    try:
        client = ClientService.create_client(
            db=db,
            client_data=client_data,
            organization_id=organization_id,
            created_by_id=current_user.id
        )
        return ClientResponse.from_orm(client)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create client")


@router.get("/", response_model=PaginatedResponse[ClientResponse], response_model_exclude_none=True)
def list_clients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search in client names, email, company"),
    client_type: Optional[str] = Query(None, description="Filter by client type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned user"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    order_by: str = Query("created_at", description="Field to order by"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Order direction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """List clients with filtering and pagination."""

    # Build filters
    filters = ClientFilter(
        search=search,
        client_type=client_type,
        status=status,
        priority=priority,
        assigned_to_id=assigned_to_id,
        tags=tags
    )

    clients, total = ClientService.list_clients(
        db=db,
        organization_id=organization_id,
        filters=filters,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_direction=order_direction
    )

    return PaginatedResponse(
        items=[ClientResponse.from_orm(client) for client in clients],
        total=total,
        page=skip // limit + 1,
        per_page=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/search", response_model=List[ClientResponse], response_model_exclude_none=True)
def search_clients(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Quick search for clients (for autocomplete/typeahead)."""

    clients = ClientService.search_clients(
        db=db,
        organization_id=organization_id,
        search_term=q,
        limit=limit
    )

    return [ClientResponse.from_orm(client) for client in clients]


@router.get("/stats", response_model=ClientStats, response_model_exclude_none=True)
def get_client_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get client statistics for the organization."""

    return ClientService.get_client_stats(db=db, organization_id=organization_id)


@router.get("/{client_id}", response_model=ClientResponse, response_model_exclude_none=True)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get a specific client by ID."""

    client = ClientService.get_client(db=db, client_id=client_id, organization_id=organization_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse.from_orm(client)


@router.get("/slug/{slug}", response_model=ClientResponse, response_model_exclude_none=True)
def get_client_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get a specific client by slug."""

    client = ClientService.get_client_by_slug(db=db, slug=slug, organization_id=organization_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse.from_orm(client)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Update a specific client."""

    try:
        client = ClientService.update_client(
            db=db,
            client_id=client_id,
            client_update=client_update,
            organization_id=organization_id,
            updated_by_id=current_user.id
        )
        return ClientResponse.from_orm(client)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Client not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update client")


@router.delete("/{client_id}", response_model=SuccessResponse)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Delete a specific client (soft delete)."""

    try:
        success = ClientService.delete_client(
            db=db,
            client_id=client_id,
            organization_id=organization_id
        )
        return SuccessResponse(
            success=success,
            message="Client deleted successfully"
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Client not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete client")


@router.post("/bulk", response_model=ClientBulkResult)
def bulk_update_clients(
    bulk_action: ClientBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Perform bulk operations on clients."""

    try:
        result = ClientService.bulk_update_clients(
            db=db,
            bulk_action=bulk_action,
            organization_id=organization_id,
            updated_by_id=current_user.id
        )
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to perform bulk operation")


@router.get("/{client_id}/cases")
def get_client_cases(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """Get all cases for a specific client."""

    try:
        cases = ClientService.get_cases_for_client(
            db=db,
            client_id=client_id,
            organization_id=organization_id
        )

        # Import here to avoid circular imports
        from schemas.case.core import CaseResponse
        return [CaseResponse.from_orm(case) for case in cases]

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Client not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get client cases")
