# === AGENT CONTEXT: SCHEMAS AGENT ===
# ✅ Phase 4: Complete schema contracts implementation
# ✅ Define all Pydantic schemas with type-safe fields
# ✅ Add pagination, response, and error wrapper patterns
# ✅ Validate alignment with models/ and services/ usage
# ✅ Enforce exports via `schemas/contract.py`
# ✅ Ensure each schema has at least one integration test
# ✅ Maintain strict folder isolation (no model/service imports)
# ✅ Add version string and export mapping to `SchemaContract`
# ✅ Annotate fields with metadata for future auto-docs


"""Pydantic schemas for User operations (registration, login, profile, password reset).

This module contains all Pydantic schema models related to user authentication, 
registration, profile management, and password operations with comprehensive
validation, type safety, and auto-documentation support.
"""

from datetime import datetime
