# === AGENT CONTEXT: MODELS AGENT ===
# ✅ Phase 4 TODOs — COMPLETED
# ✅ Implement SQLAlchemy base model definitions
# ✅ Define core ORM relationships for all entities
# ✅ Validate enum alignment with schemas (OrganizationPlan, APIKeyScope, etc.)
# ✅ Add __table_args__ for composite indexes
# ✅ Enforce contract keys defined in `models/contract.py`
# ✅ Ensure no external schema imports — strict folder isolation
# ✅ Include timestamp and soft delete mixins in all base models
# ✅ Implement test stubs for each model in tests/

"""Dependencies for models agent - isolated workspace."""

from sqlalchemy import CheckConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Generator

# Local configuration
class Config:
    """Database and core configuration for models."""
    DATABASE_URL: str = "postgresql://user:password@localhost/goldleaves"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

# Global settings
settings = Config()

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Common model utilities
def utcnow():
    """Get current UTC timestamp."""
    return datetime.utcnow()

# Common constraints and validators for models
def create_password_constraint():
    """Create password length constraint."""
    return CheckConstraint("length(hashed_password) >= 60", name="check_password_length")

def create_email_constraint():
    """Create email format constraint."""
    return CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name="check_email_format")
