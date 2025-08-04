"""
Authentication API endpoints.
Handles login, logout, token refresh, and user registration.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from core.database import get_db
from core.security import create_access_token, create_refresh_token, verify_token
from services.auth_service import AuthService
from schemas.auth import (
    Token, UserCreate, UserLogin, UserRegister, 
    PasswordReset, PasswordResetConfirm, EmailVerification
)
from schemas.base import SuccessResponse


router = APIRouter(prefix="/auth")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(db)


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
) -> SuccessResponse:
    """Register a new user account."""
    try:
        await service.register_user(user_data)
        return SuccessResponse(
            message="Registration successful. Please check your email for verification instructions."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
) -> Token:
    """Login with username/email and password."""
    try:
        tokens = await service.authenticate_user(form_data.username, form_data.password)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    service: AuthService = Depends(get_auth_service)
) -> Token:
    """Refresh access token using refresh token."""
    try:
        tokens = await service.refresh_access_token(refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    verification_data: EmailVerification,
    service: AuthService = Depends(get_auth_service)
) -> SuccessResponse:
    """Verify user email with verification token."""
    try:
        await service.verify_email(verification_data.token)
        return SuccessResponse(message="Email verified successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    reset_data: PasswordReset,
    service: AuthService = Depends(get_auth_service)
) -> SuccessResponse:
    """Request password reset."""
    await service.request_password_reset(reset_data.email)
    return SuccessResponse(
        message="If the email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    service: AuthService = Depends(get_auth_service)
) -> SuccessResponse:
    """Reset password with reset token."""
    try:
        await service.reset_password(reset_data.token, reset_data.new_password)
        return SuccessResponse(message="Password reset successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
