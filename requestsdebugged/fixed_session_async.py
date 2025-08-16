# core/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
from core.config import settings


# Create Base class - single source of truth
Base = declarative_base()

# Get database URL
def get_database_url(async_mode: bool = False):
    """Get database URL from settings with fallback."""
    try:
        url = settings.database_url
        if hasattr(url, 'get_secret_value'):
            url = url.get_secret_value()
        else:
            url = str(url) if url else "sqlite:///:memory:"
        
        # Convert to async URL if needed
        if async_mode and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif async_mode and url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://")
        
        return url
    except:
        return "sqlite+aiosqlite:///:memory:" if async_mode else "sqlite:///:memory:"


# Sync engine and session for tests/migrations
engine = create_engine(
    get_database_url(async_mode=False),
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url(async_mode=False) else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session for application
async_engine = create_async_engine(
    get_database_url(async_mode=True),
    echo=False,
    future=True
)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get sync database session.
    Used for tests and migrations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    Used for application endpoints.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()