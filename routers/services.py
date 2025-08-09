# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Complete service layer implementations

"""Service layer implementations for business logic."""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    TokenSchema,
    UserLoginSchema,
    UserProfileSchema,
    UserRegistrationSchema,
    UserRole,
    UserStatus,
)

logger = logging.getLogger(__name__)


# ===== MOCK DATABASE =====
class MockDatabase:
    """Mock database for demonstration purposes."""
    
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.organizations: Dict[str, Dict] = {}
        self.audit_logs: List[Dict] = []
        self.email_verification_tokens: Dict[str, Dict] = {}
        self.password_reset_tokens: Dict[str, Dict] = {}
        self.refresh_tokens: Dict[str, Dict] = {}
        
        # Initialize with admin user
        admin_id = str(uuid.uuid4())
        self.users[admin_id] = {
            "id": admin_id,
            "username": "admin",
            "email": "admin@goldleaves.com",
            "password_hash": self._hash_password("AdminPass123!"),
            "full_name": "System Administrator",
            "role": UserRole.ADMIN,
            "status": UserStatus.ACTIVE,
            "organization_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "email_verified": True
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (in production, use bcrypt)."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return self._hash_password(password) == password_hash

# Global database instance
db = MockDatabase()

# ===== USER SERVICE =====
class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    async def create_user(user_data: UserRegistrationSchema) -> Dict[str, Any]:
        """Create a new user."""
        # Check if username or email already exists
        for user in db.users.values():
            if user["username"] == user_data.username:
                raise ValueError("Username already exists")
            if user["email"] == user_data.email:
                raise ValueError("Email already exists")
        
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": db._hash_password(user_data.password),
            "full_name": user_data.full_name,
            "role": UserRole.USER,
            "status": UserStatus.PENDING_VERIFICATION,
            "organization_id": user_data.organization_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "email_verified": False
        }
        
        db.users[user_id] = user
        
        # Create email verification token
        verification_token = secrets.token_urlsafe(32)
        db.email_verification_tokens[verification_token] = {
            "user_id": user_id,
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        await AuditService.log_action(
            user_id=user_id,
            action="user_created",
            resource_type="user",
            resource_id=user_id,
            details={"username": user_data.username, "email": user_data.email}
        )
        
        return {
            "user_id": user_id,
            "verification_token": verification_token,
            "user": UserProfileSchema(**user).dict()
        }
    
    @staticmethod
    async def authenticate_user(login_data: UserLoginSchema) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials."""
        user = None
        
        # Find user by username or email
        for u in db.users.values():
            if (u["username"] == login_data.username_or_email or 
                u["email"] == login_data.username_or_email):
                user = u
                break
        
        if not user or not db._verify_password(login_data.password, user["password_hash"]):
            await AuditService.log_action(
                user_id=None,
                action="login_failed",
                resource_type="user",
                resource_id=None,
                details={"attempted_username": login_data.username_or_email}
            )
            return None
        
        if user["status"] != UserStatus.ACTIVE:
            await AuditService.log_action(
                user_id=user["id"],
                action="login_failed_inactive",
                resource_type="user",
                resource_id=user["id"],
                details={"status": user["status"]}
            )
            return None
        
        # Update last login
        user["last_login"] = datetime.utcnow()
        user["updated_at"] = datetime.utcnow()
        
        await AuditService.log_action(
            user_id=user["id"],
            action="login_success",
            resource_type="user",
            resource_id=user["id"],
            details={"username": user["username"]}
        )
        
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return db.users.get(user_id)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        for user in db.users.values():
            if user["email"] == email:
                return user
        return None
    
    @staticmethod
    async def update_user(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information."""
        if user_id not in db.users:
            return None
        
        user = db.users[user_id]
        original_data = user.copy()
        
        # Update allowed fields
        for field, value in update_data.items():
            if field in ["full_name", "email", "role", "status", "email_verified", "organization_id"]:
                user[field] = value
        
        user["updated_at"] = datetime.utcnow()
        
        await AuditService.log_action(
            user_id=user_id,
            action="user_updated",
            resource_type="user",
            resource_id=user_id,
            details={
                "updated_fields": List[Any](update_data.keys()),
                "original": {k: v for k, v in original_data.items() if k in update_data}
            }
        )
        
        return user
    
    @staticmethod
    async def verify_email(token: str) -> bool:
        """Verify email using token."""
        if token not in db.email_verification_tokens:
            return False
        
        token_data = db.email_verification_tokens[token]
        if datetime.utcnow() > token_data["expires_at"]:
            del db.email_verification_tokens[token]
            return False
        
        user_id = token_data["user_id"]
        if user_id in db.users:
            user = db.users[user_id]
            user["email_verified"] = True
            user["status"] = UserStatus.ACTIVE
            user["updated_at"] = datetime.utcnow()
            
            await AuditService.log_action(
                user_id=user_id,
                action="email_verified",
                resource_type="user",
                resource_id=user_id,
                details={"email": user["email"]}
            )
        
        del db.email_verification_tokens[token]
        return True
    
    @staticmethod
    async def get_all_users(page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get all users with pagination."""
        users = list(db.users.values())
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_users = users[start:end]
        
        return {
            "users": [UserProfileSchema(**user).dict() for user in paginated_users],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete a user."""
        if user_id not in db.users:
            return False
        
        user = db.users[user_id]
        del db.users[user_id]
        
        await AuditService.log_action(
            user_id=user_id,
            action="user_deleted",
            resource_type="user",
            resource_id=user_id,
            details={"username": user["username"], "email": user["email"]}
        )
        
        return True

# ===== TOKEN SERVICE =====
class TokenService:
    """Service for JWT token operations."""
    
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    
    @staticmethod
    async def create_tokens(user: Dict[str, Any], remember_me: bool = False) -> TokenSchema:
        """Create access and refresh tokens."""
        user_id = user["id"]
        
        # Create mock tokens (in production, use proper JWT)
        access_token = f"access_{secrets.token_urlsafe(32)}"
        refresh_token = f"refresh_{secrets.token_urlsafe(32)}"
        
        expires_in = TokenService.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if remember_me:
            expires_in *= 24  # 24 hours for remember me
        
        # Store refresh token
        db.refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "expires_at": datetime.utcnow() + timedelta(days=TokenService.REFRESH_TOKEN_EXPIRE_DAYS),
            "access_token": access_token
        }
        
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            scope="read write"
        )
    
    @staticmethod
    async def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify access token and return user."""
        # In production, decode and verify JWT
        for refresh_token, token_data in db.refresh_tokens.items():
            if token_data["access_token"] == token:
                if datetime.utcnow() < token_data["expires_at"]:
                    return await UserService.get_user_by_id(token_data["user_id"])
        return None
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Optional[TokenSchema]:
        """Refresh access token using refresh token."""
        if refresh_token not in db.refresh_tokens:
            return None
        
        token_data = db.refresh_tokens[refresh_token]
        if datetime.utcnow() > token_data["expires_at"]:
            del db.refresh_tokens[refresh_token]
            return None
        
        user = await UserService.get_user_by_id(token_data["user_id"])
        if not user:
            return None
        
        # Delete old refresh token
        del db.refresh_tokens[refresh_token]
        
        # Create new tokens
        return await TokenService.create_tokens(user)
    
    @staticmethod
    async def revoke_token(refresh_token: str) -> bool:
        """Revoke refresh token."""
        if refresh_token in db.refresh_tokens:
            del db.refresh_tokens[refresh_token]
            return True
        return False

# ===== EMAIL SERVICE =====
class EmailService:
    """Service for email operations."""
    
    @staticmethod
    async def send_verification_email(email: str, token: str) -> bool:
        """Send email verification email (mock implementation)."""
        # In production, integrate with actual email service
        logger.info("[EMAIL] Verification email sent to %s with token: %s", email, token)
        return True
    
    @staticmethod
    async def send_password_reset_email(email: str, token: str) -> bool:
        """Send password reset email (mock implementation)."""
        logger.info("[EMAIL] Password reset email sent to %s with token: %s", email, token)
        return True
    
    @staticmethod
    async def send_welcome_email(email: str, username: str) -> bool:
        """Send welcome email (mock implementation)."""
        logger.info("[EMAIL] Welcome email sent to %s for user: %s", email, username)
        return True

# ===== ORGANIZATION SERVICE =====
class OrganizationService:
    """Service for organization operations."""
    
    @staticmethod
    async def get_organization_by_id(org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        return db.organizations.get(org_id)
    
    @staticmethod
    async def create_organization(name: str, description: str = None) -> Dict[str, Any]:
        """Create a new organization."""
        org_id = str(uuid.uuid4())
        organization = {
            "id": org_id,
            "name": name,
            "description": description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "user_count": 0
        }
        
        db.organizations[org_id] = organization
        return organization
    
    @staticmethod
    async def get_organization_users(org_id: str) -> List[Dict[str, Any]]:
        """Get all users in an organization."""
        users = []
        for user in db.users.values():
            if user.get("organization_id") == org_id:
                users.append(user)
        return users

# ===== AUDIT SERVICE =====
class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    async def log_action(
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> None:
        """Log an audit action."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow()
        }
        
        db.audit_logs.append(log_entry)
        
        # Keep only last 1000 logs for demo
        if len(db.audit_logs) > 1000:
            db.audit_logs = db.audit_logs[-1000:]
    
    @staticmethod
    async def get_audit_logs(
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering."""
        logs = db.audit_logs.copy()
        
        # Apply filters
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]
        if action:
            logs = [log for log in logs if log["action"] == action]
        if resource_type:
            logs = [log for log in logs if log["resource_type"] == resource_type]
        
        # Sort by timestamp descending and limit
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

# ===== SECURITY SERVICE =====
class SecurityService:
    """Service for security-related operations."""
    
    failed_attempts: Dict[str, List[datetime]] = {}
    blocked_ips: Dict[str, datetime] = {}
    
    @staticmethod
    async def check_rate_limit(identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> Tuple[bool, int]:
        """Check if identifier is rate limited."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if identifier in SecurityService.failed_attempts:
            SecurityService.failed_attempts[identifier] = [
                attempt for attempt in SecurityService.failed_attempts[identifier]
                if attempt > window_start
            ]
        
        attempts = len(SecurityService.failed_attempts.get(identifier, []))
        remaining = max(0, max_attempts - attempts)
        
        return attempts < max_attempts, remaining
    
    @staticmethod
    async def record_failed_attempt(identifier: str) -> None:
        """Record a failed attempt."""
        if identifier not in SecurityService.failed_attempts:
            SecurityService.failed_attempts[identifier] = []
        
        SecurityService.failed_attempts[identifier].append(datetime.utcnow())
    
    @staticmethod
    async def is_ip_blocked(ip_address: str) -> bool:
        """Check if IP is blocked."""
        if ip_address in SecurityService.blocked_ips:
            block_until = SecurityService.blocked_ips[ip_address]
            if datetime.utcnow() < block_until:
                return True
            else:
                del SecurityService.blocked_ips[ip_address]
        return False
    
    @staticmethod
    async def block_ip(ip_address: str, duration_minutes: int = 60) -> None:
        """Block an IP address."""
        SecurityService.blocked_ips[ip_address] = datetime.utcnow() + timedelta(minutes=duration_minutes)

# ===== SYSTEM SERVICE =====
class SystemService:
    """Service for system-level operations."""
    
    @staticmethod
    async def get_health_status() -> Dict[str, Any]:
        """Get system health status."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "environment": "development",
            "database": {
                "status": "connected",
                "users_count": len(db.users),
                "organizations_count": len(db.organizations),
                "audit_logs_count": len(db.audit_logs)
            },
            "services": {
                "email": "operational",
                "rate_limiter": "operational",
                "authentication": "operational"
            }
        }
    
    @staticmethod
    async def get_system_stats() -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "total_users": len(db.users),
            "active_users": len([u for u in db.users.values() if u["status"] == UserStatus.ACTIVE]),
            "pending_users": len([u for u in db.users.values() if u["status"] == UserStatus.PENDING_VERIFICATION]),
            "total_organizations": len(db.organizations),
            "total_audit_logs": len(db.audit_logs),
            "active_tokens": len(db.refresh_tokens),
            "pending_verifications": len(db.email_verification_tokens),
            "blocked_ips": len(SecurityService.blocked_ips)
        }

# Export all services
__all__ = [
    "UserService", "TokenService", "EmailService", "OrganizationService",
    "AuditService", "SecurityService", "SystemService", "db"
]
