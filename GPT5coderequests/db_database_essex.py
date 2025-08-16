# core/db/database.py
"""
Facade re-export to avoid multiple Bases.
Import Base and get_db from here or from core.db.session.
"""
from core.db.session import Base, get_db

__all__ = ["Base", "get_db"]