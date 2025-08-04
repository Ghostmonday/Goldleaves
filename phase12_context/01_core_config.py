"""Core configuration settings for all agents."""

from __future__ import annotations
from typing import Any
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "Goldleaves"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/goldleaves"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    # Environment
    ENVIRONMENT: str = "development"

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@goldleaves.com"

    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance for import
settings = get_settings()
