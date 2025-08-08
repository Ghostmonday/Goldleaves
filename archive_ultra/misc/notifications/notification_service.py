"""
Unified notification service for coordinating all notification channels.
Combines email, webhook, and other notification methods into a single interface.
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.config import settings
from core.logging import get_logger
from core.exceptions import NotificationError

from notifications.email_service import (
    EmailService, EmailPriority, EmailAttachment, EmailDeliveryResult,
    email_service
)
from notifications.webhook_service import (
    WebhookService, WebhookEvent, WebhookConfig, WebhookDeliveryResult,
    webhook_service
)


logger = get_logger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"  # Future implementation
    PUSH = "push"  # Future implementation
    IN_APP = "in_app"  # Future implementation


class NotificationType(str, Enum):
    """Types of notifications."""
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    DOCUMENT_UPDATE = "document_update"
    CASE_UPDATE = "case_update"
    PREDICTION_COMPLETE = "prediction_complete"
    SECURITY_ALERT = "security_alert"
    REMINDER = "reminder"
    REPORT = "report"


class NotificationPriority(str, Enum):
    """Unified notification priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationRequest(BaseModel):
    """Unified notification request."""
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.EMAIL])
    recipients: Dict[str, List[str]]  # Channel -> recipient list mapping
    subject: str
    message: str
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[EmailAttachment]] = None
    webhook_event: Optional[WebhookEvent] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResult(BaseModel):
    """Unified notification result."""
    request_id: str
    status: str  # success, failed, partial_success
    timestamp: datetime
    channel_results: Dict[str, List[Union[EmailDeliveryResult, WebhookDeliveryResult]]]
    errors: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class NotificationService:
    """
    Unified notification service for coordinating all notification channels.
    """
    
    def __init__(self):
        self.email_service = email_service
        self.webhook_service = webhook_service
        
        # Notification templates mapping
        self.notification_templates = {
            NotificationType.SYSTEM_ALERT: "system_alert",
            NotificationType.USER_ACTION: "user_action",
            NotificationType.DOCUMENT_UPDATE: "document_update",
            NotificationType.CASE_UPDATE: "case_update",
            NotificationType.PREDICTION_COMPLETE: "prediction_complete",
            NotificationType.SECURITY_ALERT: "security_alert",
            NotificationType.REMINDER: "reminder",
            NotificationType.REPORT: "report"
        }
        
        # Priority mapping
        self.priority_map = {
            NotificationPriority.LOW: EmailPriority.LOW,
            NotificationPriority.NORMAL: EmailPriority.NORMAL,
            NotificationPriority.HIGH: EmailPriority.HIGH,
            NotificationPriority.URGENT: EmailPriority.URGENT
        }
    
    async def send_notification(
        self,
        request: NotificationRequest
    ) -> NotificationResult:
        """
        Send notification through specified channels.
        """
        request_id = f"notif_{datetime.utcnow().timestamp()}"
        channel_results = {}
        errors = []
        
        # Process each channel
        tasks = []
        
        if NotificationChannel.EMAIL in request.channels:
            email_task = self._send_email_notifications(request)
            tasks.append(("email", email_task))
        
        if NotificationChannel.WEBHOOK in request.channels:
            webhook_task = self._send_webhook_notifications(request)
            tasks.append(("webhook", webhook_task))
        
        # Execute all channel tasks concurrently
        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            for idx, (channel, _) in enumerate(tasks):
                if isinstance(results[idx], Exception):
                    errors.append(f"{channel}: {str(results[idx])}")
                    channel_results[channel] = []
                else:
                    channel_results[channel] = results[idx]
        
        # Determine overall status
        total_sent = sum(len(results) for results in channel_results.values())
        total_failed = len(errors)
        
        if total_sent > 0 and total_failed == 0:
            status = "success"
        elif total_sent > 0 and total_failed > 0:
            status = "partial_success"
        else:
            status = "failed"
        
        result = NotificationResult(
            request_id=request_id,
            status=status,
            timestamp=datetime.utcnow(),
            channel_results=channel_results,
            errors=errors,
            metadata=request.metadata
        )
        
        logger.info(f"Notification sent: {request_id} - {status}")
        
        return result
    
    async def _send_email_notifications(
        self,
        request: NotificationRequest
    ) -> List[EmailDeliveryResult]:
        """Send email notifications."""
        from notifications.email_service import EmailMessage
        
        results = []
        
        email_recipients = request.recipients.get("email", [])
        if not email_recipients:
            return results
        
        # Use template if specified
        template_name = request.template_name or self.notification_templates.get(request.type)
        
        # Prepare template data
        template_data = {
            "subject": request.subject,
            "message": request.message,
            "type": request.type.value,
            "priority": request.priority.value,
            "timestamp": datetime.utcnow().isoformat(),
            **(request.template_data or {}),
            **(request.data or {})
        }
        
        # Create email messages
        messages = []
        for recipient in email_recipients:
            email_message = EmailMessage(
                to=recipient,
                subject=request.subject,
                body=request.message,
                template_name=template_name,
                template_data=template_data,
                priority=self.priority_map[request.priority],
                attachments=request.attachments,
                metadata={
                    "notification_type": request.type.value,
                    **(request.metadata or {})
                }
            )
            messages.append(email_message)
        
        # Send emails in batches
        if messages:
            results = await self.email_service.send_bulk(messages)
        
        return results
    
    async def _send_webhook_notifications(
        self,
        request: NotificationRequest
    ) -> List[WebhookDeliveryResult]:
        """Send webhook notifications."""
        # Map notification type to webhook event
        webhook_event = request.webhook_event or self._map_to_webhook_event(request.type)
        
        # Prepare webhook data
        webhook_data = {
            "notification_type": request.type.value,
            "subject": request.subject,
            "message": request.message,
            "priority": request.priority.value,
            **(request.data or {})
        }
        
        # Broadcast to all registered webhooks
        results = await self.webhook_service.broadcast_event(
            event_type=webhook_event,
            data=webhook_data,
            metadata=request.metadata
        )
        
        return results
    
    def _map_to_webhook_event(self, notification_type: NotificationType) -> WebhookEvent:
        """Map notification type to webhook event."""
        mapping = {
            NotificationType.SYSTEM_ALERT: WebhookEvent.SYSTEM_ALERT,
            NotificationType.DOCUMENT_UPDATE: WebhookEvent.DOCUMENT_UPDATED,
            NotificationType.CASE_UPDATE: WebhookEvent.CASE_UPDATED,
            NotificationType.PREDICTION_COMPLETE: WebhookEvent.PREDICTION_COMPLETED,
            NotificationType.USER_ACTION: WebhookEvent.CUSTOM,
            NotificationType.SECURITY_ALERT: WebhookEvent.SYSTEM_ALERT,
            NotificationType.REMINDER: WebhookEvent.CUSTOM,
            NotificationType.REPORT: WebhookEvent.CUSTOM
        }
        return mapping.get(notification_type, WebhookEvent.CUSTOM)
    
    async def notify_document_created(
        self,
        document_id: int,
        document_title: str,
        created_by: str,
        organization_id: int,
        recipients: List[str]
    ) -> NotificationResult:
        """Send notification for document creation."""
        return await self.send_notification(
            NotificationRequest(
                type=NotificationType.DOCUMENT_UPDATE,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK],
                recipients={"email": recipients},
                subject=f"New Document: {document_title}",
                message=f"A new document '{document_title}' has been created by {created_by}.",
                webhook_event=WebhookEvent.DOCUMENT_CREATED,
                data={
                    "document_id": document_id,
                    "document_title": document_title,
                    "created_by": created_by,
                    "organization_id": organization_id
                }
            )
        )
    
    async def notify_prediction_complete(
        self,
        document_id: int,
        document_title: str,
        confidence_score: float,
        processing_time_ms: int,
        recipients: List[str]
    ) -> NotificationResult:
        """Send notification for completed AI prediction."""
        priority = (
            NotificationPriority.HIGH if confidence_score < 0.7
            else NotificationPriority.NORMAL
        )
        
        return await self.send_notification(
            NotificationRequest(
                type=NotificationType.PREDICTION_COMPLETE,
                priority=priority,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK],
                recipients={"email": recipients},
                subject=f"AI Prediction Complete: {document_title}",
                message=(
                    f"AI prediction completed for '{document_title}' "
                    f"with confidence score: {confidence_score:.2%}"
                ),
                webhook_event=WebhookEvent.PREDICTION_COMPLETED,
                data={
                    "document_id": document_id,
                    "document_title": document_title,
                    "confidence_score": confidence_score,
                    "processing_time_ms": processing_time_ms
                }
            )
        )
    
    async def notify_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        """Send system alert notification."""
        priority_map = {
            "info": NotificationPriority.LOW,
            "warning": NotificationPriority.NORMAL,
            "error": NotificationPriority.HIGH,
            "critical": NotificationPriority.URGENT
        }
        
        # Get admin emails from settings
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [getattr(settings, 'FROM_EMAIL', 'admin@goldleaves.com')])
        
        return await self.send_notification(
            NotificationRequest(
                type=NotificationType.SYSTEM_ALERT,
                priority=priority_map.get(severity, NotificationPriority.HIGH),
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK],
                recipients={"email": admin_emails},
                subject=f"[{severity.upper()}] System Alert: {alert_type}",
                message=message,
                webhook_event=WebhookEvent.SYSTEM_ALERT,
                data={
                    "alert_type": alert_type,
                    "severity": severity,
                    "details": details or {}
                }
            )
        )
    
    async def send_bulk_notifications(
        self,
        requests: List[NotificationRequest],
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> List[NotificationResult]:
        """Send multiple notifications in batches."""
        results = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[self.send_notification(req) for req in batch],
                return_exceptions=True
            )
            
            # Handle results
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Create error result
                    error_result = NotificationResult(
                        request_id=f"error_{idx}",
                        status="failed",
                        timestamp=datetime.utcnow(),
                        channel_results={},
                        errors=[str(result)]
                    )
                    results.append(error_result)
                else:
                    results.append(result)
            
            # Delay between batches
            if i + batch_size < len(requests):
                await asyncio.sleep(delay_between_batches)
        
        return results
    
    def register_webhook_endpoint(
        self,
        webhook_id: str,
        url: str,
        events: List[WebhookEvent],
        auth_type: str = "none",
        auth_credentials: Optional[Dict[str, str]] = None
    ) -> None:
        """Register a webhook endpoint for notifications."""
        from notifications.webhook_service import WebhookAuthType
        
        config = WebhookConfig(
            url=url,
            events=events,
            auth_type=WebhookAuthType(auth_type),
            auth_credentials=auth_credentials
        )
        
        self.webhook_service.register_webhook(webhook_id, config)
        logger.info(f"Registered webhook endpoint: {webhook_id} -> {url}")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get combined notification statistics."""
        webhook_stats = self.webhook_service.get_webhook_stats()
        
        return {
            "webhooks": webhook_stats,
            "channels_available": [
                NotificationChannel.EMAIL.value,
                NotificationChannel.WEBHOOK.value
            ],
            "templates_configured": List[Any](self.notification_templates.keys())
        }


# Global service instance
notification_service = NotificationService()
