"""Telemetry initialization for Sentry and OpenTelemetry.

This module provides safe initialization functions for Sentry and OpenTelemetry
that gracefully handle missing environment variables without breaking application boot.
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


def init_sentry(dsn: Optional[str] = None) -> bool:
    """Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN. If not provided, will read from SENTRY_DSN environment variable.

    Returns:
        bool: True if Sentry was successfully initialized, False otherwise.
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        if dsn is None:
            dsn = os.getenv("SENTRY_DSN")

        if not dsn:
            logger.info("Sentry DSN not provided, skipping Sentry initialization")
            return False

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            integrations=[
                FastApiIntegration(auto_session_tracking=True),
                SqlalchemyIntegration(),
            ],
            attach_stacktrace=True,
            send_default_pii=False,
        )

        logger.info("Sentry initialized successfully")
        return True

    except ImportError:
        logger.warning("Sentry SDK not available, skipping initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def init_otel(service_name: str = "goldleaves-api") -> bool:
    """Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing.

    Returns:
        bool: True if OpenTelemetry was successfully initialized, False otherwise.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if not endpoint:
            logger.info(
                "OpenTelemetry endpoint not configured, skipping initialization"
            )
            return False

        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": os.getenv("VERSION", "unknown"),
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))

        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=_get_otel_headers(),
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        logger.info(
            f"OpenTelemetry initialized successfully for service: {service_name}"
        )
        return True

    except ImportError:
        logger.warning("OpenTelemetry packages not available, skipping initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


def _get_otel_headers() -> dict:
    """Get OpenTelemetry headers from environment variables."""
    headers = {}

    # Support common header patterns
    auth_header = os.getenv("OTEL_EXPORTER_OTLP_HEADERS_AUTHORIZATION")
    if auth_header:
        headers["authorization"] = auth_header

    api_key = os.getenv("OTEL_EXPORTER_OTLP_API_KEY")
    if api_key:
        headers["api-key"] = api_key

    # Support generic headers format
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    if headers_env:
        try:
            for header_pair in headers_env.split(","):
                key, value = header_pair.split("=", 1)
                headers[key.strip()] = value.strip()
        except ValueError:
            logger.warning(f"Invalid OTEL_EXPORTER_OTLP_HEADERS format: {headers_env}")

    return headers


def instrument_fastapi_app(app: FastAPI) -> None:
    """Instrument FastAPI application for OpenTelemetry.

    Args:
        app: FastAPI application instance to instrument.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI app instrumented for OpenTelemetry")
        else:
            logger.debug(
                "OpenTelemetry endpoint not configured, skipping instrumentation"
            )

    except ImportError:
        logger.debug("OpenTelemetry FastAPI instrumentation not available")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI app: {e}")


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware to create custom trace spans for requests and responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Create trace spans for request/response cycle."""
        try:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(
                f"{request.method} {request.url.path}",
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.route": request.url.path,
                    "http.user_agent": request.headers.get("user-agent", ""),
                },
            ) as span:
                response = await call_next(request)

                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute(
                    "http.response_size",
                    len(response.body) if hasattr(response, "body") else 0,
                )

                return response

        except ImportError:
            # OpenTelemetry not available, just pass through
            return await call_next(request)
        except Exception as e:
            logger.error(f"Error in tracing middleware: {e}")
            return await call_next(request)


def setup_telemetry(app: FastAPI, service_name: str = "goldleaves-api") -> dict:
    """Setup all telemetry components for the FastAPI application.

    Args:
        app: FastAPI application instance.
        service_name: Name of the service for tracing.

    Returns:
        dict: Status of initialized components.
    """
    status = {
        "sentry": init_sentry(),
        "opentelemetry": init_otel(service_name),
    }

    # Add tracing middleware if OpenTelemetry is enabled
    if status["opentelemetry"]:
        app.add_middleware(TracingMiddleware)
        instrument_fastapi_app(app)

    logger.info(f"Telemetry setup complete: {status}")
    return status
