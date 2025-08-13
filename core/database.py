"""Database facade that re-exports the canonical SQLAlchemy Base/session.

To avoid duplicate metadata, import Base and get_db from core.db.session.
This ensures models declared anywhere in the codebase share one metadata
and one engine/session setup.
"""

from __future__ import annotations

# Re-export the single source of truth for ORM base and DB access
from core.db.session import Base, get_db  # noqa: F401


