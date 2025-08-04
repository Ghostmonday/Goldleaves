from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
import secrets
import logging

from core.config import settings
from core.database import get_db
from apps.backend.models.user import User
from apps.backend.services.auth_service import (
    create_access_token, 
    create_refresh_token, 
    hash_password, 
    verify_password,
    decode_token
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic Models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Updated for Pydantic v2

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes

class UserResponse(BaseModel):
    user: UserRead
    message: str

# Auth Helper Functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        token_type = payload.get("type", "access")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

# Route Handlers
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse with user data and success message
        
    Raises:
        HTTPException: 400 if user already exists
        HTTPException: 500 if registration fails
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False  # Email verification required
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user registered: {db_user.email} (ID: {db_user.id})")
        
        return UserResponse(
            user=UserRead.model_validate(db_user),
            message="User registered successfully. Please verify your email."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Args:
        login_data: User login credentials
        db: Database session
        
    Returns:
        Token with access and refresh tokens
        
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 401 if user is not verified (optional enforcement)
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        logger.warning(f"Login attempt with non-existent email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Login attempt with wrong password for user: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Optional: Enforce email verification
    # Uncomment if you want to require email verification before login
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Email verification required"
    #     )
    
    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token, refresh_expires_at = create_refresh_token(user.id)
    
    # Store refresh token in database
    from apps.backend.models import RefreshToken
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=refresh_expires_at,
        is_active=True
    )
    db.add(db_refresh_token)
    db.commit()
    
    logger.info(f"User logged in successfully: {user.email} (ID: {user.id})")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60
    )

@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        UserRead with current user information
    """
    return UserRead.model_validate(current_user)

@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Logout user by revoking all refresh tokens.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Revoke all active refresh tokens for the user
    from apps.backend.models import RefreshToken
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    logger.info(f"User logged out: {current_user.email} (ID: {current_user.id})")
    
    return {"message": "Logged out successfully"}
