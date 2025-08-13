# conftest.py
"""Shared fixtures for tests."""
import sys
import os
import pytest
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


@pytest.fixture(scope="session")
def db_init():
    """Session-scoped database initialization if needed."""
    from core.db.session import Base, engine
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Optionally drop tables after all tests
    # Base.metadata.drop_all(bind=engine)