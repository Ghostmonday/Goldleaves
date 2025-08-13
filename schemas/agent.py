# === AGENT CONTEXT: SCHEMAS AGENT ===
# 🚧 TODOs for Phase 4 — Complete schema contracts
# - [x] Define all Pydantic schemas with type-safe fields
# - [x] Add pagination, response, and error wrapper patterns
# - [x] Validate alignment with models/ and services/ usage
# - [x] Enforce exports via `schemas/contract.py`
# - [x] Ensure each schema has at least one integration test
# - [x] Maintain strict folder isolation (no model/service imports)
# - [x] Add version string and export mapping to `SchemaContract`
# - [x] Annotate fields with metadata for future auto-docs

"""
Schemas Agent Entry - Complete implementation.
Agent interface for schema validation and processing.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .core_contracts import SchemaContract


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETE = "complete"


class AgentRequest(BaseModel):
    """Agent processing request schema."""

    task_id: str = Field(
        title="Task ID", description="Unique task identifier"
    )

    schema_name: str = Field(
        title="Schema Name", description="Target schema name"
    )

    data: Dict[str, Any] = Field(
        title="Data", description="Data to process"
    )

    options: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Options", description="Processing options"
    )


class AgentResponse(BaseModel):
    """Agent processing response schema."""

    task_id: str = Field(
        title="Task ID", description="Task identifier"
    )

    status: AgentStatus = Field(
        title="Status", description="Processing status"
    )

    result: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Result", description="Processing result"
    )

    errors: Optional[List[str]] = Field(
        default=None,
        title="Errors", description="Processing errors"
    )


class AgentInfo(BaseModel):
    """Agent information schema."""

    agent_id: str = Field(
        default="schemas-agent-v4",
        title="Agent ID", description="Agent identifier"
    )

    version: str = Field(
        default="4.0.0",
        title="Version", description="Agent version"
    )

    contract: SchemaContract = Field(
        default_factory=SchemaContract,
        title="Contract", description="Schema contract"
    )

    capabilities: List[str] = Field(
        default_factory=lambda: [
            "schema_validation",
            "data_processing",
            "contract_enforcement",
            "type_checking"
        ],
        title="Capabilities", description="Agent capabilities"
    )
