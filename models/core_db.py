# Shim module: re-exports from core.db.session for backward compatibility
# This maintains existing imports while consolidating DB session logic

from core.db.session import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
