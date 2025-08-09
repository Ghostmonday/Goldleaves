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
Unit tests for the advanced rate limiter implementation.
"""
import asyncio
import pytest
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse

from .rate_limiter import (
    AdvancedRateLimiter,
    RateLimitAlgorithm,
    RateLimit,
    RateLimitState,
    InMemoryStorage,
    RateLimitChecker,
    limiter
)


class TestRateLimitChecker:
    """Test the rate limiting algorithms."""
    
    def test_fixed_window_algorithm(self):
        """Test fixed window rate limiting algorithm."""
        checker = RateLimitChecker()
        limit = RateLimit(count=5, period=60, algorithm=RateLimitAlgorithm.FIXED_WINDOW)
        state = RateLimitState()
        
        now = 1000.0
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, state = checker.check_fixed_window(state, limit, now + i)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 6th request should be denied
        allowed, state = checker.check_fixed_window(state, limit, now + 5)
        assert not allowed, "6th request should be denied"
        
        # Move to next window
        next_window = now + 60
        allowed, state = checker.check_fixed_window(state, limit, next_window)
        assert allowed, "First request in new window should be allowed"
    
    def test_sliding_window_algorithm(self):
        """Test sliding window rate limiting algorithm."""
        checker = RateLimitChecker()
        limit = RateLimit(count=3, period=60, algorithm=RateLimitAlgorithm.SLIDING_WINDOW)
        state = RateLimitState()
        
        now = 1000.0
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed, state = checker.check_sliding_window(state, limit, now + i)
            assert allowed, f"Request {i+1} should be allowed"
        
        # 4th request should be denied
        allowed, state = checker.check_sliding_window(state, limit, now + 3)
        assert not allowed, "4th request should be denied"
        
        # After 60 seconds, first request should be expired
        future_time = now + 61
        allowed, state = checker.check_sliding_window(state, limit, future_time)
        assert allowed, "Request after window expiry should be allowed"
    
    def test_token_bucket_algorithm(self):
        """Test token bucket rate limiting algorithm."""
        checker = RateLimitChecker()
        limit = RateLimit(count=5, period=60, algorithm=RateLimitAlgorithm.TOKEN_BUCKET)
        state = RateLimitState()
        
        now = 1000.0
        
        # First request initializes bucket
        allowed, state = checker.check_token_bucket(state, limit, now)
        assert allowed
        assert state.tokens == 4.0  # 5 - 1
        
        # Consume all tokens
        for _ in range(4):
            allowed, state = checker.check_token_bucket(state, limit, now + 0.1)
            assert allowed
        
        # Next request should be denied
        allowed, state = checker.check_token_bucket(state, limit, now + 0.2)
        assert not allowed
        
        # After some time, tokens should refill
        future_time = now + 12  # 12 seconds = 1 token refilled (5 tokens / 60 seconds)
        allowed, state = checker.check_token_bucket(state, limit, future_time)
        assert allowed
    
    def test_leaky_bucket_algorithm(self):
        """Test leaky bucket rate limiting algorithm."""
        checker = RateLimitChecker()
        limit = RateLimit(count=5, period=60, algorithm=RateLimitAlgorithm.LEAKY_BUCKET)
        state = RateLimitState()
        
        now = 1000.0
        
        # Fill up the bucket
        for i in range(5):
            allowed, state = checker.check_leaky_bucket(state, limit, now + i * 0.1)
            assert allowed, f"Request {i+1} should be allowed"
        
        # Next request should be denied
        allowed, state = checker.check_leaky_bucket(state, limit, now + 1)
        assert not allowed
        
        # After some time, bucket should leak
        future_time = now + 12  # 12 seconds allows 1 request to leak
        allowed, state = checker.check_leaky_bucket(state, limit, future_time)
        assert allowed


class TestInMemoryStorage:
    """Test the in-memory storage backend."""
    
    def test_get_set_state(self):
        """Test getting and setting rate limit state."""
        storage = InMemoryStorage()
        key = "test_key"
        
        # Getting non-existent key returns empty state
        state = storage.get_state(key)
        assert isinstance(state, RateLimitState)
        assert len(state.requests) == 0
        
        # Set and retrieve state
        state.request_count = 5
        storage.set_state(key, state)
        
        retrieved_state = storage.get_state(key)
        assert retrieved_state.request_count == 5
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        storage = InMemoryStorage()
        
        # Add some states with different timestamps
        old_state = RateLimitState()
        old_state.last_refill = 100.0
        storage.set_state("old_key", old_state)
        
        new_state = RateLimitState()
        new_state.last_refill = 1000.0
        storage.set_state("new_key", new_state)
        
        # Cleanup entries older than 500
        storage.cleanup_expired(500.0)
        
        # Old key should be gone, new key should remain
        old_retrieved = storage.get_state("old_key")
        new_retrieved = storage.get_state("new_key")
        
        assert old_retrieved.last_refill == 0.0  # Default value for new state
        assert new_retrieved.last_refill == 1000.0


class TestAdvancedRateLimiter:
    """Test the advanced rate limiter."""
    
    def test_parse_limit_valid_formats(self):
        """Test parsing of various valid limit formats."""
        limiter = AdvancedRateLimiter()
        
        test_cases = [
            ("5/minute", (5, 60)),
            ("10/min", (10, 60)),
            ("100/hour", (100, 3600)),
            ("1000/day", (1000, 86400)),
            ("50/second", (50, 1)),
            ("20/s", (20, 1)),
        ]
        
        for limit_str, expected in test_cases:
            result = limiter._parse_limit(limit_str)
            assert result == expected, f"Failed to parse {limit_str}"
    
    def test_parse_limit_invalid_formats(self):
        """Test parsing of invalid limit formats."""
        limiter = AdvancedRateLimiter()
        
        invalid_cases = [
            "invalid",
            "5/invalid_period",
            "invalid_count/minute",
            "5",
            "/minute",
            "5/",
        ]
        
        for invalid_str in invalid_cases:
            with pytest.raises(ValueError):
                limiter._parse_limit(invalid_str)
    
    def test_get_key_with_headers(self):
        """Test key generation with various header configurations."""
        limiter = AdvancedRateLimiter()
        
        # Test with X-Forwarded-For
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        key = limiter._get_key(request)
        assert len(key) == 16  # SHA256 hash truncated to 16 chars
        
        # Test with X-Real-IP
        request.headers = {"x-real-ip": "192.168.1.2"}
        key2 = limiter._get_key(request)
        assert key != key2  # Different IP should give different key
        
        # Test with custom key function
        def custom_key_func(req):
            return "custom_key"
        
        key3 = limiter._get_key(request, custom_key_func)
        assert key3 == "custom_key"
    
    def test_check_rate_limit_sliding_window(self):
        """Test rate limit checking with sliding window."""
        limiter = AdvancedRateLimiter()
        limit = RateLimit(count=3, period=60, algorithm=RateLimitAlgorithm.SLIDING_WINDOW)
        key = "test_key"
        
        now = 1000.0
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed, metadata = limiter.check_rate_limit(key, limit, now + i)
            assert allowed
            assert metadata["remaining"] == 3 - i - 1
        
        # 4th request should be denied
        allowed, metadata = limiter.check_rate_limit(key, limit, now + 3)
        assert not allowed
        assert metadata["remaining"] == 0
    
    @pytest.mark.asyncio
    async def test_limit_decorator_success(self):
        """Test the limit decorator with successful requests."""
        limiter = AdvancedRateLimiter()
        
        @limiter.limit("3/minute")
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        # Mock request
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # First 3 requests should succeed
        for i in range(3):
            result = await test_endpoint(request)
            assert result == {"message": "success"}
        
        # 4th request should be rate limited
        result = await test_endpoint(request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
    
    @pytest.mark.asyncio
    async def test_limit_decorator_with_burst(self):
        """Test the limit decorator with burst allowance."""
        limiter = AdvancedRateLimiter()
        
        @limiter.limit("2/minute", algorithm=RateLimitAlgorithm.TOKEN_BUCKET, burst_allowance=3)
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Should allow burst up to 2 + 3 = 5 requests initially
        for i in range(5):
            result = await test_endpoint(request)
            assert result == {"message": "success"}
        
        # 6th request should be denied
        result = await test_endpoint(request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
    
    @pytest.mark.asyncio
    async def test_skip_successful_requests(self):
        """Test skipping successful requests from rate limiting."""
        limiter = AdvancedRateLimiter()
        
        @limiter.limit("2/minute", skip_successful_requests=True)
        async def test_endpoint(request: Request):
            response = Mock()
            response.status_code = 200
            return response
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Should allow more than 2 requests because successful ones don't count
        for i in range(5):
            result = await test_endpoint(request)
            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_skip_failed_requests(self):
        """Test skipping failed requests from rate limiting."""
        limiter = AdvancedRateLimiter()
        
        call_count = 0
        
        @limiter.limit("2/minute", skip_failed_requests=True)
        async def test_endpoint(request: Request):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                # First 3 calls fail
                response = Mock()
                response.status_code = 400
                return response
            else:
                # Subsequent calls succeed
                response = Mock()
                response.status_code = 200
                return response
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # First 3 failed requests shouldn't count against rate limit
        for i in range(3):
            result = await test_endpoint(request)
            assert result.status_code == 400
        
        # Next 2 successful requests should be allowed
        for i in range(2):
            result = await test_endpoint(request)
            assert result.status_code == 200
        
        # 3rd successful request should be rate limited
        result = await test_endpoint(request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status without consuming requests."""
        limiter = AdvancedRateLimiter()
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Get initial status
        status1 = limiter.get_rate_limit_status(request, "5/minute")
        assert status1["remaining"] == 5
        
        # Get status again - should be the same (not consumed)
        status2 = limiter.get_rate_limit_status(request, "5/minute")
        assert status2["remaining"] == 5
        
        # Actually consume a request
        limit = RateLimit(count=5, period=60, algorithm=RateLimitAlgorithm.SLIDING_WINDOW)
        key = limiter._get_key(request)
        limiter.check_rate_limit(key, limit)
        
        # Now status should show one less
        status3 = limiter.get_rate_limit_status(request, "5/minute")
        assert status3["remaining"] == 4


class TestLegacyRateLimiter:
    """Test backwards compatibility with legacy rate limiter."""
    
    @pytest.mark.asyncio
    async def test_legacy_compatibility(self):
        """Test that legacy limiter still works."""
        
        @limiter.limit("2/minute")
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # First 2 requests should succeed
        for i in range(2):
            result = await test_endpoint(request)
            assert result == {"message": "success"}
        
        # 3rd request should be rate limited
        result = await test_endpoint(request)
        assert isinstance(result, JSONResponse)
        assert result.status_code == 429
    
    def test_legacy_parse_limit(self):
        """Test legacy limit parsing."""
        result = limiter._parse_limit("5/minute")
        assert result == (5, 60)
    
    def test_legacy_get_key(self):
        """Test legacy key generation."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        key = limiter._get_key(request)
        assert len(key) == 16  # Should use advanced limiter's hashed key


class TestConcurrency:
    """Test rate limiter under concurrent access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiter with concurrent requests."""
        limiter = AdvancedRateLimiter()
        
        @limiter.limit("5/minute")
        async def test_endpoint(request: Request):
            return {"message": "success"}
        
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        
        # Send 10 concurrent requests
        tasks = []
        for i in range(10):
            task = asyncio.create_task(test_endpoint(request))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful vs rate-limited responses
        success_count = sum(1 for r in results if isinstance(r, dict))
        rate_limited_count = sum(1 for r in results if isinstance(r, JSONResponse) and r.status_code == 429)
        
        # Should have exactly 5 successful and 5 rate-limited
        assert success_count == 5
        assert rate_limited_count == 5


if __name__ == "__main__":
    pytest.main([__file__])
