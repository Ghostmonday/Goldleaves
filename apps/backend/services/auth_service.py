"""Minimal auth service for tests: hashing, JWT create/decode, password verify."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

import jwt

from core.config import settings


def hash_password(password: str) -> str:
    # simple, test-only hash (not secure)
    salt = b"testsalt"
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 10000).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    exp_minutes = expires_minutes or getattr(settings, "jwt_expiration_minutes", 30)
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=exp_minutes)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm])


def create_refresh_token(user_id: int, days: int = 30) -> Tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=days)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
    # Return naive UTC datetime for tests comparing with datetime.utcnow()
    return token, datetime.utcfromtimestamp(int(exp.timestamp()))
