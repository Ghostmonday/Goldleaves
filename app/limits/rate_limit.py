"""Redis-backed token-bucket rate limiter with per-tenant support."""

import time
import logging
import os
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from fastapi import Request, HTTPException, Depends

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    capacity: int
    current: int
    retry_after: Optional[int] = None


class TokenBucketLimiter:
    """Redis-backed token bucket rate limiter."""
    
    def __init__(self, redis_client=None):
        """Initialize the rate limiter.
        
        Args:
            redis_client: Redis client instance. If None, will attempt to create one.
        """
        self.redis = redis_client
        self._redis_available = False
        
        if self.redis is None:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("REDIS_URL not configured, rate limiter will no-op")
            return
        
        try:
            import redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            self._redis_available = True
            logger.info("Redis connection established for rate limiting")
        except ImportError:
            logger.warning("redis package not available, rate limiter will no-op")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, rate limiter will no-op")
    
    async def check_limit(
        self, 
        tenant_id: str, 
        capacity: int, 
        refill_rate_per_min: int
    ) -> RateLimitResult:
        """Check if request should be allowed based on token bucket algorithm.
        
        Args:
            tenant_id: Unique identifier for the tenant
            capacity: Maximum number of tokens in bucket
            refill_rate_per_min: Number of tokens added per minute
            
        Returns:
            RateLimitResult indicating if request is allowed
        """
        if not self._redis_available or not self.redis:
            # No-op when Redis is unavailable
            return RateLimitResult(allowed=True, capacity=capacity, current=capacity)
        
        key = f"rate_limit:{tenant_id}"
        now = time.time()
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Get current bucket state
            bucket_data = self.redis.hmget(key, ["tokens", "last_refill"])
            current_tokens = float(bucket_data[0]) if bucket_data[0] else capacity
            last_refill = float(bucket_data[1]) if bucket_data[1] else now
            
            # Calculate tokens to add based on time passed
            time_passed = now - last_refill
            tokens_to_add = (time_passed / 60.0) * refill_rate_per_min
            
            # Update token count (cap at capacity)
            new_tokens = min(capacity, current_tokens + tokens_to_add)
            
            if new_tokens >= 1:
                # Allow request and consume one token
                new_tokens -= 1
                
                # Update Redis
                pipe.hmset(key, {
                    "tokens": new_tokens,
                    "last_refill": now
                })
                pipe.expire(key, 3600)  # Expire after 1 hour of inactivity
                pipe.execute()
                
                return RateLimitResult(
                    allowed=True, 
                    capacity=capacity, 
                    current=int(new_tokens)
                )
            else:
                # Rate limit exceeded
                retry_after = int((1 - new_tokens) * 60 / refill_rate_per_min)
                
                # Update last_refill time even for rejected requests
                pipe.hmset(key, {
                    "tokens": new_tokens,
                    "last_refill": now
                })
                pipe.expire(key, 3600)
                pipe.execute()
                
                return RateLimitResult(
                    allowed=False,
                    capacity=capacity,
                    current=int(new_tokens),
                    retry_after=retry_after
                )
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request to maintain service availability
            return RateLimitResult(allowed=True, capacity=capacity, current=capacity)


# Global limiter instance
_limiter: Optional[TokenBucketLimiter] = None


def get_limiter() -> TokenBucketLimiter:
    """Get the global rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = TokenBucketLimiter()
    return _limiter


def tenant_id_from_request(request: Request) -> str:
    """Extract tenant ID from request.
    
    Checks in order:
    1. request.state.tenant_id
    2. X-Tenant-ID header
    3. defaults to 'public'
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tenant ID string
    """
    # Check request state first
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id
    
    # Check header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id
    
    # Default fallback
    return "public"


async def limit(
    tenant_id: str, 
    capacity: int, 
    refill_rate_per_min: int
) -> None:
    """FastAPI dependency function for rate limiting.
    
    Args:
        tenant_id: Tenant identifier
        capacity: Maximum tokens in bucket
        refill_rate_per_min: Refill rate per minute
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    limiter = get_limiter()
    result = await limiter.check_limit(tenant_id, capacity, refill_rate_per_min)
    
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(result.capacity),
                "X-RateLimit-Remaining": str(result.current),
                "Retry-After": str(result.retry_after) if result.retry_after else "60"
            }
        )


def create_tenant_limit_dependency(
    capacity: int, 
    refill_rate_per_min: int
) -> Callable:
    """Create a FastAPI dependency for tenant-based rate limiting.
    
    Args:
        capacity: Maximum tokens in bucket
        refill_rate_per_min: Refill rate per minute
        
    Returns:
        FastAPI dependency function
    """
    async def rate_limit_dependency(request: Request) -> None:
        tenant_id = tenant_id_from_request(request)
        await limit(tenant_id, capacity, refill_rate_per_min)
    
    return rate_limit_dependency


def apply_rate_limit_to_app(app, capacity: int, refill_per_min: int) -> None:
    """Apply rate limiting to API v1 routes.
    
    This function scans the app routes and injects rate limiting dependency
    into routes that start with "/api/v1/".
    
    Args:
        app: FastAPI application instance
        capacity: Maximum tokens in bucket
        refill_per_min: Refill rate per minute
    """
    dependency = create_tenant_limit_dependency(capacity, refill_per_min)
    
    # Inject dependency into matching routes
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith("/api/v1/"):
            if hasattr(route, 'dependant') and route.dependant:
                # Add our dependency to the route's dependencies
                if not hasattr(route.dependant, 'dependencies'):
                    route.dependant.dependencies = []
                
                # Check if our dependency is already there to avoid duplicates
                dep_exists = any(
                    getattr(dep.call, '__name__', '') == rate_limit_dependency.__name__
                    for dep in route.dependant.dependencies
                )
                
                if not dep_exists:
                    from fastapi.dependencies.models import Dependant
                    rate_limit_dep = Dependant(call=dependency)
                    route.dependant.dependencies.append(rate_limit_dep)
    
    logger.info(f"Applied rate limiting (capacity={capacity}, refill={refill_per_min}/min) to /api/v1/* routes")