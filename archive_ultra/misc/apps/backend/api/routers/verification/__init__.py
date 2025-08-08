"""
Email verification router combining all verification endpoints.
"""

from fastapi import APIRouter
from apps.backend.api.routers.verification.token_send import router as send_router
from apps.backend.api.routers.verification.token_confirm import router as confirm_router
from apps.backend.api.routers.verification.token_resend import router as resend_router

# Create the main verification router
router = APIRouter()

# Include all verification endpoints
router.include_router(send_router, tags=["Email Verification"])
router.include_router(confirm_router, tags=["Email Verification"])
router.include_router(resend_router, tags=["Email Verification"])
