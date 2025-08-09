# tests/test_token_service.py

import pytest
import asyncio
from datetime import timedelta
from uuid import uuid4

from token_service import (
    create_access_token,
    create_refresh_token,
    verify_token,
    revoke_token,
    is_token_revoked,
    create_email_token,
    verify_email_token,
    create_token_response,
    refresh_access_token,
    cleanup_expired_tokens,
    get_token_stats,
    send_email_verification,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError
)

class TestTokenService:
    """Test cases for token service functions."""
    
    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """Test creating access tokens."""
        data = {"sub": "test_user_123", "email": "test@example.com"}
        token = await create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self):
        """Test creating refresh tokens."""
        data = {"sub": "test_user_123", "email": "test@example.com"}
        token = await create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self):
        """Test verifying valid tokens."""
        data = {"sub": "test_user_123", "email": "test@example.com"}
        token = await create_access_token(data)
        
        payload = await verify_token(token)
        assert payload["sub"] == "test_user_123"
        assert payload["type"] == "access"
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test verifying invalid tokens."""
        with pytest.raises(TokenInvalidError):
            await verify_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_token_revocation(self):
        """Test token revocation functionality."""
        data = {"sub": "test_user_123"}
        token = await create_access_token(data)
        
        # Token should not be revoked initially
        payload = await verify_token(token)
        jti = payload.get("jti")
        assert not await is_token_revoked(jti)
        
        # Revoke the token
        success = await revoke_token(token)
        assert success
        
        # Token should now be revoked
        assert await is_token_revoked(jti)
        
        # Verifying revoked token should raise error
        with pytest.raises(TokenRevokedError):
            await verify_token(token)
    
    @pytest.mark.asyncio
    async def test_create_email_token(self):
        """Test creating email verification tokens."""
        user_id = uuid4()
        email = "test@example.com"
        
        token = await create_email_token(user_id, email)
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_email_token(self):
        """Test verifying email verification tokens."""
        user_id = uuid4()
        email = "test@example.com"
        
        token = await create_email_token(user_id, email)
        result = await verify_email_token(token)
        
        assert result is not None
        assert result["user_id"] == str(user_id)
        assert result["email"] == email
    
    @pytest.mark.asyncio
    async def test_verify_email_token_invalid(self):
        """Test verifying invalid email tokens."""
        result = await verify_email_token("invalid_token")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_token_response(self):
        """Test creating complete token response."""
        user_id = "test_user_123"
        response = await create_token_response(user_id)
        
        assert "access_token" in response
        assert "refresh_token" in response
        assert "token_type" in response
        assert "expires_at" in response
        assert "refresh_expires_at" in response
        assert response["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self):
        """Test refreshing access tokens."""
        user_id = "test_user_123"
        data = {"sub": user_id}
        
        # Create refresh token
        refresh_token = await create_refresh_token(data)
        
        # Use refresh token to get new access token
        response = await refresh_access_token(refresh_token)
        
        assert "access_token" in response
        assert "refresh_token" in response
        assert response["refresh_token"] == refresh_token  # Same refresh token
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        count = await cleanup_expired_tokens()
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_get_token_stats(self):
        """Test getting token statistics."""
        stats = await get_token_stats()
        
        assert isinstance(stats, dict)
        assert "revoked_tokens" in stats
        assert "in_memory_revoked" in stats
        assert "active_tokens" in stats
        assert "expired_tokens" in stats
    
    @pytest.mark.asyncio
    async def test_send_email_verification(self):
        """Test sending email verification."""
        user_id = "test_user_123"
        email = "test@example.com"
        verification_token = "test_token"
        
        success = await send_email_verification(user_id, email, verification_token)
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_token_expiration(self):
        """Test token expiration handling."""
        data = {"sub": "test_user_123"}
        
        # Create token with very short expiry
        short_expiry = timedelta(seconds=1)
        token = await create_access_token(data, expires_delta=short_expiry)
        
        # Wait for token to expire
        await asyncio.sleep(2)
        
        # Verifying expired token should raise error
        with pytest.raises(TokenExpiredError):
            await verify_token(token)

if __name__ == "__main__":
    # Run basic tests
    async def run_tests():
        test_instance = TestTokenService()
        
        print("Running token service tests...")
        
        try:
            await test_instance.test_create_access_token()
            print("✓ test_create_access_token passed")
        except Exception as e:
            print(f"✗ test_create_access_token failed: {e}")
        
        try:
            await test_instance.test_create_refresh_token()
            print("✓ test_create_refresh_token passed")
        except Exception as e:
            print(f"✗ test_create_refresh_token failed: {e}")
        
        try:
            await test_instance.test_verify_token_valid()
            print("✓ test_verify_token_valid passed")
        except Exception as e:
            print(f"✗ test_verify_token_valid failed: {e}")
        
        try:
            await test_instance.test_create_token_response()
            print("✓ test_create_token_response passed")
        except Exception as e:
            print(f"✗ test_create_token_response failed: {e}")
        
        print("Token service tests completed!")
    
    asyncio.run(run_tests())
