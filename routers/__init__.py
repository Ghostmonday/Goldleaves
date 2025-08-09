# routers/__init__.py

"""Phase 6: Router package initialization with collaboration features."""

# Import router contracts to register them
from . import agent, auth, document_collaboration_contract

# Import core contract utilities
from .contract import (
    ROUTER_REGISTRY,
    ErrorResponseSchema,
    HTTPStatus,
    RouterContract,
    RouterTags,
    SuccessResponseSchema,
    get_all_routers,
    get_router_contract,
    register_router,
)

__all__ = [
    "RouterContract",
    "RouterTags", 
    "HTTPStatus",
    "ErrorResponseSchema",
    "SuccessResponseSchema",
    "register_router",
    "get_all_routers",
    "get_router_contract",
    "ROUTER_REGISTRY"
]
