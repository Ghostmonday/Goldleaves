"""Organization model for FK relationship and UUID usage (cross-dialect)."""
from __future__ import annotations

import uuid
from sqlalchemy import Column, String, text
from sqlalchemy.types import TIMESTAMP
from typing import Any
from datetime import datetime

from core.db.session import Base
from core.db.types import GUID, JSONBCompat


class Organization(Base):
    __tablename__ = "organizations"

    # Use GUID for cross-dialect UUID; avoid PG-only server_default for SQLite tests
    id: Column[GUID] = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Column[str] = Column(String(255), nullable=False)
    slug: Column[str] = Column(String(255), unique=True, index=True)
    plan: Column[str] = Column(String(50), default="starter")
    settings: Column[Any] = Column(JSONBCompat, default=dict)
    created_at: Column[datetime] = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Column[datetime] = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Organization id={self.id} name={self.name}>"
