"""Documents API endpoints."""

from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter(prefix="/documents")


@router.get("/")
async def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List documents."""
    return {"message": "Documents endpoint - implementation in progress"}


@router.post("/")
async def create_document(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create document."""
    return {"message": "Create document endpoint"}
