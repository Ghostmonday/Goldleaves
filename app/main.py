"""
Main FastAPI application entry point.
Properly configured with all middleware, routers, and exception handlers.
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from core.database import init_db, check_db_health
from core.logging import setup_logging
from middleware.request_id import RequestIDMiddleware
from middleware.rate_limit import RateLimitMiddleware
from middleware.security import SecurityHeadersMiddleware
from api.v1 import router as api_v1_router
from monitoring import metrics, CONTENT_TYPE_LATEST


# Set up logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Check database health
    if check_db_health():
        logger.info("Database health check passed")
    else:
        logger.error("Database health check failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if not settings.is_production else None,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan
    )
    
    # Set up middleware
    setup_middleware(app)
    
    # Set up routes
    setup_routes(app)
    
    # Set up exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    # Add CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
        )
    
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add request ID middleware
    app.add_middleware(RequestIDMiddleware)
    
    # Add rate limiting (if enabled)
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
            requests_per_hour=settings.RATE_LIMIT_REQUESTS_PER_HOUR
        )
    
    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add trusted host middleware in production
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.goldleaves.com", "goldleaves.com"]
        )


def setup_routes(app: FastAPI) -> None:
    """Configure application routes."""
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        db_healthy = check_db_health()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    # Metrics endpoint for Prometheus
    @app.get("/metrics")
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return Response(
            content=metrics.get_prometheus_metrics(), 
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs_url": "/docs" if not settings.is_production else None
        }
    
    # Include API routers
    app.include_router(api_v1_router)


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure application exception handlers."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "request_id": getattr(request.state, "request_id", "N/A")
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", "N/A")
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error" if settings.is_production else str(exc),
                "request_id": getattr(request.state, "request_id", "N/A")
            }
        )


# Create the application instance
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        workers=settings.WORKERS if not settings.is_development else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
