# routers/__init__.py

"""Phase 6: Router package initialization with collaboration features."""

# Import router contracts to register them
from . import auth
# from . import agent  # Comment out temporarily due to import issues
# from . import document_collaboration_contract  # Comment out temporarily
from . import billing

# Import core contract utilities
from .contract import (
    RouterContract,
    RouterTags,
    HTTPStatus,
    ErrorResponseSchema,
    SuccessResponseSchema,
    register_router,
    get_all_routers,
    get_router_contract,
    ROUTER_REGISTRY
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
