# core/config.py
"""Minimal settings used by Alembic and tests."""
import os
from typing import Any, Optional
from pydantic import BaseSettings, Field, SecretStr


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: Optional[Any] = Field(
        default=os.getenv("DATABASE_URL", "sqlite:///:memory:"),
        description="Database connection URL"
    )
    
    # JWT settings
    jwt_secret: str = Field(
        default=os.getenv("JWT_SECRET", "your-secret-key-change-in-production"),
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    jwt_expiration_minutes: int = Field(
        default=30,
        description="JWT token expiration in minutes"
    )
    
    # Redis
    redis_url: Optional[str] = Field(
        default=os.getenv("REDIS_URL"),
        description="Redis connection URL"
    )
    
    # Celery
    celery_broker_url: Optional[str] = Field(
        default=os.getenv("CELERY_BROKER_URL"),
        description="Celery broker URL"
    )
    
    # S3
    s3_bucket: Optional[str] = Field(
        default=os.getenv("S3_BUCKET"),
        description="S3 bucket name"
    )
    s3_region: Optional[str] = Field(
        default=os.getenv("S3_REGION", "us-east-1"),
        description="S3 region"
    )
    
    # Feature flags
    rls_enabled: bool = Field(
        default=os.getenv("RLS_ENABLED", "false").lower() == "true",
        description="Row-level security enabled"
    )
    tenant_isolation_mode: str = Field(
        default=os.getenv("TENANT_ISOLATION_MODE", "row"),
        description="Tenant isolation mode"
    )
    
    # Rate limits
    tier_rate_limits: Optional[str] = Field(
        default=os.getenv("TIER_RATE_LIMITS"),
        description="JSON string of tier rate limits"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_database_url(self) -> str:
        """Get database URL, handling secret wrapper."""
        if hasattr(self.database_url, 'get_secret_value'):
            return self.database_url.get_secret_value()
        return str(self.database_url) if self.database_url else "sqlite:///:memory:"


# Create settings instance
settings = Settings()