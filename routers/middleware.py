# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Middleware layer with contract compliance

"""Middleware implementations for request processing."""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

from .services import AuditService, SecurityService, OrganizationService
from .rate_limiter import get_rate_limiter, RateLimitResult
from core.security import verify_access_token

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request context and metadata."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request context and timing."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request metadata
        request.state.request_id = request_id
        request.state.start_time = time.time()
        request.state.timestamp = datetime.utcnow()
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        request.state.client_ip = client_ip
        request.state.user_agent = user_agent
        
        # Add headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(int((time.time() - request.state.start_time) * 1000))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app, limiter_name: str = "api"):
        super().__init__(app)
        self.limiter_name = limiter_name
        self.limiter = get_rate_limiter(limiter_name)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request):
            return await call_next(request)
        
        # Generate rate limit key
        key = self._generate_rate_limit_key(request)
        
        # Check rate limit
        result = await self.limiter.check_rate_limit(key)
        
        if not result.allowed:
            # Rate limit exceeded
            response = Response(
                content=f'{{"detail": "Rate limit exceeded", "retry_after": {result.retry_after}}}',
                status_code=429,
                media_type="application/json"
            )
            
            # Add rate limit headers
            self._add_rate_limit_headers(response, result)
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        self._add_rate_limit_headers(response, result)
        
        return response
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Determine if rate limiting should be skipped."""
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _generate_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key for request."""
        # Use client IP as default key
        client_ip = getattr(request.state, "client_ip", "unknown")
        
        # Add user information if available
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user_{user_id}"
        
        return f"ip_{client_ip}"
    
    def _add_rate_limit_headers(self, response: Response, result: RateLimitResult) -> None:
        """Add rate limit headers to response."""
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_time)
        
        if result.retry_after:
            response.headers["Retry-After"] = str(result.retry_after)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks and IP blocking."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply security checks."""
        client_ip = getattr(request.state, "client_ip", "unknown")
        
        # Check if IP is blocked
        if await SecurityService.is_ip_blocked(client_ip):
            response = Response(
                content='{"detail": "Access denied"}',
                status_code=403,
                media_type="application/json"
            )
            return response
        
        # Add security headers
        response = await call_next(request)
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value

class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests for audit purposes."""
        start_time = time.time()
        
        # Get request information
        user_id = getattr(request.state, "user_id", None)
        client_ip = getattr(request.state, "client_ip", "unknown")
        user_agent = getattr(request.state, "user_agent", "")
        request_id = getattr(request.state, "request_id", "")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log significant events
        if self._should_audit_request(request, response):
            await AuditService.log_action(
                user_id=user_id,
                action=f"{request.method}_{request.url.path}",
                resource_type="endpoint",
                resource_id=request.url.path,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "request_id": request_id
                },
                ip_address=client_ip,
                user_agent=user_agent
            )
        
        return response
    
    def _should_audit_request(self, request: Request, response: Response) -> bool:
        """Determine if request should be audited."""
        # Always audit authentication endpoints
        if request.url.path.startswith("/auth"):
            return True
        
        # Audit admin endpoints
        if request.url.path.startswith("/admin"):
            return True
        
        # Audit failed requests
        if response.status_code >= 400:
            return True
        
        # Audit write operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True
        
        return False

class OrganizationContextMiddleware(BaseHTTPMiddleware):
    """Middleware for organization context."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add organization context to requests."""
        # Extract organization from headers or user context
        org_id = request.headers.get("X-Organization-ID")
        
        if not org_id:
            # Try to get from user context if available
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                # In a real implementation, you'd fetch user's organization
                # For now, we'll skip this lookup
                pass
        
        if org_id:
            # Validate organization exists
            organization = await OrganizationService.get_organization_by_id(org_id)
            if organization:
                request.state.organization_id = org_id
                request.state.organization = organization
        
        response = await call_next(request)
        
        # Add organization headers if available
        if hasattr(request.state, "organization_id"):
            response.headers["X-Organization-ID"] = request.state.organization_id
        
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication context."""
    
    def __init__(self, app, public_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.public_paths = public_paths or [
            "/health", "/docs", "/openapi.json", "/auth/login", "/auth/register", "/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add authentication context."""
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Verify token using our JWT verification
        payload = verify_access_token(token)
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user info to request state
        request.state.user_id = payload.get("user_id")
        request.state.user_email = payload.get("sub")
        request.state.is_admin = payload.get("is_admin", False)
        request.state.is_verified = payload.get("is_verified", False)
        
        response = await call_next(request)
        return response
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public."""
        return any(path.startswith(public_path) for public_path in self.public_paths)

class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware."""
    
    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS."""
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._create_preflight_response()
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        self._add_cors_headers(request, response)
        
        return response
    
    def _create_preflight_response(self) -> Response:
        """Create preflight response."""
        response = Response(status_code=200)
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = "3600"
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _add_cors_headers(self, request: Request, response: Response) -> None:
        """Add CORS headers to response."""
        origin = request.headers.get("origin")
        
        if origin and (self.allow_origins == ["*"] or origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif self.allow_origins == ["*"]:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        if self.allow_credentials and origin:
            response.headers["Access-Control-Allow-Credentials"] = "true"

# Middleware registry for easy configuration
MIDDLEWARE_REGISTRY = {
    "request_context": RequestContextMiddleware,
    "rate_limit": RateLimitMiddleware,
    "security": SecurityMiddleware,
    "audit": AuditMiddleware,
    "organization": OrganizationContextMiddleware,
    "authentication": AuthenticationMiddleware,
    "cors": CORSMiddleware
}

def get_middleware_stack(app, config: Dict[str, Any] = None) -> List[BaseHTTPMiddleware]:
    """Get configured middleware stack."""
    config = config or {}
    middleware_stack = []
    
    # Add middleware in order of execution
    middleware_order = [
        "cors",
        "request_context", 
        "security",
        "rate_limit",
        "authentication",
        "organization",
        "audit"
    ]
    
    for middleware_name in middleware_order:
        if config.get(middleware_name, {}).get("enabled", True):
            middleware_class = MIDDLEWARE_REGISTRY[middleware_name]
            middleware_config = config.get(middleware_name, {})
            
            # Remove 'enabled' from config before passing to middleware
            middleware_config.pop("enabled", None)
            
            middleware_stack.append(middleware_class(app, **middleware_config))
    
    return middleware_stack

# Export all middleware classes and utilities
__all__ = [
    "RequestContextMiddleware", "RateLimitMiddleware", "SecurityMiddleware",
    "AuditMiddleware", "OrganizationContextMiddleware", "AuthenticationMiddleware",
    "CORSMiddleware", "MIDDLEWARE_REGISTRY", "get_middleware_stack"
]
