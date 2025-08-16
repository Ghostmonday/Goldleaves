"""
Email verification service for user account verification.
Handles token generation, validation, and email simulation.
"""

import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from core.config import settings
from apps.backend.models import User

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Service for handling email verification tokens and workflow."""

    @staticmethod
    def generate_verification_token(user_id: int) -> Tuple[str, datetime]:
        """
        Generate a JWT verification token for email verification.

        Args:
            user_id: The user's database ID

        Returns:
            Tuple of (token_string, expires_at_datetime)
        """
        expire = datetime.utcnow() + timedelta(hours=settings.verification_token_expire_hours)

        # Create a secure random token ID for additional security
        token_id = secrets.token_urlsafe(16)

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "email_verification",
            "jti": token_id  # JWT ID for token uniqueness
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm
        )

        return token, expire

    @staticmethod
    def decode_verification_token(token: str) -> dict:
        """
        Decode and validate a verification token.

        Args:
            token: The JWT token string

        Returns:
            Decoded token payload

        Raises:
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidTokenError: If token is invalid
            ValueError: If token type is incorrect
        """
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )

        # Validate token type
        if payload.get("type") != "email_verification":
            raise ValueError("Invalid token type")

        return payload

    @staticmethod
    def send_verification_email(db: Session, email: str) -> dict:
        """
        Generate and send verification email to user.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Result dictionary with success status and message

        Raises:
            ValueError: If user not found or already verified
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Verification email requested for non-existent email: {email}")
            raise ValueError("User not found")

        if user.is_verified:
            logger.info(f"Verification email requested for already verified user: {email}")
            raise ValueError("User already verified")

        # Generate new verification token
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)

        # Update user with new token
        user.verification_token = token
        user.token_expires_at = expires_at
        db.commit()

        # Simulate sending email (in production, integrate with email service)
        logger.info(f"📧 EMAIL SIMULATION - Verification email sent to {email}")
        logger.info(f"🔑 Verification token: {token}")
        logger.info(f"⏰ Token expires at: {expires_at}")

        return {
            "success": True,
            "message": "Verification email sent successfully",
            "expires_at": expires_at,
            # In development, include token for testing
            "token": token if settings.is_development else None
        }

    @staticmethod
    def confirm_email_verification(db: Session, token: str) -> dict:
        """
        Confirm email verification using token.

        Args:
            db: Database session
            token: Verification token

        Returns:
            Result dictionary with success status and message

        Raises:
            ValueError: If token is invalid or user not found
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidTokenError: If token is malformed
        """
        try:
            # Decode and validate token
            payload = EmailVerificationService.decode_verification_token(token)
            user_id = int(payload.get("sub"))

        except jwt.ExpiredSignatureError:
            logger.warning("Expired verification token used")
            raise ValueError("Verification token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid verification token: {str(e)}")
            raise ValueError("Invalid verification token")
        except (ValueError, TypeError):
            logger.warning("Invalid user ID in verification token")
            raise ValueError("Invalid verification token")

        # Find user and validate token
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Verification attempted for non-existent user ID: {user_id}")
            raise ValueError("User not found")

        # Check if token matches the one stored in database
        if user.verification_token != token:
            logger.warning(f"Token mismatch for user {user_id}")
            raise ValueError("Invalid or revoked verification token")

        # Check if token is expired (double-check against database)
        if user.token_expires_at and user.token_expires_at < datetime.utcnow():
            logger.warning(f"Expired verification token for user {user_id}")
            raise ValueError("Verification token has expired")

        # Check if already verified
        if user.is_verified:
            logger.info(f"User {user_id} attempted to verify already verified email")
            return {
                "success": True,
                "message": "Email already verified",
                "user_id": user.id
            }

        # Mark user as verified and clear verification fields
        user.is_verified = True
        user.verification_token = None
        user.token_expires_at = None
        db.commit()

        logger.info(f"✅ Email verified successfully for user {user_id} ({user.email})")

        return {
            "success": True,
            "message": "Email verified successfully",
            "user_id": user.id
        }

    @staticmethod
    def resend_verification_email(db: Session, email: str) -> dict:
        """
        Resend verification email if user is not verified.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Result dictionary with success status and message
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Resend verification requested for non-existent email: {email}")
            raise ValueError("User not found")

        if user.is_verified:
            logger.info(f"Resend verification requested for already verified user: {email}")
            raise ValueError("User already verified")

        # Generate new verification token (overwrites any existing token)
        token, expires_at = EmailVerificationService.generate_verification_token(user.id)

        # Update user with new token
        user.verification_token = token
        user.token_expires_at = expires_at
        db.commit()

        # Simulate sending email
        logger.info(f"📧 EMAIL SIMULATION - Verification email resent to {email}")
        logger.info(f"🔑 New verification token: {token}")
        logger.info(f"⏰ Token expires at: {expires_at}")

        return {
            "success": True,
            "message": "Verification email resent successfully",
            "expires_at": expires_at,
            # In development, include token for testing
            "token": token if settings.is_development else None
        }
