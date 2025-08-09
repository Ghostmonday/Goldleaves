"""Health and monitoring endpoints.

This module provides health, version, and metrics endpoints for monitoring
and observability of the Goldleaves API application.
"""

import os
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    uptime: str
    version: str
    environment: str


class VersionResponse(BaseModel):
    """Version information response model."""

    version: str
    git_sha: str
    build_time: str
    environment: str


def _get_git_sha() -> str:
    """Get the Git SHA from environment or default."""
    return os.getenv("GIT_SHA", "unknown")


def _get_version() -> str:
    """Get the application version from environment or default."""
    return os.getenv("VERSION", "1.0.0")


def _get_environment() -> str:
    """Get the environment from environment variables."""
    return os.getenv("ENVIRONMENT", "development")


def _get_uptime() -> str:
    """Get application uptime (simplified version)."""
    # This is a simple implementation. In a real application,
    # you might want to track actual startup time.
    return "unknown"


@router.get(
    "/__health__",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Get application health status",
)
async def health_check() -> HealthResponse:
    """Application health check endpoint.

    Returns basic health information including status, timestamp,
    version, and environment details.
    """
    try:
        return HealthResponse(
            status="ok",
            timestamp=datetime.utcnow().isoformat(),
            uptime=_get_uptime(),
            version=_get_version(),
            environment=_get_environment(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed",
        )


@router.get(
    "/__version__",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Version information",
    description="Get application version and build information",
)
async def version_info() -> VersionResponse:
    """Application version information endpoint.

    Returns version, Git SHA, build time, and environment information.
    """
    try:
        return VersionResponse(
            version=_get_version(),
            git_sha=_get_git_sha(),
            build_time=os.getenv("BUILD_TIME", "unknown"),
            environment=_get_environment(),
        )
    except Exception as e:
        logger.error(f"Version info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version information",
        )


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Application metrics",
    description="Get application metrics (requires METRICS_ENABLED=true)",
)
async def get_metrics() -> JSONResponse:
    """Application metrics endpoint.

    Returns application metrics in JSON format. This endpoint is gated
    by the METRICS_ENABLED environment variable.
    """
    metrics_enabled = os.getenv("METRICS_ENABLED", "false").lower() == "true"

    if not metrics_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metrics endpoint is disabled"
        )

    try:
        # Basic metrics - in a real application, you might integrate
        # with a metrics collection system like Prometheus
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": "goldleaves-api",
                "version": _get_version(),
                "environment": _get_environment(),
                "uptime": _get_uptime(),
            },
            "system": {
                "status": "healthy",
                # Add more system metrics as needed
            },
            "custom": {
                # Add custom application metrics here
                "requests_total": 0,  # This would be tracked by actual metrics
                "errors_total": 0,
            },
        }

        return JSONResponse(content=metrics)

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect metrics",
        )


@router.get(
    "/metrics/prometheus",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Prometheus metrics",
    description="Get metrics in Prometheus format (requires METRICS_ENABLED=true)",
)
async def get_prometheus_metrics() -> PlainTextResponse:
    """Prometheus metrics endpoint.

    Returns application metrics in Prometheus text format. This endpoint
    is gated by the METRICS_ENABLED environment variable.
    """
    metrics_enabled = os.getenv("METRICS_ENABLED", "false").lower() == "true"

    if not metrics_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metrics endpoint is disabled"
        )

    try:
        # Basic Prometheus-style metrics
        prometheus_metrics = f"""# HELP goldleaves_info Application information
# TYPE goldleaves_info gauge
goldleaves_info{{version="{_get_version()}",environment="{_get_environment()}"}} 1

# HELP goldleaves_up Application uptime status
# TYPE goldleaves_up gauge
goldleaves_up 1

# HELP goldleaves_requests_total Total number of requests
# TYPE goldleaves_requests_total counter
goldleaves_requests_total 0

# HELP goldleaves_errors_total Total number of errors
# TYPE goldleaves_errors_total counter
goldleaves_errors_total 0
"""

        return PlainTextResponse(content=prometheus_metrics)

    except Exception as e:
        logger.error(f"Prometheus metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect Prometheus metrics",
        )
