# core/db/session.py
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator, AsyncGenerator
from fastapi import Request
from core.config import settings


# Create Base class - single source of truth
Base = declarative_base()

# Cache database URLs
_database_url = None
_async_database_url = None


def get_database_url(async_mode: bool = False):
    """Get database URL from settings with fallback, cached."""
    global _database_url, _async_database_url
    
    if async_mode and _async_database_url:
        return _async_database_url
    elif not async_mode and _database_url:
        return _database_url
    
    try:
        url = settings.database_url
        if hasattr(url, 'get_secret_value'):
            url = url.get_secret_value()
        else:
            url = str(url) if url else "sqlite:///:memory:"
        
        # Convert to async URL if needed
        if async_mode:
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            elif url.startswith("sqlite://"):
                url = url.replace("sqlite://", "sqlite+aiosqlite://")
            _async_database_url = url
        else:
            _database_url = url
        
        return url
    except:
        fallback = "sqlite+aiosqlite:///:memory:" if async_mode else "sqlite:///:memory:"
        if async_mode:
            _async_database_url = fallback
        else:
            _database_url = fallback
        return fallback


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


async def get_async_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session with request-scoped GUCs.
    This ensures RLS policies use the correct organization context.
    """
    async with async_session_factory() as session:
        # Get organization and RLS settings from request state
        org_id = getattr(request.state, "organization_id", None)
        rls_enabled = getattr(request.state, "rls_enabled", False)
        
        # Set GUCs for this session (not LOCAL, so they persist for the request)
        if org_id:
            await session.execute(
                text("SET app.current_org = :org_id"),
                {"org_id": str(org_id)}
            )
        
        await session.execute(
            text("SET app.rls_enabled = :flag"),
            {"flag": "true" if rls_enabled else "false"}
        )
        
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()