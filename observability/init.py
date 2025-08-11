"""Observability initialization for Sentry and OpenTelemetry."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global flags to track initialization status
_sentry_initialized = False
_otel_initialized = False


def init_sentry() -> bool:
    """Initialize Sentry error tracking.
    
    Returns:
        True if Sentry was initialized successfully, False otherwise
    """
    global _sentry_initialized
    
    if _sentry_initialized:
        logger.debug("Sentry already initialized")
        return True
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        logger.debug("SENTRY_DSN not configured, skipping Sentry initialization")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        environment = os.getenv("ENVIRONMENT", "development")
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                StarletteIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            # Performance monitoring
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            
            # Error filtering
            before_send=_filter_sentry_events,
            
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII for privacy
            max_breadcrumbs=50,
            
            # Release tracking
            release=os.getenv("APP_VERSION"),
            
            # Server name
            server_name=os.getenv("HOSTNAME", "goldleaves-api")
        )
        
        _sentry_initialized = True
        logger.info(f"Sentry initialized successfully for environment: {environment}")
        return True
        
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def init_opentelemetry() -> bool:
    """Initialize OpenTelemetry tracing and metrics.
    
    Returns:
        True if OpenTelemetry was initialized successfully, False otherwise
    """
    global _otel_initialized
    
    if _otel_initialized:
        logger.debug("OpenTelemetry already initialized")
        return True
    
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    service_name = os.getenv("OTEL_SERVICE_NAME", "goldleaves-api")
    
    if not otel_endpoint:
        logger.debug("OTEL_EXPORTER_OTLP_ENDPOINT not configured, skipping OpenTelemetry initialization")
        return False
    
    try:
        from opentelemetry import trace, metrics
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.getenv("APP_VERSION", "unknown"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Initialize tracing
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer_provider = trace.get_tracer_provider()
        
        # Configure OTLP span exporter
        span_exporter = OTLPSpanExporter(
            endpoint=otel_endpoint,
            headers=_get_otel_headers()
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Initialize metrics
        metric_exporter = OTLPMetricExporter(
            endpoint=otel_endpoint,
            headers=_get_otel_headers()
        )
        
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=30000  # Export every 30 seconds
        )
        
        metrics.set_meter_provider(MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        ))
        
        # Auto-instrument frameworks
        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        
        _otel_initialized = True
        logger.info(f"OpenTelemetry initialized successfully for service: {service_name}")
        return True
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


def _filter_sentry_events(event, hint):
    """Filter Sentry events to reduce noise.
    
    Args:
        event: Sentry event data
        hint: Additional context
        
    Returns:
        Event to send or None to drop
    """
    # Drop health check errors
    if 'request' in event and event['request'].get('url', '').endswith('/health'):
        return None
    
    # Drop certain expected exceptions
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            exc_type = exception.get('type', '')
            
            # Drop rate limit errors (they're expected)
            if exc_type in ['HTTPException'] and '429' in str(exception.get('value', '')):
                return None
            
            # Drop validation errors (client-side issues)
            if exc_type in ['ValidationError', 'RequestValidationError']:
                return None
    
    return event


def _get_otel_headers() -> dict:
    """Get headers for OpenTelemetry exporters.
    
    Returns:
        Dictionary of headers
    """
    headers = {}
    
    # Add authentication if available
    if os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
        # Parse headers from environment (format: key1=value1,key2=value2)
        header_string = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
        for header_pair in header_string.split(','):
            if '=' in header_pair:
                key, value = header_pair.split('=', 1)
                headers[key.strip()] = value.strip()
    
    return headers


def init_observability() -> dict:
    """Initialize all observability components.
    
    This function should be called once during application startup.
    
    Returns:
        Dictionary with initialization status for each component
    """
    logger.info("Initializing observability components...")
    
    results = {
        "sentry": init_sentry(),
        "opentelemetry": init_opentelemetry()
    }
    
    initialized_components = [name for name, success in results.items() if success]
    
    if initialized_components:
        logger.info(f"Observability initialized: {', '.join(initialized_components)}")
    else:
        logger.info("No observability components initialized (configuration not found)")
    
    return results


def is_initialized() -> dict:
    """Check which observability components are initialized.
    
    Returns:
        Dictionary showing initialization status
    """
    return {
        "sentry": _sentry_initialized,
        "opentelemetry": _otel_initialized
    }


# Utility functions for manual instrumentation
def get_tracer(name: str = "goldleaves"):
    """Get OpenTelemetry tracer for manual instrumentation.
    
    Args:
        name: Tracer name
        
    Returns:
        Tracer instance or None if OpenTelemetry not initialized
    """
    if not _otel_initialized:
        return None
    
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except Exception:
        return None


def get_meter(name: str = "goldleaves"):
    """Get OpenTelemetry meter for custom metrics.
    
    Args:
        name: Meter name
        
    Returns:
        Meter instance or None if OpenTelemetry not initialized
    """
    if not _otel_initialized:
        return None
    
    try:
        from opentelemetry import metrics
        return metrics.get_meter(name)
    except Exception:
        return None