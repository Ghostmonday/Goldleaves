"""
Usage tracking middleware that reads tags from request.state and forwards to core.usage.
"""

from __future__ import annotations
import time
import logging
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.usage import record_usage

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking usage events with tags from request.state.
    
    Reads tag values from request.state when present, otherwise uses defaults:
    - feature: str = "unknown"
    - jurisdiction: str = "unknown" 
    - plan: str = "unknown"
    - ai: bool = False
    """
    
    def __init__(self, app, enabled: bool = True):
        """
        Initialize usage tracking middleware.
        
        Args:
            app: ASGI application
            enabled: Whether usage tracking is enabled (default: True)
        """
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track usage."""
        if not self.enabled:
            return await call_next(request)
        
        # Extract tags from request.state with defaults
        feature = getattr(request.state, "feature", "unknown")
        jurisdiction = getattr(request.state, "jurisdiction", "unknown")
        plan = getattr(request.state, "plan", "unknown")
        ai = getattr(request.state, "ai", False)
        
        # Extract additional context
        user_id = getattr(request.state, "user_id", None)
        request_id = getattr(request.state, "request_id", None)
        
        # Record the start time
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Determine if we should track this request
            if self._should_track_request(request, response):
                # Record usage event
                await self._record_usage_event(
                    request=request,
                    response=response,
                    feature=feature,
                    jurisdiction=jurisdiction,
                    plan=plan,
                    ai=ai,
                    user_id=user_id,
                    request_id=request_id,
                    processing_time=processing_time
                )
            
            return response
            
        except Exception as e:
            # Calculate processing time even for errors
            processing_time = time.time() - start_time
            
            # Track error events
            if self._should_track_request(request, None):
                await self._record_usage_event(
                    request=request,
                    response=None,
                    feature=feature,
                    jurisdiction=jurisdiction,
                    plan=plan,
                    ai=ai,
                    user_id=user_id,
                    request_id=request_id,
                    processing_time=processing_time,
                    error=str(e)
                )
            
            # Re-raise the exception
            raise
    
    def _should_track_request(self, request: Request, response: Optional[Response]) -> bool:
        """
        Determine if a request should be tracked.
        
        Args:
            request: The HTTP request
            response: The HTTP response (None for errors)
            
        Returns:
            True if the request should be tracked
        """
        # Skip health checks and docs
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return False
        
        # Skip static assets
        if request.url.path.startswith("/static"):
            return False
        
        # Track API endpoints (assuming they start with /api or have certain patterns)
        api_patterns = ["/api", "/auth", "/admin"]
        if any(request.url.path.startswith(pattern) for pattern in api_patterns):
            return True
        
        # Track requests with explicit usage tags set
        if (hasattr(request.state, "feature") and request.state.feature != "unknown" or
            hasattr(request.state, "jurisdiction") and request.state.jurisdiction != "unknown" or
            hasattr(request.state, "plan") and request.state.plan != "unknown" or
            hasattr(request.state, "ai") and request.state.ai is True):
            return True
        
        # Track requests with authenticated users
        if hasattr(request.state, "user_id") and request.state.user_id:
            return True
        
        return False
    
    async def _record_usage_event(
        self,
        request: Request,
        response: Optional[Response],
        feature: str,
        jurisdiction: str,
        plan: str,
        ai: bool,
        user_id: Optional[str],
        request_id: Optional[str],
        processing_time: float,
        error: Optional[str] = None
    ) -> None:
        """
        Record a usage event.
        
        Args:
            request: The HTTP request
            response: The HTTP response (None for errors)
            feature: Feature tag
            jurisdiction: Jurisdiction tag
            plan: Plan tag
            ai: AI flag
            user_id: User ID if available
            request_id: Request ID if available
            processing_time: Request processing time in seconds
            error: Error message if any
        """
        try:
            # Determine event type
            event_type = self._get_event_type(request, response, error)
            
            # Build metadata
            metadata = {
                "method": request.method,
                "path": request.url.path,
                "processing_time": processing_time,
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": getattr(request.state, "client_ip", "unknown")
            }
            
            if response:
                metadata["status_code"] = response.status_code
            
            if error:
                metadata["error"] = error
                metadata["status"] = "error"
            else:
                metadata["status"] = "success"
            
            # Record the usage event
            event_id = await record_usage(
                feature=feature,
                jurisdiction=jurisdiction,
                plan=plan,
                ai=ai,
                event_type=event_type,
                user_id=user_id,
                request_id=request_id,
                metadata=metadata
            )
            
            if event_id:
                logger.debug(
                    f"Recorded usage event {event_id}: {feature}/{jurisdiction}/{plan}/ai={ai}"
                )
            else:
                logger.warning("Failed to record usage event")
                
        except Exception as e:
            logger.error(f"Error recording usage event: {e}", exc_info=True)
    
    def _get_event_type(
        self,
        request: Request,
        response: Optional[Response],
        error: Optional[str]
    ) -> str:
        """
        Determine the event type based on request and response.
        
        Args:
            request: The HTTP request
            response: The HTTP response (None for errors)
            error: Error message if any
            
        Returns:
            Event type string
        """
        if error:
            return "api_error"
        
        if response and response.status_code >= 400:
            return "api_error"
        
        # Determine based on method and path
        method = request.method.lower()
        path = request.url.path
        
        if path.startswith("/auth"):
            return f"auth_{method}"
        elif path.startswith("/api"):
            return f"api_{method}"
        elif path.startswith("/admin"):
            return f"admin_{method}"
        else:
            return f"request_{method}"


# Helper function to add usage tags to request state
def set_usage_tags(
    request: Request,
    feature: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    plan: Optional[str] = None,
    ai: Optional[bool] = None
) -> None:
    """
    Set usage tags on request state.
    
    Args:
        request: The HTTP request
        feature: Feature tag
        jurisdiction: Jurisdiction tag
        plan: Plan tag
        ai: AI flag
    """
    if feature is not None:
        request.state.feature = feature
    if jurisdiction is not None:
        request.state.jurisdiction = jurisdiction
    if plan is not None:
        request.state.plan = plan
    if ai is not None:
        request.state.ai = ai


# Helper function to get usage tags from request state
def get_usage_tags(request: Request) -> dict:
    """
    Get usage tags from request state.
    
    Args:
        request: The HTTP request
        
    Returns:
        Dictionary with usage tags
    """
    return {
        "feature": getattr(request.state, "feature", "unknown"),
        "jurisdiction": getattr(request.state, "jurisdiction", "unknown"),
        "plan": getattr(request.state, "plan", "unknown"),
        "ai": getattr(request.state, "ai", False)
    }