# token_service.py

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt

# ✅ Phase 3: Email verification token generation and validation - COMPLETED

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_VERIFICATION_EXPIRE_HOURS = 24

class TokenService:

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str):
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    # ✅ Phase 3: Email verification token methods - COMPLETED
    @staticmethod
    def create_verification_token(email: str) -> str:
        """
        Create email verification token.
        ✅ Implemented secure token generation for email verification.
        Includes email, expiration time, and secure random component.
        """
        data = {
            "email": email,
            "type": "email_verification",
            "random": secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
        }
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_verification_token(token: str) -> Optional[str]:
        """
        Verify email verification token and return email if valid.
        ✅ Implemented token validation logic for email verification.
        Checks expiration, type, and returns the email address.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "email_verification":
                return None
            return payload.get("email")
        except jwt.PyJWTError:
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if token is expired."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.PyJWTError:
            return True

    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token."""
        data = {
            "email": email,
            "type": "password_reset",
            "random": secrets.token_urlsafe(16),
            "exp": datetime.utcnow() + timedelta(hours=2)  # 2 hour expiry for password reset
        }
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """Verify password reset token and return email if valid."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "password_reset":
                return None
            return payload.get("email")
        except jwt.PyJWTError:
            return None

# ✅ Phase 3: All token service TODOs completed
