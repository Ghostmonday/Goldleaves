"""
Email verification token send endpoint.
Handles generating and sending verification emails to users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from apps.backend.schemas.verification import (
    SendVerificationRequest, 
    VerificationResponse,
    VerificationErrorResponse
)
from apps.backend.services.email_verification_service import EmailVerificationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/send", 
    response_model=VerificationResponse,
    responses={
        400: {"model": VerificationErrorResponse, "description": "Bad request - user not found or already verified"},
        500: {"model": VerificationErrorResponse, "description": "Internal server error"}
    },
    summary="Send email verification token",
    description="Generate and send a verification email to the specified email address"
)
def send_verification_email(
    request: SendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Send verification email to user.
    
    This endpoint:
    1. Validates the email address exists in the system
    2. Checks that the user is not already verified
    3. Generates a new verification token
    4. Updates the user record with token and expiration
    5. Simulates sending the verification email
    
    Args:
        request: SendVerificationRequest containing the email
        db: Database session dependency
        
    Returns:
        VerificationResponse with success status and token info
        
    Raises:
        HTTPException: 400 if user not found or already verified
        HTTPException: 500 for unexpected errors
    """
    try:
        result = EmailVerificationService.send_verification_email(
            db=db, 
            email=request.email
        )
        
        logger.info(f"Verification email sent successfully to {request.email}")
        
        return VerificationResponse(
            success=result["success"],
            message=result["message"],
            expires_at=result["expires_at"],
            token=result.get("token")  # Only included in development
        )
        
    except ValueError as e:
        logger.warning(f"Verification email send failed for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error sending verification email to {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
