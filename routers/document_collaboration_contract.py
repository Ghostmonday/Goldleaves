# routers/document_collaboration_contract.py

"""Phase 6: Document collaboration router contract and registration."""

from typing import List

from fastapi import APIRouter

from . import document_collaboration
from .contract import RouterContract, RouterTags, register_router


class DocumentCollaborationRouterContract(RouterContract):
    """Router contract for document collaboration features."""
    
    def __init__(self):
        self._router = document_collaboration.router
        self.configure_routes()
    
    @property
    def router(self) -> APIRouter:
        """FastAPI router instance."""
        return self._router
    
    @property
    def prefix(self) -> str:
        """URL prefix for this router."""
        return "/api/v1"
    
    @property
    def tags(self) -> List[str]:
        """OpenAPI tags for this router."""
        return [RouterTags.DOCUMENTS, RouterTags.COLLABORATION]
    
    def configure_routes(self) -> None:
        """Configure all routes for this router."""
        # Routes are already configured in the document_collaboration module
        # This method ensures the contract interface is satisfied
        pass


# Register the router contract
register_router("document_collaboration", DocumentCollaborationRouterContract())
