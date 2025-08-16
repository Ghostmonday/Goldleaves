# core/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from core.config import settings


# Create Base class - single source of truth
Base = declarative_base()

# Get database URL
def get_database_url():
    """Get database URL from settings with fallback."""
    try:
        url = settings.database_url
        if hasattr(url, 'get_secret_value'):
            return url.get_secret_value()
        return str(url) if url else "sqlite:///:memory:"
    except:
        return "sqlite:///:memory:"


# Create engine
engine = create_engine(
    get_database_url(),
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()