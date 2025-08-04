# config.py

import os
from typing import List

class Settings:
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./goldleaves.db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    
    # Email
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080"
    ]
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Goldleaves Backend"

settings = Settings()
