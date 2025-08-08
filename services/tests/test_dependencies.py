# tests/test_dependencies.py

import pytest
import asyncio
from datetime import datetime, timedelta

from dependencies import (
    get_db_session,
    get_audit_service,
    get_cache_service,
    get_email_service,
    get_webhook_service,
    get_config_service,
    is_token_revoked,
    revoke_token,
    create_email_message,
    send_email_async,
    generate_jti,
    create_token_payload,
    cleanup_expired_revoked_tokens,
    get_dependency_health_status
)

class TestDependencies:
    """Test cases for dependency injection functions."""
    
    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """Test database session dependency injection."""
        db = await get_db_session()
        
        # Test that we can call session methods
        await db.execute("SELECT 1")
        await db.fetch_one("SELECT 1")
        await db.fetch_all("SELECT 1")
        await db.commit()
        await db.rollback()
    
    @pytest.mark.asyncio
    async def test_get_audit_service(self):
        """Test audit service dependency injection."""
        audit = await get_audit_service()
        
        # Test audit logging
        await audit.log_event("TEST_EVENT", "test_user", {"detail": "test"})
    
    @pytest.mark.asyncio
    async def test_get_cache_service(self):
        """Test cache service dependency injection."""
        cache = await get_cache_service()
        
        # Test cache operations
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        await cache.delete("test_key")
    
    @pytest.mark.asyncio
    async def test_get_email_service(self):
        """Test email service dependency injection."""
        email = await get_email_service()
        
        # Test email sending
        await email.send_notification("test@example.com", "Test Subject", "Test Body")
    
    @pytest.mark.asyncio
    async def test_get_webhook_service(self):
        """Test webhook service dependency injection."""
        webhook = await get_webhook_service()
        
        # Test webhook notification
        await webhook.notify("test_event", {"data": "test"})
    
    @pytest.mark.asyncio
    async def test_get_config_service(self):
        """Test config service dependency injection."""
        config = await get_config_service()
        
        # Test config methods
        setting = config.get_setting("SECRET_KEY", "default")
        jwt_settings = config.get_jwt_settings()
        email_settings = config.get_email_settings()
        
        assert isinstance(jwt_settings, dict)
        assert isinstance(email_settings, dict)
    
    @pytest.mark.asyncio
    async def test_token_revocation_with_dependencies(self):
        """Test token revocation with dependency injection."""
        test_jti = "test_jti_123"
        
        # Initially not revoked
        assert not await is_token_revoked(test_jti)
        
        # Revoke token
        success = await revoke_token(test_jti, "test_user")
        assert success
        
        # Now should be revoked
        assert await is_token_revoked(test_jti)
    
    @pytest.mark.asyncio
    async def test_create_email_message(self):
        """Test email message creation."""
        message = await create_email_message(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert message is not None
        assert message["To"] == "test@example.com"
        assert message["Subject"] == "Test Subject"
    
    @pytest.mark.asyncio
    async def test_send_email_async(self):
        """Test async email sending."""
        success = await send_email_async(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        
        assert isinstance(success, bool)
    
    def test_generate_jti(self):
        """Test JWT ID generation."""
        jti = generate_jti()
        
        assert isinstance(jti, str)
        assert len(jti) > 0
        
        # Generate another and ensure uniqueness
        jti2 = generate_jti()
        assert jti != jti2
    
    @pytest.mark.asyncio
    async def test_create_token_payload(self):
        """Test token payload creation."""
        data = {"sub": "test_user"}
        payload = await create_token_payload(data)
        
        assert isinstance(payload, dict)
        assert payload["sub"] == "test_user"
        assert "exp" in payload
        assert "jti" in payload
        assert "iat" in payload
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_revoked_tokens(self):
        """Test cleanup of expired revoked tokens."""
        count = await cleanup_expired_revoked_tokens()
        
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_get_dependency_health_status(self):
        """Test health status of dependencies."""
        health = await get_dependency_health_status()
        
        assert isinstance(health, dict)
        assert "timestamp" in health
        assert "services" in health
        
        services = health["services"]
        assert "database" in services
        assert "cache" in services
        assert "email" in services

if __name__ == "__main__":
    # Run basic tests
    async def run_tests():
        test_instance = TestDependencies()
        
        print("Running dependencies tests...")
        
        try:
            await test_instance.test_get_db_session()
            print("✓ test_get_db_session passed")
        except Exception as e:
            print(f"✗ test_get_db_session failed: {e}")
        
        try:
            await test_instance.test_get_audit_service()
            print("✓ test_get_audit_service passed")
        except Exception as e:
            print(f"✗ test_get_audit_service failed: {e}")
        
        try:
            await test_instance.test_get_cache_service()
            print("✓ test_get_cache_service passed")
        except Exception as e:
            print(f"✗ test_get_cache_service failed: {e}")
        
        try:
            await test_instance.test_get_config_service()
            print("✓ test_get_config_service passed")
        except Exception as e:
            print(f"✗ test_get_config_service failed: {e}")
        
        try:
            test_instance.test_generate_jti()
            print("✓ test_generate_jti passed")
        except Exception as e:
            print(f"✗ test_generate_jti failed: {e}")
        
        print("Dependencies tests completed!")
    
    asyncio.run(run_tests())
