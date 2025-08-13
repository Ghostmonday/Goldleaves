"""
Token refresh endpoint for JWT authentication.
Handles refresh token validation and rotation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import jwt
import logging

from core.config import settings
from core.database import get_db
from apps.backend.models import User, RefreshToken
from apps.backend.services.auth_service import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

router = APIRouter()

# === Request Schema ===
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# === Response Schema ===
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes

@router.post("/token/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh an access token using a valid refresh token.

    This endpoint:
    1. Validates the refresh token JWT
    2. Checks if the token exists and is active in the database
    3. Revokes the old refresh token
    4. Creates new access and refresh tokens
    5. Returns the new token pair

    Args:
        request: RefreshTokenRequest containing the refresh token
        db: Database session dependency

    Returns:
        TokenResponse with new access and refresh tokens

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    token = request.refresh_token

    try:
        # Decode JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )

        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id = int(user_id_str)

        # Check token in DB
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.is_active == True,
            RefreshToken.user_id == user_id
        ).first()

        if not db_token:
            logger.warning(f"Refresh token not found in database for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not found or revoked"
            )

        if db_token.expires_at < datetime.utcnow():
            logger.warning(f"Expired refresh token used for user {user_id}")
            # Mark as inactive
            db_token.is_active = False
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )

        # Verify user still exists and is active
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()

        if not user:
            logger.warning(f"User {user_id} not found or inactive during token refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Revoke old token and create new ones
        db_token.is_active = False

        new_refresh_token, refresh_expires_at = create_refresh_token(user_id)
        new_access_token = create_access_token(user_id)

        # Save new refresh token to database
        new_db_token = RefreshToken(
            user_id=user_id,
            token=new_refresh_token,
            expires_at=refresh_expires_at,
            is_active=True
        )
        db.add(new_db_token)
        db.commit()

        logger.info(f"Token refreshed successfully for user {user_id}")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.jwt_expiration_minutes * 60  # Convert to seconds
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Expired refresh token signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except ValueError:
        logger.warning("Invalid user ID in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
