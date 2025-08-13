from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
import uuid
import jwt

from core.config import settings


class EmailVerificationService:
    @staticmethod
    def generate_verification_token(user_id: int, expires_hours: int = 2) -> Tuple[str, datetime]:
        now = datetime.utcnow()
        exp = now + timedelta(hours=expires_hours)
        payload = {
            "sub": str(user_id),
            "type": "email_verification",
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)
        return token, exp

    @staticmethod
    def decode_verification_token(token: str) -> Dict[str, Any]:
        payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "email_verification":
            raise ValueError("Invalid token type")
        return payload
