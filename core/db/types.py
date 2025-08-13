"""Cross-dialect SQLAlchemy types for UUID and JSON/JSONB.

GUID: stores UUIDs using native Postgres UUID, and CHAR(36) on others.
JSONBCompat: uses JSONB on Postgres, JSON on other dialects.
"""
from __future__ import annotations

import uuid as _uuid
from typing import Any, Optional

from sqlalchemy.types import CHAR, TypeDecorator, JSON as _JSON
from sqlalchemy.dialects.postgresql import UUID as _PG_UUID, JSONB as _PG_JSONB


class GUID(TypeDecorator[str]):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise stores as CHAR(36).
    Accepts and returns uuid.UUID instances.
    """

    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:  # type: ignore[override]
        if value is None:
            return None
        if isinstance(value, _uuid.UUID):
            return str(value)
        # accept strings and try to coerce
        try:
            return str(_uuid.UUID(str(value)))
        except Exception:
            return str(value)

    def process_result_value(self, value: Any, dialect) -> Optional[_uuid.UUID]:  # type: ignore[override]
        if value is None:
            return None
        if isinstance(value, _uuid.UUID):
            return value
        try:
            return _uuid.UUID(str(value))
        except Exception:
            return None


class JSONBCompat(TypeDecorator[Any]):
    """Use JSONB on Postgres and JSON elsewhere."""

    impl = _JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PG_JSONB())
        return dialect.type_descriptor(_JSON())
