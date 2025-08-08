# tests/test_agent.py

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from agent import (
    create_email_verification_token,
    verify_email_verification_token,
    create_access_token,
    create_refresh_token,
    is_token_revoked,
    revoke_token,
    send_verification_email,
    send_welcome_email,
    get_services_async,
    get_token_functions_async,
    get_email_functions_async,
    health_check_services,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError
)

class TestAgent:
    """Test cases for agent service functions."""
    
    @pytest.mark.asyncio
    async def test_create_email_verification_token(self):
        """Test creating email verification tokens."""
        user_id = "test_user_123"
        email = "test@example.com"
        
        token = await create_email_verification_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_email_verification_token(self):
        """Test verifying email verification tokens."""
        user_id = "test_user_123"
        email = "test@example.com"
        
        token = await create_email_verification_token(user_id, email)
        result = await verify_email_verification_token(token)
        
        assert isinstance(result, dict)
        assert result["user_id"] == user_id
        assert result["email"] == email
    
    @pytest.mark.asyncio
    async def test_verify_email_verification_token_invalid(self):
        """Test verifying invalid email verification tokens."""
        with pytest.raises(TokenInvalidError):
            await verify_email_verification_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """Test creating access tokens."""
        data = {"sub": "test_user_123"}
        token = await create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self):
        """Test creating refresh tokens."""
        data = {"sub": "test_user_123"}
        token = await create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_token_revocation(self):
        """Test token revocation functionality."""
        test_jti = "test_jti_456"
        
        # Initially not revoked
        assert not await is_token_revoked(test_jti)
        
        # Revoke token
        success = await revoke_token(test_jti, "test_user")
        assert success
        
        # Now should be revoked
        assert await is_token_revoked(test_jti)
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self):
        """Test sending verification emails."""
        user_id = "test_user_123"
        email = "test@example.com"
        
        success = await send_verification_email(user_id, email)
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test sending welcome emails."""
        email = "test@example.com"
        first_name = "Test"
        
        success = await send_welcome_email(email, first_name)
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_get_services_async(self):
        """Test getting async services."""
        services = await get_services_async()
        
        assert isinstance(services, dict)
        assert "create_email_verification_token" in services
        assert "verify_email_verification_token" in services
        assert "create_access_token" in services
        assert "create_refresh_token" in services
        assert "send_verification_email" in services
        assert "send_welcome_email" in services
        assert "is_token_revoked" in services
        assert "revoke_token" in services
    
    @pytest.mark.asyncio
    async def test_get_token_functions_async(self):
        """Test getting async token functions."""
        functions = await get_token_functions_async()
        
        assert isinstance(functions, dict)
        assert "create_email_verification_token" in functions
        assert "verify_email_verification_token" in functions
        assert "create_access_token" in functions
        assert "create_refresh_token" in functions
    
    @pytest.mark.asyncio
    async def test_get_email_functions_async(self):
        """Test getting async email functions."""
        functions = await get_email_functions_async()
        
        assert isinstance(functions, dict)
        assert "send_verification_email" in functions
        assert "send_welcome_email" in functions
    
    @pytest.mark.asyncio
    async def test_health_check_services(self):
        """Test health check of services."""
        health = await health_check_services()
        
        assert isinstance(health, dict)
        assert "timestamp" in health
        assert "services" in health
        assert "overall_status" in health
        
        services = health["services"]
        assert "database" in services
        assert "cache" in services
        assert "config" in services
    
    @pytest.mark.asyncio
    async def test_email_token_workflow(self):
        """Test complete email verification token workflow."""
        user_id = "test_user_123"
        email = "test@example.com"
        
        # Create token
        token = await create_email_verification_token(user_id, email)
        
        # Verify token
        result = await verify_email_verification_token(token)
        assert result["user_id"] == user_id
        assert result["email"] == email
        
        # Send verification email
        success = await send_verification_email(user_id, email)
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_token_error_handling(self):
        """Test error handling in token operations."""
        # Test with empty token
        with pytest.raises(TokenInvalidError):
            await verify_email_verification_token("")
        
        # Test with None token
        with pytest.raises(TokenInvalidError):
            await verify_email_verification_token(None)

if __name__ == "__main__":
    # Run basic tests
    async def run_tests():
        test_instance = TestAgent()
        
        print("Running agent tests...")
        
        try:
            await test_instance.test_create_email_verification_token()
            print("✓ test_create_email_verification_token passed")
        except Exception as e:
            print(f"✗ test_create_email_verification_token failed: {e}")
        
        try:
            await test_instance.test_verify_email_verification_token()
            print("✓ test_verify_email_verification_token passed")
        except Exception as e:
            print(f"✗ test_verify_email_verification_token failed: {e}")
        
        try:
            await test_instance.test_create_access_token()
            print("✓ test_create_access_token passed")
        except Exception as e:
            print(f"✗ test_create_access_token failed: {e}")
        
        try:
            await test_instance.test_get_services_async()
            print("✓ test_get_services_async passed")
        except Exception as e:
            print(f"✗ test_get_services_async failed: {e}")
        
        try:
            await test_instance.test_health_check_services()
            print("✓ test_health_check_services passed")
        except Exception as e:
            print(f"✗ test_health_check_services failed: {e}")
        
        print("Agent tests completed!")
    
    asyncio.run(run_tests())
