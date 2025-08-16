"""
Unified configuration for Goldleaves backend.
Single source of truth for all application settings.
"""

from builtins import isinstance, list, property
import os
from functools import lru_cache
from typing import List, Optional, Union, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8"
    )

    # Application
    PROJECT_NAME: str = Field(default="Goldleaves")
    VERSION: str = Field(default="1.0.0")
    DESCRIPTION: str = Field(default="Document Management System")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # API Configuration
    API_V1_STR: str = Field(default="/api/v1")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=1)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/goldleaves"
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_ECHO: bool = Field(default=False)

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(default=24)
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(default=2)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Email
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=587)
    SMTP_TLS: bool = Field(default=True)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    FROM_EMAIL: str = Field(default="noreply@goldleaves.com")
    FROM_NAME: str = Field(default="Goldleaves")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=1000)

    # File Storage
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_UPLOAD_SIZE_MB: int = Field(default=100)
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".doc", ".docx", ".txt", ".jpg", ".png"]
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Redis (Optional)
    REDIS_URL: Optional[str] = Field(default=None)

    # Sentry (Optional)
    SENTRY_DSN: Optional[str] = Field(default=None)

    # Webhook Configuration
    WEBHOOK_SECRET: str = Field(default="goldleaves-webhook-secret")
    WEBHOOK_TIMEOUT: int = Field(default=30)
    WEBHOOK_MAX_RETRIES: int = Field(default=3)
    WEBHOOK_ENABLED: bool = Field(default=True)

    # Admin Configuration
    ADMIN_EMAILS: List[str] = Field(
        default=["admin@goldleaves.com"]
    )

    # Frontend URL
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    # Feature Flags
    ENABLE_REGISTRATION: bool = Field(default=True)
    ENABLE_EMAIL_VERIFICATION: bool = Field(default=True)
    ENABLE_2FA: bool = Field(default=False)
    ENABLE_API_KEYS: bool = Field(default=True)

    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
