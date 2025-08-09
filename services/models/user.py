# models/user.py

import enum
import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy setup (would typically be in a separate database module)
Base = declarative_base()

# Enums
class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin" 
    MODERATOR = "moderator"

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"

class User(Base):
    """
    User model for authentication and user management.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=text("gen_random_uuid()"))
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Role and status
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING_VERIFICATION)
    
    # Email verification
    is_email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Login tracking
    login_count = Column(Integer, nullable=False, default=0)
    
    # Additional fields
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert user instance to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role.value,
            "status": self.status.value,
            "is_email_verified": self.is_email_verified,
            "email_verified_at": self.email_verified_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "login_count": self.login_count,
            "bio": self.bio,
            "avatar_url": self.avatar_url
        }

# Database session setup (would typically be in a separate database module)
# This is a simplified setup for demonstration
DATABASE_URL = "postgresql://user:password@localhost/goldleaves_db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock database functions (in a real app, these would use actual database operations)
_mock_users_db: Dict[str, User] = {}

async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        user_id (str): User ID to search for
        
    Returns:
        Optional[User]: User instance if found, None otherwise
    """
    try:
        # In a real application, this would query the database
        # For now, using mock data
        user = _mock_users_db.get(user_id)
        if user:
            logger.debug(f"User {user_id} found")
        else:
            logger.debug(f"User {user_id} not found")
        return user
        
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {str(e)}")
        return None

async def get_user_by_email(email: str) -> Optional[User]:
    """
    Get user by email address.
    
    Args:
        email (str): Email address to search for
        
    Returns:
        Optional[User]: User instance if found, None otherwise
    """
    try:
        # In a real application, this would query the database
        for user in _mock_users_db.values():
            if user.email.lower() == email.lower():
                logger.debug(f"User with email {email} found")
                return user
        
        logger.debug(f"User with email {email} not found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        return None

async def get_all_users(
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Get paginated list of users with optional filtering.
    
    Args:
        page (int): Page number (1-indexed)
        page_size (int): Number of users per page
        filters (Optional[Dict]): Optional filters (role, status, search)
        
    Returns:
        Dict containing users list and pagination metadata
    """
    try:
        # In a real application, this would query the database with filters and pagination
        # For now, using mock data
        all_users = list(_mock_users_db.values())
        
        # Apply filters
        if filters:
            if filters.get("role"):
                all_users = [u for u in all_users if u.role.value == filters["role"]]
            
            if filters.get("status"):
                all_users = [u for u in all_users if u.status.value == filters["status"]]
            
            if filters.get("search"):
                search_term = filters["search"].lower()
                all_users = [
                    u for u in all_users 
                    if search_term in u.email.lower() or 
                       (u.username and search_term in u.username.lower()) or
                       (u.first_name and search_term in u.first_name.lower()) or
                       (u.last_name and search_term in u.last_name.lower())
                ]
        
        # Sort by created_at descending
        all_users.sort(key=lambda x: x.created_at, reverse=True)
        
        # Calculate pagination
        total_count = len(all_users)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_users = all_users[start_index:end_index]
        
        logger.info(f"Retrieved {len(paginated_users)} users (page {page}/{page_size})")
        
        return {
            "users": paginated_users,
            "total_count": total_count,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        return {
            "users": [],
            "total_count": 0,
            "page": page,
            "page_size": page_size
        }

async def update_user_email_verified(
    user_id: str, 
    is_verified: bool, 
    verified_at: Optional[datetime] = None
) -> bool:
    """
    Update user's email verification status.
    
    Args:
        user_id (str): User ID to update
        is_verified (bool): Whether email is verified
        verified_at (Optional[datetime]): Verification timestamp
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for email verification update")
            return False
        
        user.is_email_verified = is_verified
        user.email_verified_at = verified_at or datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Update status to active if verifying email
        if is_verified and user.status == UserStatus.PENDING_VERIFICATION:
            user.status = UserStatus.ACTIVE
        
        logger.info(f"Updated email verification for user {user_id}: verified={is_verified}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating email verification for user {user_id}: {str(e)}")
        return False

async def create_user(
    email: str,
    password_hash: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: UserRole = UserRole.USER
) -> Optional[User]:
    """
    Create a new user.
    
    Args:
        email (str): User's email address
        password_hash (str): Hashed password
        username (Optional[str]): Username
        first_name (Optional[str]): First name
        last_name (Optional[str]): Last name
        role (UserRole): User role
        
    Returns:
        Optional[User]: Created user instance if successful, None otherwise
    """
    try:
        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())
        
        # Create user instance
        user = User(
            id=user_id,
            email=email.lower(),
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status=UserStatus.PENDING_VERIFICATION,
            is_email_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            login_count=0
        )
        
        # Store in mock database
        _mock_users_db[user_id] = user
        
        logger.info(f"Created new user {user_id} with email {email}")
        return user
        
    except Exception as e:
        logger.error(f"Error creating user with email {email}: {str(e)}")
        return None

async def update_user_last_login(user_id: str) -> bool:
    """
    Update user's last login timestamp and increment login count.
    
    Args:
        user_id (str): User ID to update
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        user = _mock_users_db.get(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for last login update")
            return False
        
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        user.updated_at = datetime.utcnow()
        
        logger.debug(f"Updated last login for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating last login for user {user_id}: {str(e)}")
        return False

# Initialize some mock data for testing
async def init_mock_data():
    """Initialize mock data for testing purposes."""
    try:
        # Create admin user
        admin_user = await create_user(
            email="admin@goldleaves.com",
            password_hash="$2b$12$dummy_hash_for_admin",
            username="admin",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN
        )
        if admin_user:
            admin_user.is_email_verified = True
            admin_user.status = UserStatus.ACTIVE
            admin_user.email_verified_at = datetime.utcnow()
        
        # Create regular user
        regular_user = await create_user(
            email="user@example.com",
            password_hash="$2b$12$dummy_hash_for_user",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.USER
        )
        
        logger.info("Mock data initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing mock data: {str(e)}")

# Initialize mock data
import asyncio

asyncio.create_task(init_mock_data())
