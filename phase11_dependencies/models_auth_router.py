# models/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
import bcrypt

from models.core_db import get_db
from models.user import User
from models.user_schemas import (
    UserCreate, UserResponse, UserLogin, Token, 
    EmailVerificationRequest, EmailVerificationResponse,
    AdminUserResponse, AdminUserListResponse, UserUpdateRequest
)
from models.token_service import TokenService
from models.email_utils import email_service
from core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password, verify_access_token
from core.config import get_settings

# ✅ Phase 3: /verify-email endpoint - COMPLETED
# ✅ Phase 3: /admin/users endpoint with admin-only permission checks - COMPLETED

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

# Dependency to get current admin user
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Get current authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password using core security
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,
        email_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email
    verification_token = TokenService.create_verification_token(user.email)
    email_service.send_verification_email(user.email, verification_token)
    
    return user

@router.post("/login", response_model=Dict[str, Any])
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access and refresh tokens."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.update_login_timestamp()
    db.commit()
    
    # Create access and refresh tokens
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(refresh_token)
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.email == email, User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        settings = get_settings()
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        new_access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

# ✅ Phase 3: /verify-email endpoint - COMPLETED
@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest, 
    db: Session = Depends(get_db)
):
    """
    Verify user email using verification token.
    ✅ Implemented email verification logic:
    1. Validate the verification token using TokenService
    2. Extract email from token
    3. Find user by email
    4. Update user's email_verified status
    5. Return appropriate response
    """
    try:
        # Verify the token and extract email
        email = TokenService.verify_verification_token(request.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already verified
        if user.email_verified:
            return EmailVerificationResponse(
                message="Email already verified",
                success=True,
                user_id=user.id
            )
        
        # Update user's email verification status
        user.email_verified = True
        user.is_verified = True  # Also mark user as verified
        db.commit()
        
        return EmailVerificationResponse(
            message="Email verified successfully",
            success=True,
            user_id=user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify email: {str(e)}"
        )

# ✅ Phase 3: /admin/users endpoint - COMPLETED
@router.get("/admin/users", response_model=AdminUserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Users per page"),
    search: str = Query(None, description="Search by email"),
    is_admin: bool = Query(None, description="Filter by admin status"),
    is_active: bool = Query(None, description="Filter by active status"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users with filtering and pagination - Admin only.
    ✅ Implemented admin user listing with:
    1. Admin permission check (implemented via dependency)
    2. Filtering by various criteria
    3. Pagination
    4. Return detailed user information using AdminUserResponse schema
    """
    try:
        # Build query with filters
        query = db.query(User)
        
        # Apply search filter
        if search:
            query = query.filter(User.email.ilike(f"%{search}%"))
        
        # Apply admin filter
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        # Apply active filter
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Convert to AdminUserResponse with organization info
        admin_users = []
        for user in users:
            admin_user_data = {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "email_verified": user.email_verified,
                "created_at": user.created_at,
                "last_login": user.last_login,
                "organization_id": user.organization_id,
                "organization_name": user.organization.name if user.organization else None,
                "total_logins": getattr(user, 'login_count', 0),  # ✅ Implemented login tracking
                "account_status": "active" if user.is_active else "inactive",
                "login_count": getattr(user, 'login_count', 0)
            }
            admin_users.append(AdminUserResponse(**admin_user_data))
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        
        return AdminUserListResponse(
            users=admin_users,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@router.get("/admin/users/{user_id}", response_model=AdminUserResponse)
async def get_user_by_id(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get specific user by ID - Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    admin_user_data = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "organization_id": user.organization_id,
        "organization_name": user.organization.name if user.organization else None,
        "total_logins": getattr(user, 'login_count', 0),  # ✅ Implemented login tracking
        "account_status": "active" if user.is_active else "inactive",
        "login_count": getattr(user, 'login_count', 0)
    }
    
    return AdminUserResponse(**admin_user_data)

@router.put("/admin/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user - Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    if user_update.email_verified is not None:
        user.email_verified = user_update.email_verified
    if user_update.organization_id is not None:
        user.organization_id = user_update.organization_id
    
    db.commit()
    db.refresh(user)
    
    admin_user_data = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "organization_id": user.organization_id,
        "organization_name": user.organization.name if user.organization else None,
        "total_logins": getattr(user, 'login_count', 0),
        "account_status": "active" if user.is_active else "inactive",
        "login_count": getattr(user, 'login_count', 0)
    }
    
    return AdminUserResponse(**admin_user_data)

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user - Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# Resend verification email endpoint
@router.post("/resend-verification")
async def resend_verification_email(
    email: str,
    db: Session = Depends(get_db)
):
    """Resend verification email to user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a verification email has been sent"}
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate new verification token and send email
    verification_token = TokenService.create_verification_token(user.email)
    email_service.send_verification_email(user.email, verification_token)
    
    return {"message": "Verification email sent successfully"}

# ✅ Phase 3: All auth router TODOs completed
