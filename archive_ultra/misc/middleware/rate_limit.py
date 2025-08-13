"""
Rate limiting middleware for API protection.
Implements token bucket algorithm for rate limiting requests.
"""

import time
from typing import Callable, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        now = time.time()

        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    @property
    def available_tokens(self) -> int:
        """Get number of available tokens."""
        now = time.time()
        elapsed = now - self.last_refill
        return min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        """
        Initialize rate limiter.

        Args:
            app: The ASGI application
            requests_per_minute: Requests allowed per minute
            requests_per_hour: Requests allowed per hour
            key_func: Function to extract rate limit key from request
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.key_func = key_func or self._default_key_func

        # Storage for rate limit buckets
        self.minute_buckets: Dict[str, TokenBucket] = {}
        self.hour_buckets: Dict[str, TokenBucket] = {}

        # Clean up old buckets periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def _default_key_func(self, request: Request) -> str:
        """Default function to extract rate limit key from request."""
        # Use client IP as default key
        client_ip = request.client.host if request.client else "unknown"

        # Check for forwarded IP headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip

        return client_ip

    def _cleanup_buckets(self) -> None:
        """Clean up old bucket entries."""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets that haven't been used in the last hour
        cutoff = now - 3600

        # Clean minute buckets
        expired_minute_keys = [
            key for key, bucket in self.minute_buckets.items()
            if bucket.last_refill < cutoff
        ]
        for key in expired_minute_keys:
            del self.minute_buckets[key]

        # Clean hour buckets
        expired_hour_keys = [
            key for key, bucket in self.hour_buckets.items()
            if bucket.last_refill < cutoff
        ]
        for key in expired_hour_keys:
            del self.hour_buckets[key]

        self.last_cleanup = now

    def _get_or_create_bucket(
        self,
        buckets: Dict[str, TokenBucket],
        key: str,
        capacity: int,
        refill_rate: float
    ) -> TokenBucket:
        """Get or create a token bucket for the given key."""
        if key not in buckets:
            buckets[key] = TokenBucket(capacity, refill_rate)
        return buckets[key]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with rate limiting.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint

        Returns:
            Response or rate limit error
        """
        # Skip rate limiting for certain paths
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Clean up old buckets periodically
        self._cleanup_buckets()

        # Get rate limit key
        key = self.key_func(request)

        # Get or create buckets
        minute_bucket = self._get_or_create_bucket(
            self.minute_buckets,
            key,
            self.requests_per_minute,
            self.requests_per_minute / 60.0  # refill rate per second
        )

        hour_bucket = self._get_or_create_bucket(
            self.hour_buckets,
            key,
            self.requests_per_hour,
            self.requests_per_hour / 3600.0  # refill rate per second
        )

        # Check both rate limits
        minute_allowed = minute_bucket.consume()
        hour_allowed = hour_bucket.consume()

        if not minute_allowed or not hour_allowed:
            # Rate limit exceeded
            response = JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60 if not minute_allowed else 3600
                }
            )

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(int(minute_bucket.available_tokens))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

            return response

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(minute_bucket.available_tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response
