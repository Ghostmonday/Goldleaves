# conftest.py
"""Shared fixtures for tests."""
import sys
import os
import pytest
import pytest_asyncio
from pathlib import Path

# Ensure PYTHONPATH is set
root_dir = Path(__file__).parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import FastAPI app
from routers.main import app as fastapi_app


@pytest.fixture
def app():
    """Fixture that returns the FastAPI app."""
    return fastapi_app


@pytest_asyncio.fixture(scope="session")
async def db_init():
    """Session-scoped database initialization."""
    from core.db.session import Base, engine, async_engine
    from sqlalchemy.ext.asyncio import AsyncConnection
    
    # For tests, use create_all instead of migrations
    # This ensures tables exist before tests run
    
    # Create tables using sync engine for compatibility
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Optionally drop tables after all tests (usually not needed for in-memory DBs)
    # Base.metadata.drop_all(bind=engine)