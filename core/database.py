from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from core.config import settings

engine = create_engine(
    settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from apps.backend.models import Base
    Base.metadata.create_all(bind=engine)