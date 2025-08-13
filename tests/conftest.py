"""Shared fixtures for async tests (clean)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio


# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def app():
    from routers.main import app as fastapi_app

    return fastapi_app


# mypy: ignore-error-code=misc for untyped fixture decorator from pytest-asyncio
@pytest_asyncio.fixture(scope="session")  # type: ignore[misc]
async def db_init():
    """Create tables for tests using SQLAlchemy metadata (sync + async engines).

    When using SQLite in-memory, the sync and async engines don't share a DB.
    Create the schema on both to keep tests simple.
    """
    from core.db.session import Base, engine, async_engine

    # Import models to ensure they're registered (explicit alias usage)
    import models.organization as _org
    import models.billing_event as _be
    _ = (_org, _be)

    # Create on sync engine
    Base.metadata.create_all(bind=engine)

    # And on async engine
    try:
        from sqlalchemy.ext.asyncio import AsyncEngine

        _ae: AsyncEngine = async_engine  # type: ignore[assignment]
        async with _ae.begin() as conn:  # type: ignore[attr-defined]
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # If async engine isn't SQLite or already has tables, ignore
        pass
    yield
