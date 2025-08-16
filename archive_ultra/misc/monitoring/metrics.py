"""
Metrics collection and monitoring for Goldleaves application.
Provides Prometheus-compatible metrics for system monitoring.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import threading

from prometheus_client import (
    Counter as PrometheusCounter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST
)


# Application metrics
request_count = PrometheusCounter(
    'goldleaves_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'goldleaves_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'goldleaves_active_users',
    'Number of currently active users'
)

document_count = Gauge(
    'goldleaves_documents_total',
    'Total number of documents in the system'
)

notification_count = PrometheusCounter(
    'goldleaves_notifications_total',
    'Total number of notifications sent',
    ['type', 'channel', 'status']
)

webhook_delivery_count = PrometheusCounter(
    'goldleaves_webhook_deliveries_total',
    'Total number of webhook deliveries',
    ['status']
)

email_delivery_count = PrometheusCounter(
    'goldleaves_email_deliveries_total',
    'Total number of email deliveries',
    ['status']
)

database_connection_pool = Gauge(
    'goldleaves_db_connections',
    'Database connection pool status',
    ['status']
)

cache_operations = PrometheusCounter(
    'goldleaves_cache_operations_total',
    'Cache operations',
    ['operation', 'result']
)

# Application info
app_info = Info(
    'goldleaves_app_info',
    'Application information'
)


class MetricsCollector:
    """
    Centralized metrics collection for the application.
    """

    def __init__(self):
        self._start_time = time.time()
        self._custom_metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Initialize app info
        app_info.info({
            'version': '1.0.0',
            'environment': 'development',  # This would come from settings
            'start_time': datetime.utcnow().isoformat()
        })

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ):
        """Record HTTP request metrics."""
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_notification(
        self,
        notification_type: str,
        channel: str,
        status: str
    ):
        """Record notification delivery metrics."""
        notification_count.labels(
            type=notification_type,
            channel=channel,
            status=status
        ).inc()

    def record_webhook_delivery(self, status: str):
        """Record webhook delivery metrics."""
        webhook_delivery_count.labels(status=status).inc()

    def record_email_delivery(self, status: str):
        """Record email delivery metrics."""
        email_delivery_count.labels(status=status).inc()

    def update_active_users(self, count: int):
        """Update active users count."""
        active_users.set(count)

    def update_document_count(self, count: int):
        """Update total document count."""
        document_count.set(count)

    def update_db_connections(self, active: int, idle: int, total: int):
        """Update database connection metrics."""
        database_connection_pool.labels(status='active').set(active)
        database_connection_pool.labels(status='idle').set(idle)
        database_connection_pool.labels(status='total').set(total)

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        cache_operations.labels(
            operation=operation,
            result=result
        ).inc()

    def set_custom_metric(self, name: str, value: Any, labels: Optional[Dict[str, str]] = None):
        """Set custom application metric."""
        with self._lock:
            key = f"{name}_{labels}" if labels else name
            self._custom_metrics[key] = {
                'name': name,
                'value': value,
                'labels': labels or {},
                'timestamp': time.time()
            }

    def get_custom_metrics(self) -> Dict[str, Any]:
        """Get all custom metrics."""
        with self._lock:
            return self._custom_metrics.copy()

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics."""
        return generate_latest().decode('utf-8')

    def get_application_stats(self) -> Dict[str, Any]:
        """Get comprehensive application statistics."""
        uptime = time.time() - self._start_time

        return {
            'uptime_seconds': uptime,
            'uptime_human': str(timedelta(seconds=int(uptime))),
            'start_time': datetime.fromtimestamp(self._start_time).isoformat(),
            'current_time': datetime.utcnow().isoformat(),
            'custom_metrics': self.get_custom_metrics(),
            'system_metrics': {
                'active_users': active_users._value._value,
                'total_documents': document_count._value._value,
            }
        }

    def reset_metrics(self):
        """Reset all metrics (for testing)."""
        # Note: Prometheus metrics cannot be reset in production
        # This is mainly for testing purposes
        with self._lock:
            self._custom_metrics.clear()


# Global metrics collector instance
metrics = MetricsCollector()


# Convenience functions
def record_request_metric(method: str, endpoint: str, status_code: int, duration: float):
    """Convenience function to record request metrics."""
    metrics.record_request(method, endpoint, status_code, duration)


def record_notification_metric(notification_type: str, channel: str, status: str):
    """Convenience function to record notification metrics."""
    metrics.record_notification(notification_type, channel, status)


def record_webhook_metric(status: str):
    """Convenience function to record webhook metrics."""
    metrics.record_webhook_delivery(status)


def record_email_metric(status: str):
    """Convenience function to record email metrics."""
    metrics.record_email_delivery(status)


# Context manager for timing operations
class timer:
    """Context manager for timing operations."""

    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metrics.set_custom_metric(
            f"{self.metric_name}_duration",
            duration,
            self.labels
        )


# Decorator for timing functions
def timed_operation(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to time function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with timer(metric_name, labels):
                return func(*args, **kwargs)
        return wrapper
    return decorator
