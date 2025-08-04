"""
Unified database configuration and session management.
Provides both sync and async database support.
"""

import os
from typing import Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings


# Database naming conventions
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

# Base class for all models
Base = declarative_base(metadata=metadata)

# Synchronous database setup
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Asynchronous database setup
async_engine = create_async_engine(
    settings.database_url_async,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency to get database session.
    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database session.
    Usage:
        async with get_async_db_context() as db:
            result = await db.execute(select(User))
            user = result.scalar_one()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db() -> None:
    """Initialize database tables."""
    # Import all models to ensure they're registered with Base
    try:
        from models import user, organization, document, audit  # noqa
    except ImportError:
        # Models will be imported when they exist
        pass
    
    Base.metadata.create_all(bind=engine)


async def init_async_db() -> None:
    """Initialize database tables asynchronously."""
    # Import all models to ensure they're registered with Base
    try:
        from models import user, organization, document, audit  # noqa
    except ImportError:
        # Models will be imported when they exist
        pass
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)


async def drop_async_db() -> None:
    """Drop all database tables asynchronously. Use with caution!"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Health check functions
def check_db_health() -> bool:
    """Check if database is accessible."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


async def check_async_db_health() -> bool:
    """Check if database is accessible asynchronously."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


# Event listeners for debugging (only in development)
if settings.is_development:
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        """Log database connections in development."""
        connection_record.info['pid'] = os.getpid()
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkouts in development."""
        pid = os.getpid()
        if connection_record.info['pid'] != pid:
            connection_record.connection = connection_proxy.connection = None
            from sqlalchemy import exc
            raise exc.DisconnectionError(
                "Connection record belongs to pid %s, attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
            )
