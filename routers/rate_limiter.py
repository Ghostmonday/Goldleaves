# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Advanced rate limiter with contract compliance and isolated dependencies

"""Advanced rate limiting implementations with multiple algorithms and storage backends."""

import asyncio
import time
import json
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from contextlib import asynccontextmanager

from .contract import RouterContract, ServiceProtocol
from .schemas import RateLimitStatusSchema, RateLimitExceededSchema

class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms."""
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"

class RateLimitBackend(str, Enum):
    """Rate limit storage backends."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_capacity: int = 10
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    backend: RateLimitBackend = RateLimitBackend.MEMORY
    key_prefix: str = "rate_limit"
    grace_period: int = 5  # seconds
    enable_burst: bool = True
    adaptive_factor: float = 1.5

@dataclass
class RateLimitResult:
    """Rate limit check result."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    algorithm_used: str = ""
    backend_used: str = ""
    window_start: Optional[int] = None
    window_end: Optional[int] = None

class RateLimitBackendInterface(ABC):
    """Abstract interface for rate limit backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

class MemoryBackend(RateLimitBackendInterface):
    """In-memory rate limit backend."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def _cleanup_expired(self):
        """Remove expired keys."""
        now = time.time()
        expired_keys = [k for k, exp in self.expiry.items() if exp <= now]
        for key in expired_keys:
            self.data.pop(key, None)
            self.expiry.pop(key, None)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        async with self._lock:
            await self._cleanup_expired()
            return self.data.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        async with self._lock:
            self.data[key] = value
            if ttl:
                self.expiry[key] = time.time() + ttl
            return True
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter."""
        async with self._lock:
            await self._cleanup_expired()
            current = self.data.get(key, 0)
            if isinstance(current, (int, float)):
                new_value = current + amount
            else:
                new_value = amount
            
            self.data[key] = new_value
            if ttl and key not in self.expiry:
                self.expiry[key] = time.time() + ttl
            
            return new_value
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        async with self._lock:
            deleted = key in self.data
            self.data.pop(key, None)
            self.expiry.pop(key, None)
            return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        async with self._lock:
            await self._cleanup_expired()
            return key in self.data

class RedisBackend(RateLimitBackendInterface):
    """Redis rate limit backend (mock implementation)."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        # Mock Redis with in-memory fallback
        self._memory_backend = MemoryBackend()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        # In production, use actual Redis client
        return await self._memory_backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL."""
        return await self._memory_backend.set(key, value, ttl)
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment counter."""
        return await self._memory_backend.increment(key, amount, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        return await self._memory_backend.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self._memory_backend.exists(key)

class RateLimitAlgorithmInterface(ABC):
    """Abstract interface for rate limiting algorithms."""
    
    @abstractmethod
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check if request is within rate limit."""
        pass

class SlidingWindowRateLimiter(RateLimitAlgorithmInterface):
    """Sliding window rate limiter."""
    
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        now = time.time()
        window_size = 60  # 1 minute window
        
        # Get current window data
        window_key = f"{config.key_prefix}:sliding:{key}"
        window_data = await backend.get(window_key)
        
        if window_data is None:
            window_data = []
        elif isinstance(window_data, str):
            try:
                window_data = json.loads(window_data)
            except json.JSONDecodeError:
                window_data = []
        
        # Remove expired entries
        cutoff = now - window_size
        window_data = [timestamp for timestamp in window_data if timestamp > cutoff]
        
        # Check if we can add a new request
        current_count = len(window_data)
        limit = config.requests_per_minute
        
        if current_count >= limit:
            # Calculate retry after based on oldest request
            if window_data:
                oldest_request = min(window_data)
                retry_after = int(oldest_request + window_size - now) + 1
            else:
                retry_after = window_size
            
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=int(now + window_size),
                retry_after=retry_after,
                algorithm_used="sliding_window",
                backend_used=config.backend.value,
                window_start=int(cutoff),
                window_end=int(now)
            )
        
        # Add current request
        window_data.append(now)
        
        # Save updated window
        await backend.set(window_key, json.dumps(window_data), ttl=window_size + 60)
        
        remaining = limit - len(window_data)
        reset_time = int(now + window_size)
        
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            algorithm_used="sliding_window",
            backend_used=config.backend.value,
            window_start=int(cutoff),
            window_end=int(now)
        )

class TokenBucketRateLimiter(RateLimitAlgorithmInterface):
    """Token bucket rate limiter."""
    
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        now = time.time()
        bucket_key = f"{config.key_prefix}:bucket:{key}"
        
        # Get current bucket state
        bucket_data = await backend.get(bucket_key)
        
        if bucket_data is None:
            # Initialize bucket
            bucket_data = {
                "tokens": config.burst_capacity,
                "last_refill": now,
                "capacity": config.burst_capacity
            }
        elif isinstance(bucket_data, str):
            try:
                bucket_data = json.loads(bucket_data)
            except json.JSONDecodeError:
                bucket_data = {
                    "tokens": config.burst_capacity,
                    "last_refill": now,
                    "capacity": config.burst_capacity
                }
        
        # Calculate tokens to add based on time passed
        time_passed = now - bucket_data["last_refill"]
        refill_rate = config.requests_per_minute / 60.0  # tokens per second
        tokens_to_add = time_passed * refill_rate
        
        # Update bucket
        bucket_data["tokens"] = min(
            bucket_data["capacity"],
            bucket_data["tokens"] + tokens_to_add
        )
        bucket_data["last_refill"] = now
        
        # Check if we can consume a token
        if bucket_data["tokens"] >= 1:
            bucket_data["tokens"] -= 1
            
            # Save updated bucket
            await backend.set(bucket_key, json.dumps(bucket_data), ttl=3600)
            
            return RateLimitResult(
                allowed=True,
                limit=config.requests_per_minute,
                remaining=int(bucket_data["tokens"]),
                reset_time=int(now + (bucket_data["capacity"] - bucket_data["tokens"]) / refill_rate),
                algorithm_used="token_bucket",
                backend_used=config.backend.value
            )
        else:
            # Calculate retry after
            retry_after = int((1 - bucket_data["tokens"]) / refill_rate) + 1
            
            return RateLimitResult(
                allowed=False,
                limit=config.requests_per_minute,
                remaining=0,
                reset_time=int(now + retry_after),
                retry_after=retry_after,
                algorithm_used="token_bucket",
                backend_used=config.backend.value
            )

class FixedWindowRateLimiter(RateLimitAlgorithmInterface):
    """Fixed window rate limiter."""
    
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm."""
        now = time.time()
        window_size = 60  # 1 minute window
        current_window = int(now // window_size)
        
        window_key = f"{config.key_prefix}:fixed:{key}:{current_window}"
        
        # Get current count
        current_count = await backend.get(window_key) or 0
        if isinstance(current_count, str):
            try:
                current_count = int(current_count)
            except ValueError:
                current_count = 0
        
        limit = config.requests_per_minute
        
        if current_count >= limit:
            window_end = (current_window + 1) * window_size
            retry_after = int(window_end - now)
            
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=int(window_end),
                retry_after=retry_after,
                algorithm_used="fixed_window",
                backend_used=config.backend.value,
                window_start=int(current_window * window_size),
                window_end=int(window_end)
            )
        
        # Increment counter
        new_count = await backend.increment(window_key, 1, ttl=window_size + 60)
        remaining = limit - new_count
        window_end = (current_window + 1) * window_size
        
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_time=int(window_end),
            algorithm_used="fixed_window",
            backend_used=config.backend.value,
            window_start=int(current_window * window_size),
            window_end=int(window_end)
        )

class LeakyBucketRateLimiter(RateLimitAlgorithmInterface):
    """Leaky bucket rate limiter."""
    
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check rate limit using leaky bucket algorithm."""
        now = time.time()
        bucket_key = f"{config.key_prefix}:leaky:{key}"
        
        # Get current queue
        queue_data = await backend.get(bucket_key)
        
        if queue_data is None:
            queue = []
        elif isinstance(queue_data, str):
            try:
                queue = json.loads(queue_data)
            except json.JSONDecodeError:
                queue = []
        else:
            queue = queue_data
        
        # Remove processed items (leak)
        leak_rate = config.requests_per_minute / 60.0  # requests per second
        time_passed = 0
        if queue:
            last_item_time = queue[-1] if queue else now
            time_passed = now - last_item_time
        
        items_to_remove = int(time_passed * leak_rate)
        if items_to_remove > 0 and queue:
            queue = queue[items_to_remove:]
        
        # Check if bucket is full
        capacity = config.burst_capacity
        if len(queue) >= capacity:
            # Calculate retry after
            if queue:
                next_leak_time = queue[0] + (1 / leak_rate)
                retry_after = max(1, int(next_leak_time - now))
            else:
                retry_after = int(1 / leak_rate)
            
            return RateLimitResult(
                allowed=False,
                limit=config.requests_per_minute,
                remaining=0,
                reset_time=int(now + retry_after),
                retry_after=retry_after,
                algorithm_used="leaky_bucket",
                backend_used=config.backend.value
            )
        
        # Add request to queue
        queue.append(now)
        
        # Save updated queue
        await backend.set(bucket_key, json.dumps(queue), ttl=3600)
        
        remaining = capacity - len(queue)
        reset_time = int(now + (len(queue) / leak_rate))
        
        return RateLimitResult(
            allowed=True,
            limit=config.requests_per_minute,
            remaining=remaining,
            reset_time=reset_time,
            algorithm_used="leaky_bucket",
            backend_used=config.backend.value
        )

class AdaptiveRateLimiter(RateLimitAlgorithmInterface):
    """Adaptive rate limiter that adjusts based on traffic patterns."""
    
    async def check_rate_limit(
        self,
        key: str,
        config: RateLimitConfig,
        backend: RateLimitBackendInterface
    ) -> RateLimitResult:
        """Check rate limit using adaptive algorithm."""
        now = time.time()
        window_size = 60  # 1 minute window
        
        # Get traffic pattern data
        pattern_key = f"{config.key_prefix}:adaptive:{key}:pattern"
        pattern_data = await backend.get(pattern_key)
        
        if pattern_data is None:
            pattern_data = {
                "requests": [],
                "avg_rate": config.requests_per_minute,
                "peak_rate": config.requests_per_minute,
                "last_update": now
            }
        elif isinstance(pattern_data, str):
            try:
                pattern_data = json.loads(pattern_data)
            except json.JSONDecodeError:
                pattern_data = {
                    "requests": [],
                    "avg_rate": config.requests_per_minute,
                    "peak_rate": config.requests_per_minute,
                    "last_update": now
                }
        
        # Clean old requests
        cutoff = now - window_size
        pattern_data["requests"] = [
            req_time for req_time in pattern_data["requests"] 
            if req_time > cutoff
        ]
        
        # Calculate current rate
        current_rate = len(pattern_data["requests"])
        
        # Update adaptive limit
        if current_rate > pattern_data["peak_rate"]:
            pattern_data["peak_rate"] = current_rate
        
        # Calculate adaptive factor
        if current_rate > pattern_data["avg_rate"]:
            adaptive_factor = config.adaptive_factor
        else:
            adaptive_factor = 1.0
        
        adaptive_limit = int(config.requests_per_minute * adaptive_factor)
        
        # Check limit
        if current_rate >= adaptive_limit:
            retry_after = window_size // adaptive_limit if adaptive_limit > 0 else window_size
            
            return RateLimitResult(
                allowed=False,
                limit=adaptive_limit,
                remaining=0,
                reset_time=int(now + window_size),
                retry_after=retry_after,
                algorithm_used="adaptive",
                backend_used=config.backend.value
            )
        
        # Add current request
        pattern_data["requests"].append(now)
        
        # Update average rate (exponential moving average)
        alpha = 0.1  # smoothing factor
        pattern_data["avg_rate"] = (
            alpha * current_rate + (1 - alpha) * pattern_data["avg_rate"]
        )
        pattern_data["last_update"] = now
        
        # Save pattern data
        await backend.set(pattern_key, json.dumps(pattern_data), ttl=window_size + 60)
        
        remaining = adaptive_limit - len(pattern_data["requests"])
        
        return RateLimitResult(
            allowed=True,
            limit=adaptive_limit,
            remaining=remaining,
            reset_time=int(now + window_size),
            algorithm_used="adaptive",
            backend_used=config.backend.value
        )

class RateLimiter:
    """Main rate limiter class that orchestrates different algorithms and backends."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.backend = self._create_backend()
        self.algorithm = self._create_algorithm()
    
    def _create_backend(self) -> RateLimitBackendInterface:
        """Create backend instance based on configuration."""
        if self.config.backend == RateLimitBackend.MEMORY:
            return MemoryBackend()
        elif self.config.backend == RateLimitBackend.REDIS:
            return RedisBackend()
        else:
            # Default to memory
            return MemoryBackend()
    
    def _create_algorithm(self) -> RateLimitAlgorithmInterface:
        """Create algorithm instance based on configuration."""
        if self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return SlidingWindowRateLimiter()
        elif self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return TokenBucketRateLimiter()
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return FixedWindowRateLimiter()
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return LeakyBucketRateLimiter()
        elif self.config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            return AdaptiveRateLimiter()
        else:
            # Default to sliding window
            return SlidingWindowRateLimiter()
    
    async def check_rate_limit(self, key: str) -> RateLimitResult:
        """Check if request is within rate limit."""
        return await self.algorithm.check_rate_limit(key, self.config, self.backend)
    
    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a key."""
        deleted = False
        
        # Try to delete all possible keys for this identifier
        for algo in RateLimitAlgorithm:
            for prefix in ["sliding", "bucket", "fixed", "leaky", "adaptive"]:
                test_key = f"{self.config.key_prefix}:{prefix}:{key}"
                if await self.backend.delete(test_key):
                    deleted = True
        
        return deleted
    
    async def get_rate_limit_status(self, key: str) -> RateLimitStatusSchema:
        """Get current rate limit status without consuming quota."""
        # Create a temporary config for status check
        temp_config = RateLimitConfig(
            requests_per_minute=self.config.requests_per_minute,
            algorithm=self.config.algorithm,
            backend=self.config.backend,
            key_prefix=self.config.key_prefix
        )
        
        # Check status without incrementing
        result = await self.algorithm.check_rate_limit(key, temp_config, self.backend)
        
        return RateLimitStatusSchema(
            limit=result.limit,
            remaining=result.remaining,
            reset_time=result.reset_time,
            retry_after=result.retry_after,
            allowed=result.allowed,
            algorithm_used=result.algorithm_used,
            backend_used=result.backend_used
        )

# Rate limiter registry for different contexts
_rate_limiters: Dict[str, RateLimiter] = {}

def get_rate_limiter(name: str = "default") -> RateLimiter:
    """Get or create a rate limiter instance."""
    if name not in _rate_limiters:
        config = RateLimitConfig()
        _rate_limiters[name] = RateLimiter(config)
    return _rate_limiters[name]

def create_rate_limiter(name: str, config: RateLimitConfig) -> RateLimiter:
    """Create a named rate limiter with specific configuration."""
    _rate_limiters[name] = RateLimiter(config)
    return _rate_limiters[name]

async def check_rate_limit(key: str, limiter_name: str = "default") -> RateLimitResult:
    """Convenience function to check rate limit."""
    limiter = get_rate_limiter(limiter_name)
    return await limiter.check_rate_limit(key)

async def reset_rate_limit(key: str, limiter_name: str = "default") -> bool:
    """Convenience function to reset rate limit."""
    limiter = get_rate_limiter(limiter_name)
    return await limiter.reset_rate_limit(key)

# Create default rate limiters for different use cases
create_rate_limiter("auth", RateLimitConfig(
    requests_per_minute=10,
    requests_per_hour=60,
    algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
    burst_capacity=5
))

create_rate_limiter("api", RateLimitConfig(
    requests_per_minute=100,
    requests_per_hour=6000,
    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
    burst_capacity=20
))

create_rate_limiter("admin", RateLimitConfig(
    requests_per_minute=200,
    requests_per_hour=12000,
    algorithm=RateLimitAlgorithm.ADAPTIVE,
    burst_capacity=50,
    adaptive_factor=2.0
))

# Export all classes and functions
__all__ = [
    "RateLimitAlgorithm", "RateLimitBackend", "RateLimitConfig", "RateLimitResult",
    "RateLimitBackendInterface", "MemoryBackend", "RedisBackend",
    "RateLimitAlgorithmInterface", "SlidingWindowRateLimiter", "TokenBucketRateLimiter",
    "FixedWindowRateLimiter", "LeakyBucketRateLimiter", "AdaptiveRateLimiter",
    "RateLimiter", "get_rate_limiter", "create_rate_limiter", 
    "check_rate_limit", "reset_rate_limit"
]
