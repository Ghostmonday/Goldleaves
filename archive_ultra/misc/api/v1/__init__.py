"""API v1 package."""

from fastapi import APIRouter
from . import auth  # Only include auth for now

# Import notification router directly from notifications directory to avoid routers.__init__.py
from routers.notifications import router as notifications_router

router = APIRouter(prefix="/api/v1")

# Include core routers only
router.include_router(auth.router, tags=["authentication"])
router.include_router(notifications_router, tags=["notifications"])

__all__ = ["router"]
