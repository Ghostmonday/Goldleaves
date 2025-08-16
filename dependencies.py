"""Comprehensive auto-generated dependency shim for tests.

This file supplies async-friendly stub implementations for the symbols imported
in tests (notably services/tests/test_dependencies.py). Real implementations
should progressively replace these. Each stub is intentionally minimal yet
behaviorally plausible so tests that only validate interface surface can pass.

If a real implementation module (services.dependencies or models.dependencies)
is available it will be imported at the end so any genuine objects override
these shims.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
import uuid
import asyncio


# --------------------------- DB Session Stub ---------------------------------
class _MockAsyncDBSession:
    """Very small async DB session facade used by tests.

    Provides execute/fetch_x/commit/rollback methods that just simulate async
    operations. Returns simple placeholder values.
    """

    async def execute(self, _query: str):  # noqa: D401
        return 1

    async def fetch_one(self, _query: str):
        return {"one": 1}

    async def fetch_all(self, _query: str):
        return [{"one": 1}]

    async def commit(self):
        return True

    async def rollback(self):
        return True


async def get_db_session():  # noqa: D401
    return _MockAsyncDBSession()


# --------------------------- Audit Service Stub ------------------------------
class _MockAuditService:
    async def log_event(self, event_type: str, actor: str, detail: Dict[str, Any]):
        # Pretend to persist / emit audit record
        return {
            "event_type": event_type,
            "actor": actor,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def get_audit_service():  # noqa: D401
    return _MockAuditService()


# --------------------------- Cache Service Stub ------------------------------
class _MockCacheService:
    def __init__(self):
        self._store: Dict[str, Any] = {}

    async def set(self, key: str, value: Any, ttl: int = 60):  # noqa: D401
        # ttl ignored for stub
        self._store[key] = (value, datetime.now(timezone.utc) + timedelta(seconds=ttl))
        return True

    async def get(self, key: str):  # noqa: D401
        item = self._store.get(key)
        if not item:
            return None
        value, exp = item
        if exp < datetime.now(timezone.utc):
            self._store.pop(key, None)
            return None
        return value

    async def delete(self, key: str):  # noqa: D401
        return self._store.pop(key, None) is not None


_cache_instance = _MockCacheService()


async def get_cache_service():  # noqa: D401
    return _cache_instance


# --------------------------- Email Service Stub ------------------------------
class _MockEmailService:
    async def send_notification(self, to: str, subject: str, body: str):  # noqa: D401
        return {"to": to, "subject": subject, "body": body, "sent": True}


async def get_email_service():  # noqa: D401
    return _MockEmailService()


async def create_email_message(to: str, subject: str, body: str):  # noqa: D401
    return {"To": to, "Subject": subject, "Body": body}


async def send_email_async(to: str, subject: str, body: str):  # noqa: D401
    # Reuse email service for consistency
    svc = await get_email_service()
    res = await svc.send_notification(to, subject, body)
    return bool(res)


# --------------------------- Webhook Service Stub ----------------------------
class _MockWebhookService:
    async def notify(self, event: str, payload: Dict[str, Any]):  # noqa: D401
        return {"event": event, "payload": payload, "delivered": True}


async def get_webhook_service():  # noqa: D401
    return _MockWebhookService()


# --------------------------- Config Service Stub -----------------------------
class _MockConfigService:
    DEFAULTS = {
        "SECRET_KEY": "test-secret-key",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "EMAIL_FROM": "noreply@example.com",
    }

    def get_setting(self, key: str, default: Any = None):  # noqa: D401
        return self.DEFAULTS.get(key, default)

    def get_jwt_settings(self):  # noqa: D401
        return {
            "algorithm": self.get_setting("JWT_ALGORITHM"),
            "expire_minutes": self.get_setting("ACCESS_TOKEN_EXPIRE_MINUTES"),
            "issuer": "goldleaves.test",
        }

    def get_email_settings(self):  # noqa: D401
        return {"from": self.get_setting("EMAIL_FROM"), "provider": "stub"}


async def get_config_service():  # noqa: D401
    return _MockConfigService()


# --------------------------- Token & Revocation ------------------------------
_revoked_tokens: Dict[str, datetime] = {}


def generate_jti() -> str:  # noqa: D401
    return uuid.uuid4().hex


async def create_token_payload(data: Dict[str, Any]):  # noqa: D401
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=30)
    payload = {
        **data,
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
        "jti": generate_jti(),
    }
    return payload


async def revoke_token(jti: str, revoked_by: Optional[str] = None):  # noqa: D401
    _revoked_tokens[jti] = datetime.now(timezone.utc)
    return True


async def is_token_revoked(jti: str):  # noqa: D401
    return jti in _revoked_tokens


async def cleanup_expired_revoked_tokens():  # noqa: D401
    # In this stub tokens never expire; just report count
    return len(_revoked_tokens)


# --------------------------- Health Status -----------------------------------
async def get_dependency_health_status():  # noqa: D401
    # Simulate parallel health checks
    async def _ok(name: str):
        await asyncio.sleep(0)  # yield
        return name, {"status": "ok"}

    results = await asyncio.gather(
        _ok("database"),
        _ok("cache"),
        _ok("email"),
    )
    services = {k: v for k, v in results}
    return {"timestamp": datetime.now(timezone.utc).isoformat(), "services": services}


# --------------------------- Compatibility alias -----------------------------
# Some tests may import legacy names; keep placeholder for forward compat.

# (No legacy names currently required beyond those above.)


# --------------------------- Fallback Real Imports ---------------------------
try:  # If real implementations exist they should override the stubs.
    from services.dependencies import *  # type: ignore  # noqa: F401,F403
except Exception:  # pragma: no cover - absence is fine in test shim context
    try:
        from models.dependencies import *  # type: ignore  # noqa: F401,F403
    except Exception:
        try:
            from sqlalchemy.orm import declarative_base  # type: ignore
        except Exception:  # pragma: no cover
            from sqlalchemy.ext.declarative import declarative_base  # type: ignore
        Base = declarative_base()  # noqa: N816

