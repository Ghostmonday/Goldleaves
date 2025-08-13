# routers/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.stack import (
    correlation_id_middleware,
    request_timer_middleware, 
    tenant_resolver_middleware
)
from middleware.usage import usage_logger_middleware


def create_development_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(title="Backend API", version="1.0.0")
    
    # Add CORS middleware (tighten for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Tighten for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register middlewares in CORRECT order (reverse order due to middleware stack)
    # Order of execution: correlation → timer → auth → tenant → usage
    
    # 5. Usage logger (outermost in registration, last to execute)
    @app.middleware("http")
    async def usage_middleware(request, call_next):
        return await usage_logger_middleware(request, call_next)
    
    # 4. Tenant resolver
    @app.middleware("http")
    async def tenant_middleware(request, call_next):
        return await tenant_resolver_middleware(request, call_next)
    
    # 3. Auth middleware (add your auth middleware here)
    # @app.middleware("http")
    # async def auth_middleware(request, call_next):
    #     return await auth_dependencies_middleware(request, call_next)
    
    # 2. Request timer
    @app.middleware("http")
    async def timer_middleware(request, call_next):
        return await request_timer_middleware(request, call_next)
    
    # 1. Correlation ID (innermost in registration, first to execute)
    @app.middleware("http")
    async def correlation_middleware(request, call_next):
        return await correlation_id_middleware(request, call_next)
    
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
        return {"message": "Backend API", "version": "1.0.0"}
    
    return app


# Expose app instance
app = create_development_app()