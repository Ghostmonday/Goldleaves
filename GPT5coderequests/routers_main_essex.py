# routers/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.stack import tenant_resolver_middleware
from middleware.usage import usage_logger_middleware


def create_development_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="Backend API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register middlewares in order: tenant before usage
    @app.middleware("http")
    async def usage_middleware(request, call_next):
        return await usage_logger_middleware(request, call_next)
    
    @app.middleware("http")
    async def tenant_middleware(request, call_next):
        return await tenant_resolver_middleware(request, call_next)
    
    # Include existing routers if available
    try:
        from routers.usage import router as usage_router
        app.include_router(usage_router, prefix="/usage", tags=["usage"])
    except ImportError:
        pass
    
    try:
        from routers.billing import router as billing_router
        app.include_router(billing_router, prefix="/billing", tags=["billing"])
    except ImportError:
        pass
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "Backend API"}
    
    return app


# Expose app instance
app = create_development_app()