# tests/fixtures/db.py
"""Database fixtures for tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.db.session import Base


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest.fixture
def db_tables(db_engine):
    """Create all tables for testing."""
    Base.metadata.create_all(bind=db_engine)
    yield
    Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def db(db_engine, db_tables):
    """
    Provide database session for tests.
    Creates in-memory SQLite with all tables.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()