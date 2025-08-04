# routers/main.py
"""Main FastAPI application with router registration."""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

# Import routers
from .auth import router as auth_router
from ..core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Goldleaves Backend starting up...")
    
    yield
    
    # Shutdown
    print("🛑 Goldleaves Backend shutting down...")


def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    config = config or {}
    
    # Create FastAPI app
    app = FastAPI(
        title="Goldleaves Backend API",
        description="Legal platform backend with Phase 12 form crowdsourcing",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth_router)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Application health check."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "phase": "12_form_crowdsourcing"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if settings.ENVIRONMENT == "development" else "An error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
