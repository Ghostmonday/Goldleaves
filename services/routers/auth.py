# routers/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging
from typing import Optional

from schemas import (
    EmailVerificationRequest, 
    EmailVerificationResponse, 
    AdminUserResponse, 
    AdminUsersListResponse,
    UserRole,
    UserStatus
)
from token_service import (
    verify_email_token, 
    revoke_token,
    verify_token,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError
)
from core.email_utils import send_verification_email
from models.user import get_user_by_id, get_all_users, update_user_email_verified

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current user from JWT token.
    
    Args:
        credentials: JWT credentials from Authorization header
        
    Returns: Dict[str, Any]: Current user payload
        
    Raises:
        HTTPException: If token is invalid, expired, or revoked
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenInvalidError, TokenRevokedError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to check admin role
async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> dict:
    """
    Require admin role for accessing protected endpoints.
    
    Args:
        current_user: Current user payload from token
        
    Returns: Dict[str, Any]: Current user payload if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    user_role = current_user.get("role", "user")
    if user_role != "admin":
        logger.warning(f"Non-admin user {current_user.get('sub')} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: EmailVerificationRequest):
    """
    Verify user email using verification token.
    
    This endpoint accepts an email verification token, validates it,
    and activates the user's email verification status.
    
    Args:
        request: Email verification request containing the token
        
    Returns:
        EmailVerificationResponse: Success response with verification details
        
    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    try:
        # Verify the email verification token
        token_payload = await verify_email_token(request.token)
        if not token_payload:
            logger.warning("Invalid email verification token provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email verification token"
            )
            
        user_id = token_payload["user_id"]
        email = token_payload["email"]
        
        logger.info(f"Verifying email for user {user_id} with email {email}")
        
        # Get user from database
        user = await get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found during email verification")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email matches user's current email
        if user.email.lower() != email.lower():
            logger.warning(f"Email mismatch for user {user_id}: token email {email}, user email {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification token does not match user's current email"
            )
        
        # Check if email is already verified
        if user.is_email_verified:
            logger.info(f"Email {email} for user {user_id} is already verified")
            # Revoke the token since it's no longer needed (extract jti from original token)
            try:
                import jwt
                from config import settings
                payload = jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
                jti = payload.get("jti")
                if jti:
                    await revoke_token(request.token)
            except Exception:
                pass  # Continue even if revocation fails
            
            return EmailVerificationResponse(
                message="Email is already verified",
                user_id=user_id,
                email=email,
                verified_at=user.email_verified_at or datetime.utcnow()
            )
        
        # Update user's email verification status
        verification_time = datetime.utcnow()
        await update_user_email_verified(user_id, True, verification_time)
        
        # Revoke the verification token after successful verification
        try:
            await revoke_token(request.token)
        except Exception as e:
            logger.warning(f"Failed to revoke token after verification: {str(e)}")
            # Continue even if revocation fails
        
        logger.info(f"Email {email} successfully verified for user {user_id}")
        
        return EmailVerificationResponse(
            message="Email verified successfully",
            user_id=user_id,
            email=email,
            verified_at=verification_time
        )
        
    except TokenExpiredError:
        logger.warning(f"Expired email verification token provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification token has expired. Please request a new verification email."
        )
    except (TokenInvalidError, TokenRevokedError) as e:
        logger.warning(f"Invalid email verification token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email verification token"
        )
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during email verification"
        )

@router.get("/admin/users", response_model=AdminUsersListResponse)
async def get_admin_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Get paginated list of users for admin dashboard.
    
    This endpoint provides admin users with access to user management data,
    including filtering and search capabilities.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of users per page (1-100)
        role: Filter by user role
        status: Filter by user status
        search: Search term for email/username
        current_user: Current admin user (injected by dependency)
        
    Returns:
        AdminUsersListResponse: Paginated list of users with metadata
        
    Raises:
        HTTPException: If request parameters are invalid
    """
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        logger.info(f"Admin {current_user.get('sub')} requested users list: page={page}, size={page_size}")
        
        # Build filters
        filters = {}
        if role:
            filters["role"] = role.value
        if status:
            filters["status"] = status.value
        if search:
            filters["search"] = search.strip()
        
        # Get users from database with pagination
        users_data = await get_all_users(
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        # Convert to response format
        admin_users = []
        for user in users_data["users"]:
            admin_user = AdminUserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                role=UserRole(user.role),
                status=UserStatus(user.status),
                is_email_verified=user.is_email_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                login_count=user.login_count or 0
            )
            admin_users.append(admin_user)
        
        # Calculate total pages
        total_pages = (users_data["total_count"] + page_size - 1) // page_size
        
        logger.info(f"Returning {len(admin_users)} users for admin {current_user.get('sub')}")
        
        return AdminUsersListResponse(
            users=admin_users,
            total_count=users_data["total_count"],
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving admin users list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving users"
        )

@router.post("/admin/users/{user_id}/resend-verification")
async def resend_verification_email(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Resend email verification for a specific user (admin only).
    
    Args:
        user_id: ID of the user to resend verification for
        current_user: Current admin user (injected by dependency)
        
    Returns: Dict[str, Any]: Success message
        
    Raises:
        HTTPException: If user not found or verification fails
    """
    try:
        # Get user from database
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if email is already verified
        if user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User's email is already verified"
            )
        
        # Send verification email
        success = await send_verification_email(user.id, user.email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        logger.info(f"Admin {current_user.get('sub')} resent verification email to user {user_id}")
        
        return {
            "message": "Verification email sent successfully",
            "user_id": user_id,
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending verification email"
        )
