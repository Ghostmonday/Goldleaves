"""
Email verification token resend endpoint.
Handles resending verification emails to unverified users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from apps.backend.schemas.verification import (
    ResendVerificationRequest, 
    VerificationResponse,
    VerificationErrorResponse
)
from apps.backend.services.email_verification_service import EmailVerificationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/resend",
    response_model=VerificationResponse,
    responses={
        400: {"model": VerificationErrorResponse, "description": "Bad request - user not found or already verified"},
        500: {"model": VerificationErrorResponse, "description": "Internal server error"}
    },
    summary="Resend email verification token",
    description="Resend a verification email to an unverified user with a new token"
)
def resend_verification_email(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification email to user.
    
    This endpoint:
    1. Validates the email address exists in the system
    2. Checks that the user is not already verified
    3. Generates a new verification token (invalidating any previous one)
    4. Updates the user record with new token and expiration
    5. Simulates sending the verification email
    
    Args:
        request: ResendVerificationRequest containing the email
        db: Database session dependency
        
    Returns:
        VerificationResponse with success status and token info
        
    Raises:
        HTTPException: 400 if user not found or already verified
        HTTPException: 500 for unexpected errors
    """
    try:
        result = EmailVerificationService.resend_verification_email(
            db=db,
            email=request.email
        )
        
        logger.info(f"Verification email resent successfully to {request.email}")
        
        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_at=result["expires_at"],
            token=result.get("token")  # Only included in development
        )
        
    except ValueError as e:
        logger.warning(f"Verification email resend failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error resending verification email to {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
