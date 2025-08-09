# === AGENT CONTEXT: ROUTERS AGENT ===
# 🚧 TODOs for Phase 4 — Complete endpoint contracts
# - [ ] Define FastAPI routes with dependency injection
# - [ ] Enforce usage of Pydantic schemas from schemas/
# - [ ] Route all business logic to services/ layer
# - [ ] Attach rate limit, audit, and org context middleware
# - [ ] Export routers via `RouterContract` in contract.py
# - [ ] Add tag, prefix, and response model to all endpoints
# - [ ] Ensure endpoint coverage with integration tests
# - [ ] Maintain full folder isolation (no model/service import)
# - [ ] Use consistent 2xx/4xx status codes and error schemas

"""
Rate limiting configuration and strategies.
"""
from dataclasses import dataclass
from typing import Optional, Callable
from fastapi import Request

from .rate_limiter import RateLimitAlgorithm, AdvancedRateLimiter


@dataclass
class EndpointRateLimit:
    """Configuration for rate limiting a specific endpoint."""
    limit: str  # e.g., "10/minute"
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_allowance: int = 0
    error_message: Optional[str] = None
    key_func: Optional[Callable[[Request], str]] = None
    skip_successful_requests: bool = False
    skip_failed_requests: bool = False


class RateLimitConfig:
    """
    Centralized rate limiting configuration for different endpoints and user types.
    """
    
    # Default rate limits for different endpoint types
    AUTH_ENDPOINTS = {
        "login": EndpointRateLimit(
            limit="10/minute",
            algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
            error_message="Too many login attempts. Please try again later.",
            skip_failed_requests=True  # Don't penalize failed attempts
        ),
        "register": EndpointRateLimit(
            limit="3/minute",
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_allowance=2,
            error_message="Registration rate limit exceeded. Please try again later."
        ),
        "password_reset": EndpointRateLimit(
            limit="5/hour",
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            error_message="Too many password reset requests. Please try again later."
        ),
        "email_verification": EndpointRateLimit(
            limit="10/hour",
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            error_message="Too many email verification attempts. Please try again later."
        )
    }
    
    # Rate limits for API endpoints
    API_ENDPOINTS = {
        "public": EndpointRateLimit(
            limit="100/hour",
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        ),
        "authenticated": EndpointRateLimit(
            limit="1000/hour",
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_allowance=50
        ),
        "admin": EndpointRateLimit(
            limit="5000/hour",
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_allowance=200
        )
    }
    
    # Special rate limits for sensitive operations
    SENSITIVE_ENDPOINTS = {
        "admin_user_list": EndpointRateLimit(
            limit="20/minute",
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            error_message="Admin operation rate limit exceeded."
        ),
        "data_export": EndpointRateLimit(
            limit="5/hour",
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            error_message="Data export limit exceeded. Please try again later."
        ),
        "bulk_operations": EndpointRateLimit(
            limit="10/hour",
            algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
            error_message="Bulk operation limit exceeded."
        )
    }
    
    @classmethod
    def get_user_key_func(cls, user_id_field: str = "user_id") -> Callable[[Request], str]:
        """
        Create a key function that uses user ID instead of IP for authenticated endpoints.
        
        Args:
            user_id_field: The field name in the request state that contains the user ID.
            
        Returns:
            A function that extracts user ID from request for rate limiting.
        """
        def user_key_func(request: Request) -> str:
            # In a real application, you would extract user ID from the JWT token
            # or from the request state after authentication
            user_id = getattr(request.state, user_id_field, None)
            if user_id:
                return f"user:{user_id}"
            else:
                # Fallback to IP-based limiting for unauthenticated requests
                return request.client.host or "unknown"
        
        return user_key_func
    
    @classmethod
    def get_tiered_key_func(cls) -> Callable[[Request], str]:
        """
        Create a key function that implements tiered rate limiting based on user type.
        
        Returns:
            A function that creates different rate limit pools for different user tiers.
        """
        def tiered_key_func(request: Request) -> str:
            # Extract user type from request state (set during authentication)
            user_type = getattr(request.state, "user_type", "anonymous")
            user_id = getattr(request.state, "user_id", None)
            
            if user_type == "admin":
                return f"admin:{user_id}" if user_id else "admin:unknown"
            elif user_type == "premium":
                return f"premium:{user_id}" if user_id else "premium:unknown"
            elif user_type == "authenticated":
                return f"auth:{user_id}" if user_id else "auth:unknown"
            else:
                # Anonymous users are limited by IP
                return f"anon:{request.client.host or 'unknown'}"
        
        return tiered_key_func


class RateLimitManager:
    """
    Manager class for applying rate limits with different strategies.
    """
    
    def __init__(self, limiter: Optional[AdvancedRateLimiter] = None):
        self.limiter = limiter or AdvancedRateLimiter()
        self.config = RateLimitConfig()
    
    def apply_auth_limit(self, endpoint_type: str):
        """Apply rate limit for authentication endpoints."""
        if endpoint_type not in self.config.AUTH_ENDPOINTS:
            raise ValueError(f"Unknown auth endpoint type: {endpoint_type}")
        
        config = self.config.AUTH_ENDPOINTS[endpoint_type]
        return self.limiter.limit(
            limit_str=config.limit,
            algorithm=config.algorithm,
            burst_allowance=config.burst_allowance,
            error_message=config.error_message,
            key_func=config.key_func,
            skip_successful_requests=config.skip_successful_requests,
            skip_failed_requests=config.skip_failed_requests
        )
    
    def apply_api_limit(self, user_tier: str):
        """Apply rate limit for API endpoints based on user tier."""
        if user_tier not in self.config.API_ENDPOINTS:
            raise ValueError(f"Unknown user tier: {user_tier}")
        
        config = self.config.API_ENDPOINTS[user_tier]
        return self.limiter.limit(
            limit_str=config.limit,
            algorithm=config.algorithm,
            burst_allowance=config.burst_allowance,
            error_message=config.error_message,
            key_func=self.config.get_tiered_key_func()
        )
    
    def apply_sensitive_limit(self, operation_type: str):
        """Apply rate limit for sensitive operations."""
        if operation_type not in self.config.SENSITIVE_ENDPOINTS:
            raise ValueError(f"Unknown sensitive operation: {operation_type}")
        
        config = self.config.SENSITIVE_ENDPOINTS[operation_type]
        return self.limiter.limit(
            limit_str=config.limit,
            algorithm=config.algorithm,
            burst_allowance=config.burst_allowance,
            error_message=config.error_message,
            key_func=self.config.get_user_key_func()
        )
    
    def get_limit_status(self, request: Request, endpoint_type: str, category: str = "auth"):
        """Get rate limit status for a specific endpoint."""
        if category == "auth":
            config = self.config.AUTH_ENDPOINTS.get(endpoint_type)
        elif category == "api":
            config = self.config.API_ENDPOINTS.get(endpoint_type)
        elif category == "sensitive":
            config = self.config.SENSITIVE_ENDPOINTS.get(endpoint_type)
        else:
            raise ValueError(f"Unknown category: {category}")
        
        if not config:
            raise ValueError(f"Unknown endpoint type: {endpoint_type}")
        
        return self.limiter.get_rate_limit_status(
            request=request,
            limit_str=config.limit,
            algorithm=config.algorithm,
            key_func=config.key_func
        )


# Global rate limit manager instance
rate_limit_manager = RateLimitManager()
