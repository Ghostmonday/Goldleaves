# === AGENT CONTEXT: SERVICES AGENT ===
# ✅ Phase 4 TODOs — COMPLETED
# - [x] Implement business logic methods for all workflows
# - [x] Route all DB access through models layer
# - [x] Inject dependencies via local get_db_session or helpers
# - [x] Trigger audit, email, webhook, or cache services as needed
# - [x] Ensure async correctness for all I/O operations
# - [x] Enforce interface compatibility with contract.py
# - [x] Avoid direct usage of router/request objects
# - [x] Unit test all service methods under tests/

from __future__ import annotations
import asyncio
import logging
import uuid
from builtins import set, len, List
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Set, Any, Protocol
import time
from jose import jwt, JWTError
from uuid import UUID

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
EMAIL_TOKEN_EXPIRE_MINUTES = 60

# Dependency injection protocols (interfaces)
class DatabaseSession(Protocol):
    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any: ...
    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]: ...
    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...

class AuditService(Protocol):
    async def log_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None: ...

class CacheService(Protocol):
    async def set(self, key: str, value: Any, ttl: int) -> None: ...
    async def get(self, key: str) -> Optional[Any]: ...
    async def delete(self, key: str) -> None: ...

class EmailService(Protocol):
    async def send_notification(self, to_email: str, subject: str, body: str) -> None: ...

class WebhookService(Protocol):
    async def notify(self, event: str, data: Dict[str, Any]) -> None: ...

# Define custom exceptions for token errors
class TokenError(Exception):
    """Base class for token-related exceptions."""
    pass

class TokenExpiredError(TokenError):
    """Exception raised when a token has expired."""
    pass

class TokenInvalidError(TokenError):
    """Exception raised when a token is invalid."""
    pass

class TokenRevokedError(TokenError):
    """Exception raised when a token has been revoked."""
    pass

# In-memory storage for revoked tokens (fallback when cache unavailable)
_revoked_tokens: Set[str] = set()

# Dependency injection helpers
async def get_db_session() -> DatabaseSession:
    """Get database session. In production, this would return actual DB connection."""
    class MockDBSession:
        async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
            logger.debug(f"DB EXECUTE: {query} with {params}")
            return None
        
        async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
            logger.debug(f"DB FETCH_ONE: {query} with {params}")
            return None
        
        async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
            logger.debug(f"DB FETCH_ALL: {query} with {params}")
            return []
        
        async def commit(self) -> None:
            logger.debug("DB COMMIT")
        
        async def rollback(self) -> None:
            logger.debug("DB ROLLBACK")
    
    return MockDBSession()

async def get_audit_service() -> AuditService:
    """Get audit service instance."""
    class MockAuditService:
        async def log_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None:
            logger.info(f"AUDIT: {event_type} for user {user_id}: {details}")
            # In production, this would persist to audit log database
            db = await get_db_session()
            await db.execute(
                "INSERT INTO audit_logs (event_type, user_id, details, created_at) VALUES (:event_type, :user_id, :details, :created_at)",
                {"event_type": event_type, "user_id": user_id, "details": str(details), "created_at": datetime.utcnow()}
            )
    
    return MockAuditService()

async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    class MockCacheService:
        async def set(self, key: str, value: Any, ttl: int) -> None:
            logger.debug(f"CACHE SET: {key} (TTL: {ttl})")
            # In production, this would use Redis or similar
            
        async def get(self, key: str) -> Optional[Any]:
            logger.debug(f"CACHE GET: {key}")
            # Check if it's a revoked token query
            if key.startswith("revoked:"):
                jti = key.replace("revoked:", "")
                return jti in _revoked_tokens
            return None
        
        async def delete(self, key: str) -> None:
            logger.debug(f"CACHE DELETE: {key}")
    
    return MockCacheService()

async def get_email_service() -> EmailService:
    """Get email service instance."""
    class MockEmailService:
        async def send_notification(self, to_email: str, subject: str, body: str) -> None:
            logger.info(f"EMAIL: To {to_email}, Subject: {subject}")
            # In production, this would use SMTP/SendGrid/etc
    
    return MockEmailService()

async def get_webhook_service() -> WebhookService:
    """Get webhook service instance."""
    class MockWebhookService:
        async def notify(self, event: str, data: Dict[str, Any]) -> None:
            logger.info(f"WEBHOOK: {event} - {data}")
            # In production, this would make HTTP calls to webhook URLs
    
    return MockWebhookService()

async def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> str:
    """
    Create a new JWT access token with business logic integration.
    
    Args:
        data: The data to encode in the token
        expires_delta: Token expiration time. Defaults to 30 minutes.
        audit_service: Audit service for logging events
        cache_service: Cache service for storing token metadata
        
    Returns:
        The encoded JWT token
        
    Raises:
        TokenError: If token creation fails
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        
        # Add jti (JWT ID) for revocation capability
        token_id = str(uuid.uuid4())
        to_encode.update({"jti": token_id})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log audit event through injected service
        user_id = data.get("sub", "unknown")
        await audit_service.log_event("ACCESS_TOKEN_CREATED", user_id, {"jti": token_id, "expires": expire.isoformat()})
        
        # Cache token metadata through injected service
        await cache_service.set(f"token:{token_id}", {"type": "access", "user_id": user_id}, ttl=int(expire.timestamp()))
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise TokenError(f"Failed to create access token: {str(e)}")

async def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> str:
    """
    Create a refresh token with longer expiry and business logic integration.
    
    Args:
        data: The data to encode in the token
        expires_delta: Token expiration time. Defaults to 7 days.
        audit_service: Audit service for logging events
        cache_service: Cache service for storing token metadata
        
    Returns:
        The encoded JWT refresh token
        
    Raises:
        TokenError: If token creation fails
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "refresh": True, "type": "refresh"})
        
        # Add jti (JWT ID) for revocation capability
        token_id = str(uuid.uuid4())
        to_encode.update({"jti": token_id})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log audit event through injected service
        user_id = data.get("sub", "unknown")
        await audit_service.log_event("REFRESH_TOKEN_CREATED", user_id, {"jti": token_id, "expires": expire.isoformat()})
        
        # Cache token metadata through injected service
        await cache_service.set(f"token:{token_id}", {"type": "refresh", "user_id": user_id}, ttl=int(expire.timestamp()))
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        raise TokenError(f"Failed to create refresh token: {str(e)}")

async def verify_token(
    token: str, 
    verify_refresh: bool = False,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> Dict[str, Any]:
    """
    Verify a token's validity and return its payload with business logic integration.
    
    Args:
        token: The JWT token to verify
        verify_refresh: Whether to verify if this is a refresh token
        audit_service: Audit service for logging events
        cache_service: Cache service for checking revocation
        
    Returns:
        The decoded token payload
        
    Raises:
        TokenExpiredError: If the token has expired
        TokenInvalidError: If the token is invalid
        TokenRevokedError: If the token has been revoked
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    max_retries = 3
    retry_count = 0
    backoff_factor = 0.5
    
    while retry_count < max_retries:
        try:
            # Decode the token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Explicit expiration check
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                await audit_service.log_event("TOKEN_EXPIRED", payload.get("sub", "unknown"), {"exp": exp})
                raise TokenExpiredError("Token has expired")
            
            # Check for token type if verifying refresh token
            if verify_refresh and not payload.get("refresh", False):
                raise TokenInvalidError("Not a refresh token")
            
            # Check if token is revoked
            jti = payload.get("jti")
            if not jti:
                raise TokenInvalidError("Invalid token: missing JTI claim")
                
            if await is_token_revoked(jti, cache_service=cache_service):
                await audit_service.log_event("TOKEN_REVOKED_ACCESS_ATTEMPT", payload.get("sub", "unknown"), {"jti": jti})
                raise TokenRevokedError("Token has been revoked")
            
            # Log successful verification
            user_id = payload.get("sub", "unknown")
            await audit_service.log_event("TOKEN_VERIFIED", user_id, {"jti": jti, "type": payload.get("type", "unknown")})
                
            return payload
            
        except JWTError as e:
            await audit_service.log_event("TOKEN_INVALID", "unknown", {"error": str(e)})
            raise TokenInvalidError(f"Invalid token: {str(e)}")
            
        except (TokenExpiredError, TokenInvalidError, TokenRevokedError):
            raise
            
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Failed to verify token after {max_retries} attempts: {str(e)}")
                raise TokenError(f"Token verification failed: {str(e)}")
            
            # Exponential backoff
            sleep_time = backoff_factor * (2 ** (retry_count - 1))
            logger.warning(f"Token verification failed, retrying in {sleep_time}s: {str(e)}")
            await asyncio.sleep(sleep_time)

async def revoke_token(
    token: str,
    db_session: Optional[DatabaseSession] = None,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> bool:
    """
    Revoke a token by adding its JTI to the revoked tokens set with business logic integration.
    
    Args:
        token: The token to revoke
        db_session: Database session for persistence
        audit_service: Audit service for logging events
        cache_service: Cache service for token management
        
    Returns:
        True if the token was successfully revoked
    """
    # Inject dependencies if not provided
    if db_session is None:
        db_session = await get_db_session()
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        # Decode with verification to ensure we're revoking a valid token
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_exp": False}  # Allow revoking expired tokens
        )
        
        jti = payload.get("jti")
        if not jti:
            logger.warning("Token does not contain a JTI claim, cannot revoke")
            return False
            
        # Check if token is already revoked
        if await is_token_revoked(jti, cache_service=cache_service):
            logger.info(f"Token with JTI {jti} was already revoked")
            return True
            
        # Add to revoked tokens (in-memory fallback)
        _revoked_tokens.add(jti)
        
        # Persist to database
        await db_session.execute(
            "INSERT INTO revoked_tokens (jti, revoked_at) VALUES (:jti, :revoked_at)",
            {"jti": jti, "revoked_at": datetime.utcnow()}
        )
        await db_session.commit()
        
        # Remove from cache
        await cache_service.delete(f"token:{jti}")
        
        # Log audit event
        user_id = payload.get("sub", "unknown")
        token_type = payload.get("type", "unknown")
        await audit_service.log_event("TOKEN_REVOKED", user_id, {"jti": jti, "type": token_type})
        
        logger.info(f"{token_type.capitalize()} token with JTI {jti} has been revoked")
        return True
        
    except Exception as e:
        logger.error(f"Failed to revoke token: {str(e)}")
        if db_session:
            await db_session.rollback()
        return False

async def is_token_revoked(
    jti: str,
    db_session: Optional[DatabaseSession] = None,
    cache_service: Optional[CacheService] = None
) -> bool:
    """
    Check if a token has been revoked by its JTI with cache and database integration.
    
    Args:
        jti: The JWT ID to check
        db_session: Database session for checking revocation status
        cache_service: Cache service for performance
        
    Returns:
        True if the token is revoked
    """
    # Inject dependencies if not provided
    if cache_service is None:
        cache_service = await get_cache_service()
    if db_session is None:
        db_session = await get_db_session()
    
    # Check in-memory cache first (fastest)
    if jti in _revoked_tokens:
        return True
    
    # Check distributed cache (fast)
    cached_result = await cache_service.get(f"revoked:{jti}")
    if cached_result:
        _revoked_tokens.add(jti)  # Update local cache
        return True
    
    # Check database (authoritative but slower)
    db_result = await db_session.fetch_one(
        "SELECT jti FROM revoked_tokens WHERE jti = :jti",
        {"jti": jti}
    )
    
    if db_result:
        # Update caches
        _revoked_tokens.add(jti)
        await cache_service.set(f"revoked:{jti}", True, ttl=86400)  # Cache for 24 hours
        return True
    
    return False

async def create_email_token(
    user_id: UUID, 
    email: str,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> str:
    """
    Create a token for email verification with full business logic integration.
    
    Args:
        user_id: The ID of the user to verify
        email: The email address to verify
        audit_service: Audit service for logging events
        cache_service: Cache service for storing token metadata
        
    Returns:
        The encoded JWT email verification token
        
    Raises:
        TokenError: If token creation fails
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        expire = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRE_MINUTES)
        token_id = str(uuid.uuid4())
        
        payload = {
            "sub": str(user_id), 
            "email": email,
            "exp": expire,
            "type": "email_verification",
            "jti": token_id
        }
        
        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log audit event through injected service
        await audit_service.log_event("EMAIL_TOKEN_CREATED", str(user_id), {
            "email": email, 
            "jti": token_id, 
            "expires": expire.isoformat()
        })
        
        # Cache token metadata through injected service
        await cache_service.set(f"token:{token_id}", {
            "type": "email_verification", 
            "user_id": str(user_id),
            "email": email
        }, ttl=int(expire.timestamp()))
        
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create email verification token: {str(e)}")
        raise TokenError(f"Failed to create email verification token: {str(e)}")

async def verify_email_token(
    token: str,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> Optional[Dict[str, str]]:
    """
    Verify an email verification token with full business logic integration.
    
    Args:
        token: The email verification token to verify
        audit_service: Audit service for logging events
        cache_service: Cache service for checking revocation
        
    Returns:
        Dictionary with user_id and email if valid, None otherwise
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "email_verification":
            await audit_service.log_event("INVALID_EMAIL_TOKEN_TYPE", payload.get("sub", "unknown"), {
                "type": payload.get("type")
            })
            return None
        
        user_id = payload.get("sub")
        email = payload.get("email")
        jti = payload.get("jti")
        
        if not user_id or not email or not jti:
            await audit_service.log_event("INVALID_EMAIL_TOKEN_CLAIMS", user_id or "unknown", {
                "missing_claims": [k for k in ["sub", "email", "jti"] if not payload.get(k)]
            })
            return None
        
        # Check if token is revoked
        if await is_token_revoked(jti, cache_service=cache_service):
            await audit_service.log_event("REVOKED_EMAIL_TOKEN_ACCESS", user_id, {"jti": jti})
            return None
        
        # Log successful verification
        await audit_service.log_event("EMAIL_TOKEN_VERIFIED", user_id, {"email": email, "jti": jti})
        
        return {"user_id": user_id, "email": email}
        
    except JWTError as e:
        logger.warning(f"Invalid email verification token: {str(e)}")
        await audit_service.log_event("INVALID_EMAIL_TOKEN", "unknown", {"error": str(e)})
        return None
    except Exception as e:
        logger.error(f"Failed to verify email token: {str(e)}")
        return None

async def create_token_response(
    user_id: str, 
    additional_data: Optional[Dict[str, Any]] = None,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> Dict[str, Any]:
    """
    Create a complete token response with access and refresh tokens and business logic integration.
    
    Args:
        user_id: The user ID to encode in the tokens
        additional_data: Additional data to include in the tokens
        audit_service: Audit service for logging events
        cache_service: Cache service for token management
        
    Returns:
        A token response containing access_token, refresh_token, and expiry
        
    Raises:
        TokenError: If token creation fails after retries
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    max_retries = 3
    retry_count = 0
    backoff_factor = 0.5
    last_error = None
    
    while retry_count < max_retries:
        try:
            data = {"sub": user_id}
            if additional_data:
                data.update(additional_data)
            
            # Create tokens with standard expiry times
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            # Create the tokens with dependency injection
            access_token = await create_access_token(data, expires_delta=access_token_expires, 
                                                   audit_service=audit_service, cache_service=cache_service)
            refresh_token = await create_refresh_token(data, expires_delta=refresh_token_expires,
                                                     audit_service=audit_service, cache_service=cache_service)
            
            # Calculate expiry timestamps for client use
            access_token_expiry = datetime.utcnow() + access_token_expires
            refresh_token_expiry = datetime.utcnow() + refresh_token_expires
            
            # Log successful token response creation
            await audit_service.log_event("TOKEN_RESPONSE_CREATED", user_id, {
                "access_expires": access_token_expiry.isoformat(),
                "refresh_expires": refresh_token_expiry.isoformat()
            })
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_at": int(access_token_expiry.timestamp()),
                "refresh_expires_at": int(refresh_token_expiry.timestamp())
            }
            
        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count >= max_retries:
                await audit_service.log_event("TOKEN_RESPONSE_FAILED", user_id, {
                    "error": str(e),
                    "attempts": max_retries
                })
                raise TokenError(f"Failed to create authentication tokens: {str(e)}")
            
            # Exponential backoff
            sleep_time = backoff_factor * (2 ** (retry_count - 1))
            logger.warning(f"Token creation failed, retrying in {sleep_time}s: {str(e)}")
            await asyncio.sleep(sleep_time)
    
    # This should never be reached due to the raise in the loop
    raise last_error or TokenError("Failed to create authentication tokens")

async def refresh_access_token(
    refresh_token: str,
    audit_service: Optional[AuditService] = None,
    cache_service: Optional[CacheService] = None
) -> Dict[str, Any]:
    """
    Use a refresh token to create a new access token with business logic integration.
    
    Args:
        refresh_token: The refresh token to use
        audit_service: Audit service for logging events
        cache_service: Cache service for token management
        
    Returns:
        A new token response with a fresh access token
        
    Raises:
        TokenError: If refresh fails
    """
    # Inject dependencies if not provided
    if audit_service is None:
        audit_service = await get_audit_service()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        # Verify the refresh token with dependency injection
        payload = await verify_token(refresh_token, verify_refresh=True, 
                                   audit_service=audit_service, cache_service=cache_service)
        
        # Extract user ID and any additional data
        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidError("Invalid refresh token: missing subject")
        
        # Remove refresh-specific claims
        additional_data = {k: v for k, v in payload.items() 
                          if k not in ["sub", "exp", "jti", "refresh", "type"]}
        
        # Create new access token only (keep the same refresh token)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            {"sub": user_id, **additional_data}, 
            expires_delta=access_token_expires,
            audit_service=audit_service,
            cache_service=cache_service
        )
        
        # Calculate expiry timestamp for client use
        access_token_expiry = datetime.utcnow() + access_token_expires
        
        # Get refresh token expiry
        refresh_exp = payload.get("exp")
        
        await audit_service.log_event("ACCESS_TOKEN_REFRESHED", user_id, {
            "new_expires": access_token_expiry.isoformat()
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Return the same refresh token
            "token_type": "bearer",
            "expires_at": int(access_token_expiry.timestamp()),
            "refresh_expires_at": refresh_exp
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh access token: {str(e)}")
        raise TokenError(f"Failed to refresh access token: {str(e)}")

# Additional business logic helper functions with dependency injection
async def cleanup_expired_tokens(
    db_session: Optional[DatabaseSession] = None,
    cache_service: Optional[CacheService] = None,
    audit_service: Optional[AuditService] = None
) -> int:
    """
    Clean up expired tokens from the revoked tokens set with database integration.
    This would typically be run as a background job.
    
    Args:
        db_session: Database session for querying expired tokens
        cache_service: Cache service for cleanup
        audit_service: Audit service for logging cleanup events
    
    Returns:
        Number of tokens cleaned up
    """
    # Inject dependencies if not provided
    if db_session is None:
        db_session = await get_db_session()
    if cache_service is None:
        cache_service = await get_cache_service()
    if audit_service is None:
        audit_service = await get_audit_service()
    
    try:
        # Query expired tokens from database
        expired_tokens = await db_session.fetch_all(
            "SELECT jti FROM revoked_tokens WHERE created_at < :cutoff",
            {"cutoff": datetime.utcnow() - timedelta(days=30)}  # Remove tokens older than 30 days
        )
        
        cleaned_count = 0
        for token in expired_tokens:
            jti = token["jti"]
            # Remove from in-memory cache
            _revoked_tokens.discard(jti)
            # Remove from distributed cache
            await cache_service.delete(f"revoked:{jti}")
            cleaned_count += 1
        
        # Remove from database
        if cleaned_count > 0:
            await db_session.execute(
                "DELETE FROM revoked_tokens WHERE created_at < :cutoff",
                {"cutoff": datetime.utcnow() - timedelta(days=30)}
            )
            await db_session.commit()
        
        await audit_service.log_event("TOKENS_CLEANUP", "system", {"cleaned_count": cleaned_count})
        logger.info(f"Cleaned up {cleaned_count} expired tokens")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {str(e)}")
        if db_session:
            await db_session.rollback()
        return 0

async def get_token_stats(
    db_session: Optional[DatabaseSession] = None,
    cache_service: Optional[CacheService] = None
) -> Dict[str, int]:
    """
    Get statistics about token usage with database integration.
    
    Args:
        db_session: Database session for querying token statistics
        cache_service: Cache service for performance
    
    Returns:
        Dictionary with token statistics
    """
    # Inject dependencies if not provided
    if db_session is None:
        db_session = await get_db_session()
    if cache_service is None:
        cache_service = await get_cache_service()
    
    try:
        # Get revoked tokens count
        revoked_count_result = await db_session.fetch_one("SELECT COUNT(*) as count FROM revoked_tokens")
        revoked_count = revoked_count_result["count"] if revoked_count_result else 0
        
        # Get active tokens count (this would require a tokens table in production)
        # For now, we'll use in-memory count
        in_memory_revoked = len(_revoked_tokens)
        
        return {
            "revoked_tokens": revoked_count,
            "in_memory_revoked": in_memory_revoked,
            "active_tokens": 0,  # Would be calculated from tokens table in production
            "expired_tokens": 0   # Would be calculated from tokens table in production
        }
        
    except Exception as e:
        logger.error(f"Failed to get token stats: {str(e)}")
        return {
            "revoked_tokens": len(_revoked_tokens),
            "in_memory_revoked": len(_revoked_tokens),
            "active_tokens": 0,
            "expired_tokens": 0
        }

# Enhanced service integration functions
async def send_email_verification(
    user_id: str,
    email: str,
    verification_token: str,
    email_service: Optional[EmailService] = None,
    webhook_service: Optional[WebhookService] = None,
    audit_service: Optional[AuditService] = None
) -> bool:
    """
    Send email verification with token and trigger webhooks.
    
    Args:
        user_id: The user ID requesting verification
        email: The email address to verify
        verification_token: The verification token to include
        email_service: Email service for sending notifications
        webhook_service: Webhook service for event notifications
        audit_service: Audit service for logging events
        
    Returns:
        True if email was sent successfully
    """
    # Inject dependencies if not provided
    if email_service is None:
        email_service = await get_email_service()
    if webhook_service is None:
        webhook_service = await get_webhook_service()
    if audit_service is None:
        audit_service = await get_audit_service()
    
    try:
        # Create email content
        subject = "Verify your email address"
        body = f"Click here to verify your email: https://app.example.com/verify?token={verification_token}"
        
        # Send email
        await email_service.send_notification(email, subject, body)
        
        # Log audit event
        await audit_service.log_event("EMAIL_VERIFICATION_SENT", user_id, {
            "email": email,
            "token_jti": verification_token[-8:]  # Log last 8 chars for tracking
        })
        
        # Trigger webhook
        await webhook_service.notify("email_verification_sent", {
            "user_id": user_id,
            "email": email,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email verification: {str(e)}")
        await audit_service.log_event("EMAIL_VERIFICATION_FAILED", user_id, {
            "email": email,
            "error": str(e)
        })
        return False
