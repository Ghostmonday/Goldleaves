"""
Usage tracking middleware for FastAPI.
Captures billable routes and logs usage events with idempotency.
"""

import uuid
from datetime import datetime
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status

from core.usage import start_event, is_billable_route


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking usage events on billable routes.
    
    Features:
    - Tracks configured billable routes from BILLABLE_ROUTES env var
    - Ensures X-Request-ID header (generates if missing)
    - Extracts tenant_id and user_id from auth context
    - Skips tracking on 4xx auth failures
    - Stores UTC timestamps
    - Provides idempotency via request_id deduplication
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track usage if on billable route."""
        
        # Ensure X-Request-ID header exists
        request_id = self._ensure_request_id(request)
        
        # Check if this is a billable route
        route_path = request.url.path
        if not is_billable_route(route_path):
            return await call_next(request)
        
        # Get user context from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        tenant_id = self._get_tenant_id(request)
        
        # Skip tracking if no user context (likely unauthenticated)
        if not user_id or not tenant_id:
            return await call_next(request)
        
        # Process the request
        response = await call_next(request)
        
        # Skip tracking on auth failures (4xx status codes)
        if 400 <= response.status_code < 500:
            return response
        
        # Track usage event asynchronously (don't block response)
        try:
            await self._track_usage_event(
                request=request,
                response=response,
                request_id=request_id,
                user_id=user_id,
                tenant_id=tenant_id,
                route=route_path
            )
        except Exception as e:
            # Log error but don't fail the main request
            print(f"Error tracking usage event: {e}")
        
        return response
    
    def _ensure_request_id(self, request: Request) -> str:
        """Ensure X-Request-ID header exists, generate if missing."""
        request_id = request.headers.get('X-Request-ID')
        
        if not request_id:
            request_id = str(uuid.uuid4())
            # Store in request state for potential use by other middleware
            request.state.request_id = request_id
        
        return request_id
    
    def _get_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant_id from request context."""
        # Try multiple sources for tenant_id
        
        # 1. From request state (set by organization middleware)
        tenant_id = getattr(request.state, 'organization_id', None)
        if tenant_id:
            return str(tenant_id)
        
        # 2. From X-Organization-ID header
        tenant_id = request.headers.get('X-Organization-ID')
        if tenant_id:
            return tenant_id
        
        # 3. From query parameter (for API keys)
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            return tenant_id
        
        # 4. Default to user_id if no organization context
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user_{user_id}"
        
        return None
    
    def _get_action(self, request: Request) -> str:
        """Determine action based on HTTP method."""
        method_to_action = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
            'HEAD': 'read',
            'OPTIONS': 'read'
        }
        return method_to_action.get(request.method.upper(), 'unknown')
    
    def _calculate_units(self, request: Request, response: Response) -> float:
        """Calculate usage units for the request."""
        # Basic implementation - can be extended for more sophisticated calculation
        
        # Default to 1 unit per request
        units = 1.0
        
        # For data upload/download, could factor in content length
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                # Could implement tiered pricing based on response size
                # For now, just use base unit
                pass
            except (ValueError, TypeError):
                pass
        
        return units
    
    async def _track_usage_event(
        self,
        request: Request,
        response: Response,
        request_id: str,
        user_id: str,
        tenant_id: str,
        route: str
    ) -> None:
        """Track the usage event asynchronously."""
        
        action = self._get_action(request)
        units = self._calculate_units(request, response)
        
        # Prepare metadata
        metadata = {
            'method': request.method,
            'status_code': response.status_code,
            'user_agent': request.headers.get('user-agent', ''),
            'client_ip': getattr(request.state, 'client_ip', 'unknown'),
            'response_size': response.headers.get('content-length'),
            'processing_time': getattr(request.state, 'processing_time', None)
        }
        
        # Convert metadata to JSON string
        import json
        metadata_str = json.dumps(metadata)
        
        # Create usage event (this handles idempotency internally)
        usage_event = start_event(
            route=route,
            action=action,
            request_id=request_id,
            user_id=str(user_id),
            tenant_id=tenant_id,
            units=units,
            metadata=metadata_str
        )
        
        if usage_event:
            # Add usage event ID to response headers for debugging
            response.headers['X-Usage-Event-ID'] = str(usage_event.id)


class BillableRoutesConfig:
    """Configuration helper for billable routes."""
    
    @staticmethod
    def get_default_billable_routes() -> list[str]:
        """Get default billable routes patterns."""
        return [
            '/api/v1/documents',
            '/api/v1/cases',
            '/api/v1/clients',
            '/api/v1/forms',
            '/api/v1/ai',
            '/api/v1/search'
        ]
    
    @staticmethod
    def is_route_billable(route: str, patterns: Optional[list[str]] = None) -> bool:
        """Check if route matches billable patterns."""
        if patterns is None:
            patterns = BillableRoutesConfig.get_default_billable_routes()
        
        return any(route.startswith(pattern) for pattern in patterns)


# Export middleware class
__all__ = ['UsageTrackingMiddleware', 'BillableRoutesConfig']