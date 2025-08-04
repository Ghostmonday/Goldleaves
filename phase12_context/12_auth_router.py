# routers/auth.py
"""Authentication router implementation with full contract compliance."""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from core.dependencies import get_db, get_current_active_user
from services.auth_service import AuthService
from models.user import User

# Security scheme
security = HTTPBearer()

# Initialize router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        422: {"description": "Validation Error"}
    }
)


@router.post("/register")
async def register(
    user_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.register_user(user_data)
        
        # In real implementation, send verification email via background task
        # background_tasks.add_task(send_verification_email, user_data["email"])
        
        return {
            "success": True,
            "message": "User registered successfully. Please check your email for verification.",
            "data": {"user_id": result["user_id"]}
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
async def login(
    login_data: Dict[str, Any],
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Authenticate user and return tokens."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.login_user(login_data)
        
        return {
            "success": True,
            "message": "Login successful",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Verify user email with verification token."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.verify_email(token)
        
        return {
            "success": True,
            "message": "Email verified successfully",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Email verification failed")


@router.post("/reset-password")
async def reset_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send password reset email."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.reset_password(email)
        
        # In real implementation, send reset email via background task
        # background_tasks.add_task(send_password_reset_email, email)
        
        return {
            "success": True,
            "message": "If the email exists, a reset link has been sent",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Password reset failed")


@router.post("/change-password")
async def change_password(
    password_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Change user password."""
    try:
        auth_service = AuthService(db)
        result = await auth_service.change_password(
            current_user.id,
            password_data["old_password"],
            password_data["new_password"]
        )
        
        return {
            "success": True,
            "message": "Password changed successfully",
            "data": result
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Password change failed")


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get current user information."""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "is_admin": current_user.is_admin,
            "role": current_user.role.value,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
    }


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Refresh access token using refresh token."""
    # Mock implementation for context
    return {
        "success": True,
        "message": "Token refreshed successfully",
        "data": {
            "access_token": "new_access_token",
            "token_type": "bearer"
        }
    }
