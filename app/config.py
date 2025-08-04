"""
Unified configuration for Goldleaves backend.
Single source of truth for all application settings.
"""

import os
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    PROJECT_NAME: str = Field("Goldleaves", env="PROJECT_NAME")
    VERSION: str = Field("1.0.0", env="APP_VERSION")
    DESCRIPTION: str = Field("Document Management System", env="APP_DESCRIPTION")
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # API Configuration
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")
    
    # Server
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    WORKERS: int = Field(1, env="WORKERS")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        "postgresql://user:password@localhost/goldleaves",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(False, env="DATABASE_ECHO")
    
    # Security
    SECRET_KEY: str = Field(
        "your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = Field(24, env="EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS")
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = Field(2, env="PASSWORD_RESET_TOKEN_EXPIRE_HOURS")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8080"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Email
    SMTP_HOST: str = Field("localhost", env="SMTP_HOST")
    SMTP_PORT: int = Field(587, env="SMTP_PORT")
    SMTP_TLS: bool = Field(True, env="SMTP_TLS")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    FROM_EMAIL: str = Field("noreply@goldleaves.com", env="FROM_EMAIL")
    FROM_NAME: str = Field("Goldleaves", env="FROM_NAME")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(1000, env="RATE_LIMIT_REQUESTS_PER_HOUR")
    
    # File Storage
    UPLOAD_DIR: str = Field("./uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE_MB: int = Field(100, env="MAX_UPLOAD_SIZE_MB")
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        [".pdf", ".doc", ".docx", ".txt", ".jpg", ".png"],
        env="ALLOWED_UPLOAD_EXTENSIONS"
    )
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Redis (Optional)
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    # Sentry (Optional)
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    
    # Webhook Configuration
    WEBHOOK_SECRET: str = Field("goldleaves-webhook-secret", env="WEBHOOK_SECRET")
    WEBHOOK_TIMEOUT: int = Field(30, env="WEBHOOK_TIMEOUT")
    WEBHOOK_MAX_RETRIES: int = Field(3, env="WEBHOOK_MAX_RETRIES")
    WEBHOOK_ENABLED: bool = Field(True, env="WEBHOOK_ENABLED")
    
    # Admin Configuration
    ADMIN_EMAILS: List[str] = Field(
        ["admin@goldleaves.com"],
        env="ADMIN_EMAILS"
    )
    
    # Frontend URL
    FRONTEND_URL: str = Field("http://localhost:3000", env="FRONTEND_URL")
    
    # Feature Flags
    ENABLE_REGISTRATION: bool = Field(True, env="ENABLE_REGISTRATION")
    ENABLE_EMAIL_VERIFICATION: bool = Field(True, env="ENABLE_EMAIL_VERIFICATION")
    ENABLE_2FA: bool = Field(False, env="ENABLE_2FA")
    ENABLE_API_KEYS: bool = Field(True, env="ENABLE_API_KEYS")
    
    class Config:
        case_sensitive = True
        env_file_encoding = "utf-8"
    
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
