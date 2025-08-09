# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Main application with contract-based architecture

"""Main FastAPI application demonstrating the Phase 4 contract-based router architecture."""

from __future__ import annotations
import uvicorn
from typing import Dict, Any
from builtins import len, list, print, getattr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from contextlib import asynccontextmanager
from datetime import datetime

from .contract import get_all_routers, ROUTER_REGISTRY, RouterTags, ErrorResponseSchema
from .middleware import get_middleware_stack, MIDDLEWARE_REGISTRY
from .schemas import HealthCheckSchema
from .services import SystemService
from .health import router as health_router
from core.telemetry import setup_telemetry

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Goldleaves Backend starting up...")
    print(f"📦 Loaded {len(ROUTER_REGISTRY)} routers")
    print(f"🔧 Available middleware: {list(MIDDLEWARE_REGISTRY.keys())}")
    
    yield
    
    # Shutdown
    print("🛑 Goldleaves Backend shutting down...")

def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    config = config or {}
    
    # Create FastAPI app
    app = FastAPI(
        title="Goldleaves Backend API",
        description="Phase 4: Contract-based router architecture with isolated dependencies",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add custom middleware stack
    middleware_config = config.get("middleware", {})
    
    # Add middleware directly instead of using the middleware stack for now
    # This avoids the double app parameter issue
    from .middleware import (
        RequestContextMiddleware, RateLimitMiddleware, SecurityMiddleware,
        AuditMiddleware, OrganizationContextMiddleware, AuthenticationMiddleware
    )
    
    # Add middleware in reverse order (FastAPI adds them as a stack)
    if middleware_config.get("audit", {}).get("enabled", True):
        app.add_middleware(AuditMiddleware)
    
    if middleware_config.get("organization", {}).get("enabled", True):
        app.add_middleware(OrganizationContextMiddleware)
    
    if middleware_config.get("authentication", {}).get("enabled", True):
        auth_config = middleware_config.get("authentication", {})
        public_paths = auth_config.get("public_paths", ["/__health__", "/__version__", "/health", "/metrics", "/metrics/prometheus", "/docs", "/openapi.json", "/auth/login", "/auth/register"])
        app.add_middleware(AuthenticationMiddleware, public_paths=public_paths)
    
    if middleware_config.get("rate_limit", {}).get("enabled", True):
        rate_config = middleware_config.get("rate_limit", {})
        limiter_name = rate_config.get("limiter_name", "api")
        app.add_middleware(RateLimitMiddleware, limiter_name=limiter_name)
    
    if middleware_config.get("security", {}).get("enabled", True):
        app.add_middleware(SecurityMiddleware)
    
    app.add_middleware(RequestContextMiddleware)
    
    # Setup telemetry (Sentry and OpenTelemetry)
    telemetry_status = setup_telemetry(app, "goldleaves-api")
    print(f"📊 Telemetry status: {telemetry_status}")
    
    # Add health router first (includes /__health__, /__version__, /metrics)
    app.include_router(health_router, tags=[RouterTags.HEALTH])
    
    # Add routers
    routers = get_all_routers()
    for router_contract in ROUTER_REGISTRY.values():
        app.include_router(
            router_contract.router,
            prefix=router_contract.prefix,
            tags=router_contract.tags
        )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        return JSONResponse(
            status_code=500,
            content=ErrorResponseSchema(
                detail="Internal server error",
                error_code="INTERNAL_ERROR",
                timestamp=datetime.utcnow().isoformat(),
                request_id=getattr(request.state, "request_id", "unknown")
            ).dict()
        )
    
    return app

def create_development_app() -> FastAPI:
    """Create app with development configuration."""
    config = {
        "cors": {
            "origins": ["http://localhost:3000", "http://localhost:8080"]
        },
        "middleware": {
            "rate_limit": {"enabled": True, "limiter_name": "api"},
            "security": {"enabled": True},
            "audit": {"enabled": True},
            "authentication": {
                "enabled": True,
                "public_paths": ["/__health__", "/__version__", "/metrics", "/metrics/prometheus", "/health", "/stats", "/docs", "/openapi.json", "/auth/login", "/auth/register"]
            },
            "organization": {"enabled": True},
            "cors": {"enabled": True}
        }
    }
    
    return create_app(config)

def create_production_app() -> FastAPI:
    """Create app with production configuration."""
    config = {
        "cors": {
            "origins": ["https://app.goldleaves.com", "https://admin.goldleaves.com"]
        },
        "middleware": {
            "rate_limit": {"enabled": True, "limiter_name": "api"},
            "security": {"enabled": True},
            "audit": {"enabled": True},
            "authentication": {
                "enabled": True,
                "public_paths": ["/health", "/stats", "/metrics", "/metrics/prometheus"]
            },
            "organization": {"enabled": True},
            "cors": {
                "enabled": True,
                "allow_origins": ["https://app.goldleaves.com", "https://admin.goldleaves.com"],
                "allow_credentials": True
            }
        }
    }
    
    return create_app(config)

# Create default app instance
app = create_development_app()

if __name__ == "__main__":
    # Run development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
