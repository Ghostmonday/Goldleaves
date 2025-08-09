# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Complete router contract definitions

"""Router contract definitions and export structure for Goldleaves backend."""

from abc import ABC, abstractmethod
from fastapi import APIRouter
from typing import Dict, List, Protocol, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel
from builtins import property
from datetime import datetime
import asyncio

class RouterTags(str, Enum):
    """Standardized router tags for OpenAPI documentation."""
    AUTH = "authentication"
    USERS = "users"
    ADMIN = "admin"
    ORGANIZATIONS = "organizations"
    AUDIT = "audit"
    RATE_LIMIT = "rate-limiting"
    HEALTH = "health"
    DOCUMENTS = "documents"
    COLLABORATION = "collaboration"
    STORAGE = "storage"
    COURT_PACKAGING = "court-packaging"
    FORMS = "forms"
    BILLING = "billing"

class HTTPStatus(int, Enum):
    """Standard HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500

# Alias for compatibility with rate_limiter.py
StatusCodes = HTTPStatus

class ErrorResponseSchema(BaseModel):
    """Standard error response schema."""
    detail: str
    error_code: str
    timestamp: str
    request_id: str = ""

class SuccessResponseSchema(BaseModel):
    """Standard success response schema."""
    message: str
    data: Dict[str, Any] = {}
    timestamp: str

class RouterContract(ABC):
    """Abstract base contract for all router implementations."""
    
    @property
    @abstractmethod
    def router(self) -> APIRouter:
        """FastAPI router instance."""
        pass
    
    @property
    @abstractmethod
    def prefix(self) -> str:
        """URL prefix for this router."""
        pass
    
    @property
    @abstractmethod
    def tags(self) -> List[str]:
        """OpenAPI tags for this router."""
        pass
    
    @abstractmethod
    def configure_routes(self) -> None:
        """Configure all routes for this router."""
        pass

class ServiceProtocol(Protocol):
    """Protocol defining service layer interface."""
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource."""
        ...
    
    async def get_by_id(self, resource_id: str) -> Dict[str, Any]:
        """Get resource by ID."""
        ...
    
    async def update(self, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a resource."""
        ...
    
    async def delete(self, resource_id: str) -> bool:
        """Delete a resource."""
        ...

class MiddlewareContract(ABC):
    """Abstract base contract for middleware implementations."""
    
    @abstractmethod
    async def __call__(self, request, call_next):
        """Middleware call implementation."""
        pass

# === RATE LIMITING CONTRACTS ===

class RateLimitAlgorithm(str, Enum):
    """Available rate limiting algorithms."""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"

class StorageBackend(str, Enum):
    """Available storage backends for rate limiting."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    burst_allowance: int = 10
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    storage_backend: StorageBackend = StorageBackend.MEMORY
    key_prefix: str = "rate_limit"
    enabled: bool = True

class RateLimitResult(BaseModel):
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None

class StorageProtocol(Protocol):
    """Protocol for rate limiting storage backends."""
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from storage."""
        ...
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set value in storage with optional TTL."""
        ...
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter in storage."""
        ...
    
    async def delete(self, key: str) -> None:
        """Delete key from storage."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        ...

class RateLimiterProtocol(Protocol):
    """Protocol for rate limiter implementations."""
    
    async def check_rate_limit(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check if request is within rate limits."""
        ...
    
    async def reset_rate_limit(self, key: str) -> None:
        """Reset rate limit for a key."""
        ...
    
    async def get_rate_limit_status(self, key: str) -> Dict[str, Any]:
        """Get current rate limit status for a key."""
        ...

# Router registry for centralized management
ROUTER_REGISTRY: Dict[str, RouterContract] = {}

def register_router(name: str, router_contract: RouterContract) -> None:
    """Register a router contract."""
    ROUTER_REGISTRY[name] = router_contract

def get_all_routers() -> List[APIRouter]:
    """Get all registered FastAPI routers."""
    return [contract.router for contract in ROUTER_REGISTRY.values()]

def get_router_contract(name: str) -> RouterContract:
    """Get a specific router contract by name."""
    if name not in ROUTER_REGISTRY:
        raise ValueError(f"Router '{name}' not found in registry")
    return ROUTER_REGISTRY[name]

# Export all contracts and utilities
__all__ = [
    "RouterContract",
    "ServiceProtocol", 
    "MiddlewareContract",
    "RouterTags",
    "HTTPStatus",
    "StatusCodes",
    "ErrorResponseSchema",
    "SuccessResponseSchema",
    "RateLimitAlgorithm",
    "StorageBackend",
    "RateLimitConfig",
    "RateLimitResult",
    "StorageProtocol",
    "RateLimiterProtocol",
    "register_router",
    "get_all_routers",
    "get_router_contract",
    "ROUTER_REGISTRY"
]

# Register document storage router
def _register_storage_router():
    """Register the document storage router."""
    try:
        from .document_storage import router as storage_router
        storage_contract = RouterContract(
            name="document_storage",
            router=storage_router,
            prefix="/api/v1",
            tags=[RouterTags.STORAGE, RouterTags.COURT_PACKAGING],
            dependencies=[],
            metadata={
                "description": "Phase 7: Secure document storage, export, and court packaging",
                "version": "1.0.0",
                "features": [
                    "Multi-tenant file storage with encryption",
                    "Comprehensive export pipelines",
                    "Jurisdiction-aware court packaging",
                    "Audit trail preservation",
                    "E-filing preparation"
                ]
            }
        )
        register_router("document_storage", storage_contract)
    except ImportError:
        # Storage router not available
        pass

# Auto-register on import
_register_storage_router()

# Register forms router
def _register_forms_router():
    """Register the forms router."""
    try:
        from .forms import router as forms_router
        
        forms_contract = RouterContract(
            router=forms_router,
            prefix="",  # Already has /api/v1/forms prefix
            tags=[RouterTags.FORMS],
            auth_required=True,
            description="Form crowdsourcing and management"
        )
        
        register_router("forms", forms_contract)
    except ImportError:
        # Forms router not available
        pass

# Auto-register forms on import
_register_forms_router()
