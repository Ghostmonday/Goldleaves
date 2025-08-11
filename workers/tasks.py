"""Background tasks for Goldleaves using Celery."""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import celery app - handle case where it's not available
try:
    from .app import celery_app
    if celery_app is None:
        raise ImportError("Celery app not available")
except (ImportError, RuntimeError) as e:
    logger.warning(f"Celery not available: {e}")
    
    # Create a dummy decorator for when Celery is not available
    class DummyCelery:
        @staticmethod
        def task(*args, **kwargs):
            def decorator(func):
                logger.warning(f"Task {func.__name__} defined but Celery not available")
                return func
            return decorator
    
    celery_app = DummyCelery()


@celery_app.task(bind=True, name="workers.tasks.long_doc_job")
def long_doc_job(self, doc_id: str) -> str:
    """Simulate a long-running document processing job.
    
    This task simulates work by sleeping but does NOT execute the sleep
    on import - only when the task is actually called.
    
    Args:
        doc_id: Document ID to process
        
    Returns:
        Processing result message
        
    Raises:
        Exception: If document processing fails
    """
    try:
        logger.info(f"Starting long document job for doc_id: {doc_id}")
        
        # Simulate work phases
        phases = [
            ("Initializing", 2),
            ("Parsing document", 3),
            ("Analyzing content", 4),
            ("Generating insights", 3),
            ("Finalizing", 1)
        ]
        
        total_progress = 0
        for phase_name, duration in phases:
            logger.info(f"Doc {doc_id}: {phase_name}...")
            
            # Update task progress if Celery is available
            if hasattr(self, 'update_state'):
                total_progress += duration
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current_phase": phase_name,
                        "progress": min(total_progress * 100 // 13, 95)  # Total ~13 seconds
                    }
                )
            
            # Simulate work (but only when actually called, not on import)
            time.sleep(duration)
        
        result = f"Document {doc_id} processed successfully"
        logger.info(f"Completed long document job for doc_id: {doc_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Document job failed for doc_id {doc_id}: {e}")
        raise


@celery_app.task(name="workers.tasks.send_notification")
def send_notification(user_id: str, message: str, notification_type: str = "info") -> bool:
    """Send a notification to a user.
    
    Args:
        user_id: Target user ID
        message: Notification message
        notification_type: Type of notification (info, warning, error, success)
        
    Returns:
        True if notification sent successfully
    """
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}: {message}")
        
        # Simulate notification sending
        time.sleep(1)
        
        # In a real implementation, this would integrate with:
        # - Email service
        # - Push notification service
        # - In-app notification system
        # - SMS service, etc.
        
        logger.info(f"Notification sent successfully to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")
        raise


@celery_app.task(name="workers.tasks.cleanup_expired_data")
def cleanup_expired_data(data_type: str, days_old: int = 30) -> dict:
    """Clean up expired data of specified type.
    
    Args:
        data_type: Type of data to clean up (e.g., 'temp_files', 'old_logs')
        days_old: Age threshold in days
        
    Returns:
        Cleanup results summary
    """
    try:
        logger.info(f"Starting cleanup of {data_type} older than {days_old} days")
        
        # Simulate cleanup work
        time.sleep(2)
        
        # Mock cleanup results
        cleaned_count = 42  # In real implementation, this would be actual count
        freed_space_mb = 156.7
        
        result = {
            "data_type": data_type,
            "days_old": days_old,
            "items_cleaned": cleaned_count,
            "space_freed_mb": freed_space_mb,
            "status": "completed"
        }
        
        logger.info(f"Cleanup completed: {cleaned_count} items, {freed_space_mb}MB freed")
        return result
        
    except Exception as e:
        logger.error(f"Cleanup task failed for {data_type}: {e}")
        raise


@celery_app.task(name="workers.tasks.generate_report")
def generate_report(report_type: str, user_id: str, filters: Optional[dict] = None) -> str:
    """Generate a report for a user.
    
    Args:
        report_type: Type of report to generate
        user_id: User requesting the report
        filters: Optional filters to apply
        
    Returns:
        Report file path or identifier
    """
    try:
        filters = filters or {}
        logger.info(f"Generating {report_type} report for user {user_id} with filters: {filters}")
        
        # Simulate report generation phases
        phases = ["Collecting data", "Processing", "Formatting", "Finalizing"]
        
        for i, phase in enumerate(phases):
            logger.info(f"Report generation: {phase}...")
            time.sleep(1.5)
            
            # Update progress if Celery is available
            if hasattr(generate_report, 'update_state'):
                generate_report.update_state(
                    state="PROGRESS",
                    meta={
                        "current_phase": phase,
                        "progress": (i + 1) * 25
                    }
                )
        
        # Mock report file path
        report_file = f"reports/{report_type}_{user_id}_{int(time.time())}.pdf"
        
        logger.info(f"Report generated successfully: {report_file}")
        return report_file
        
    except Exception as e:
        logger.error(f"Report generation failed for user {user_id}: {e}")
        raise


# Task status helper functions
def get_task_status(task_id: str) -> Optional[dict]:
    """Get status of a Celery task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status information or None if Celery not available
    """
    if celery_app and hasattr(celery_app, 'AsyncResult'):
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result,
                "traceback": result.traceback
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None
    
    logger.warning("Celery not available, cannot get task status")
    return None


# Export main tasks for easy import
__all__ = [
    "long_doc_job",
    "send_notification", 
    "cleanup_expired_data",
    "generate_report",
    "get_task_status"
]