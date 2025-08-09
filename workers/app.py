"""Celery application configuration for Goldleaves background tasks."""

import os
import logging

logger = logging.getLogger(__name__)


def create_celery_app():
    """Create and configure Celery application.
    
    Returns:
        Configured Celery application instance
        
    Raises:
        RuntimeError: If celery is not installed or REDIS_URL not configured
    """
    try:
        from celery import Celery
    except ImportError:
        raise RuntimeError(
            "celery is not installed. Please install it with: pip install celery[redis]"
        )
    
    # Get Redis URL for broker
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError(
            "REDIS_URL environment variable is required for Celery broker. "
            "Please set REDIS_URL (e.g., redis://localhost:6379/0)"
        )
    
    # Create Celery app
    app = Celery(
        "goldleaves",
        broker=redis_url,
        backend=redis_url,
        include=["workers.tasks"]
    )
    
    # Configure Celery
    app.conf.update(
        # Task routing and execution
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        
        # Task result expiration
        result_expires=3600,  # 1 hour
        
        # Worker configuration
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        
        # Task routing
        task_default_queue="default",
        task_routes={
            "workers.tasks.long_doc_job": {"queue": "documents"},
            "workers.tasks.*": {"queue": "default"},
        },
        
        # Retry policy
        task_default_retry_delay=60,  # seconds
        task_max_retries=3,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
    )
    
    # Auto-discover tasks
    app.autodiscover_tasks(["workers.tasks"])
    
    logger.info(f"Celery app configured with broker: {redis_url}")
    return app


# Create the Celery app instance
try:
    celery_app = create_celery_app()
except RuntimeError as e:
    logger.warning(f"Failed to create Celery app: {e}")
    celery_app = None


# Make celery app available for import
app = celery_app


if __name__ == "__main__":
    # Allow running celery worker directly
    if celery_app:
        celery_app.start()