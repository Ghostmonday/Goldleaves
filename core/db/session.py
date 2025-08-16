"""Unified SQLAlchemy session helpers (sync + async) with optional GUCs.

Provides a single source of truth for Base/engine/session factories.
Async sessions optionally set Postgres GUCs per request to support RLS.
Falls back to in-memory SQLite for tests when no DB URL is configured.
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from ..config import settings

# Create Base class - single source of truth
Base = declarative_base()

# Cached URLs to avoid repeated parsing
_database_url_cache: str | None = None
_async_database_url_cache: str | None = None


def get_database_url(async_mode: bool = False) -> str:
    """Get database URL from settings with fallback, cached, and async mapping."""
    global _database_url_cache, _async_database_url_cache
    if async_mode and _async_database_url_cache:
        return _async_database_url_cache
    if not async_mode and _database_url_cache:
        return _database_url_cache

    try:
        url = settings.database_url
        if hasattr(url, "get_secret_value"):
            url = url.get_secret_value()
        else:
            url = str(url) if url else "sqlite:///:memory:"
        if not url:
            url = "sqlite:///:memory:"
        # Special handling for SQLite in-memory so sync/async share same DB
        if url.startswith("sqlite:///:memory:"):
            if async_mode:
                url = "sqlite+aiosqlite:///file:shared_test?mode=memory&cache=shared&uri=true"
                _async_database_url_cache = url
            else:
                url = "sqlite:///file:shared_test?mode=memory&cache=shared&uri=true"
                _database_url_cache = url
            return url

        if async_mode:
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://")
            elif url.startswith("sqlite://"):
                url = url.replace("sqlite://", "sqlite+aiosqlite://")
            _async_database_url_cache = url
        else:
            _database_url_cache = url
        return url
    except Exception:
        fallback_url = "sqlite+aiosqlite:///:memory:" if async_mode else "sqlite:///:memory:"
        if async_mode:
            _async_database_url_cache = fallback_url
        else:
            _database_url_cache = fallback_url
        return fallback_url


# Sync engine and session for tests/migrations
_sync_url = get_database_url(async_mode=False)
engine_kwargs: Dict[str, Any] = {}
if _sync_url.startswith("sqlite"):
    # Share single connection for in-memory DB across threads/connections
    connect_args = {"check_same_thread": False}
    # Enable URI handling so file:shared_test works as SQLite memory URI
    if _sync_url.startswith("sqlite:///file:"):
        connect_args["uri"] = True
    engine_kwargs.update({"connect_args": connect_args, "poolclass": StaticPool})
engine = create_engine(_sync_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session for application
_async_url = get_database_url(async_mode=True)
async_engine_kwargs: Dict[str, Any] = {"echo": False, "future": True}
if _async_url.startswith("sqlite+"):
    async_engine_kwargs.update({
    "connect_args": {"check_same_thread": False, "uri": True},
        "poolclass": StaticPool,
    })
async_engine = create_async_engine(_async_url, **async_engine_kwargs)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get sync database session (used in tests/migrations)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from starlette.requests import Request


async def get_async_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Async session with optional Postgres GUCs for RLS based on request state."""
    async with async_session_factory() as session:
        # Only attempt GUCs if using Postgres
        try:
            dialect = session.bind.dialect.name  # type: ignore[attr-defined]
        except Exception:
            dialect = ""

        org_id = getattr(getattr(request, "state", object()), "organization_id", None)
        rls_enabled = getattr(getattr(request, "state", object()), "rls_enabled", False)

        if dialect == "postgresql":
            if org_id:
                await session.execute(text("SET app.current_org = :org_id"), {"org_id": str(org_id)})
            await session.execute(
                text("SET app.rls_enabled = :flag"), {"flag": "true" if rls_enabled else "false"}
            )

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
