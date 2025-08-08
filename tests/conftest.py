import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from apps.backend.main import app
from core.database import get_db
from apps.backend.models import Base, User, RefreshToken
from apps.backend.services.auth_service import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    """FastAPI test client with fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Database session for direct database operations in tests."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }

@pytest.fixture
def sample_user_data_2():
    """Second sample user data for testing conflicts."""
    return {
        "username": "testuser2",
        "email": "test2@example.com", 
        "password": "AnotherSecurePassword456!"
    }

@pytest.fixture
def created_user(db_session: Session):
    """Create a test user in the database."""
    user = User(
        username="existinguser",
        email="existing@example.com",
        hashed_password=hash_password("ExistingPassword789!"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def unverified_user(db_session: Session):
    """Create an unverified test user in the database."""
    user = User(
        username="unverifieduser",
        email="unverified@example.com",
        hashed_password=hash_password("UnverifiedPassword123!"),
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def inactive_user(db_session: Session):
    """Create an inactive test user in the database."""
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password=hash_password("InactivePassword123!"),
        is_active=False,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user