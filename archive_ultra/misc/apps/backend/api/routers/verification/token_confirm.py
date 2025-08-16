"""
Email verification token confirmation endpoint.
Handles confirming email verification using tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from apps.backend.schemas.verification import (
    ConfirmVerificationRequest,
    ConfirmVerificationResponse,
    VerificationErrorResponse
)
from apps.backend.services.email_verification_service import EmailVerificationService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/confirm",
    response_model=ConfirmVerificationResponse,
    responses={
        401: {"model": VerificationErrorResponse, "description": "Invalid or expired token"},
        404: {"model": VerificationErrorResponse, "description": "User not found"},
        500: {"model": VerificationErrorResponse, "description": "Internal server error"}
    },
    summary="Confirm email verification",
    description="Confirm user's email verification using the token from their email"
)
def confirm_email_verification(
    request: ConfirmVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm email verification using token.

    This endpoint:
    1. Validates and decodes the verification token
    2. Finds the user associated with the token
    3. Checks token matches and hasn't expired
    4. Marks the user as verified
    5. Clears verification token fields

    Args:
        request: ConfirmVerificationRequest containing the token
        db: Database session dependency

    Returns:
        ConfirmVerificationResponse with success status and user info

    Raises:
        HTTPException: 401 if token is invalid or expired
        HTTPException: 404 if user not found
        HTTPException: 500 for unexpected errors
    """
    try:
        result = EmailVerificationService.confirm_email_verification(
            db=db,
            token=request.token
        )

        logger.info(f"Email verification confirmed successfully for user {result.get('user_id')}")

        return ConfirmVerificationResponse(
            success=result["success"],
            message=result["message"],
            user_id=result.get("user_id")
        )

    except ValueError as e:
        error_message = str(e)
        logger.warning(f"Email verification failed: {error_message}")

        # Map specific errors to appropriate HTTP status codes
        if "expired" in error_message.lower():
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "invalid" in error_message.lower() or "revoked" in error_message.lower():
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )

    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
