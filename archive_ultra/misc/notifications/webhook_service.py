"""
Webhook notification service with retry logic and delivery tracking.
Supports multiple webhook endpoints with authentication.
"""

import asyncio
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid

try:
    import httpx
except ImportError:
    httpx = None

from pydantic import BaseModel, HttpUrl, Field, validator
from sqlalchemy.orm import Session

from app.config import settings
from core.logging import get_logger
from core.exceptions import NotificationError


logger = get_logger(__name__)


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"


class WebhookAuthType(str, Enum):
    """Webhook authentication types."""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    HMAC = "hmac"
    API_KEY = "api_key"


class WebhookEvent(str, Enum):
    """Standard webhook event types."""
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_CLOSED = "case.closed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    PREDICTION_COMPLETED = "prediction.completed"
    PREDICTION_CORRECTED = "prediction.corrected"
    SYSTEM_ALERT = "system.alert"
    CUSTOM = "custom"


class WebhookConfig(BaseModel):
    """Webhook endpoint configuration."""
    url: HttpUrl
    events: List[WebhookEvent] = Field(default_factory=list)
    auth_type: WebhookAuthType = WebhookAuthType.NONE
    auth_credentials: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = Field(default=30, ge=1, le=300)
    retry_enabled: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    verify_ssl: bool = True
    active: bool = True
    metadata: Optional[Dict[str, Any]] = None


class WebhookPayload(BaseModel):
    """Webhook payload structure."""
    webhook_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: WebhookEvent
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookDeliveryResult(BaseModel):
    """Webhook delivery result."""
    webhook_id: str
    event_id: str
    status: WebhookStatus
    url: str
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    delivered_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None


class WebhookService:
    """
    Webhook notification service with retry logic and delivery tracking.
    """

    def __init__(self):
        # HTTP client configuration
        if httpx:
            self.http_timeout = httpx.Timeout(30.0, connect=10.0)
            self.http_limits = httpx.Limits(max_keepalive_connections=10, max_connections=100)

        # Retry configuration
        self.retry_delays = [1, 5, 30, 300, 1800]  # seconds: 1s, 5s, 30s, 5m, 30m

        # Delivery tracking
        self._delivery_cache: Dict[str, WebhookDeliveryResult] = {}
        self._webhook_configs: Dict[str, WebhookConfig] = {}

        # Default webhook secret for HMAC
        self.webhook_secret = getattr(settings, 'WEBHOOK_SECRET', 'goldleaves-webhook-secret')

    def register_webhook(self, webhook_id: str, config: WebhookConfig) -> None:
        """Register a webhook endpoint configuration."""
        self._webhook_configs[webhook_id] = config
        logger.info(f"Registered webhook {webhook_id} for events: {config.events}")

    def unregister_webhook(self, webhook_id: str) -> None:
        """Unregister a webhook endpoint."""
        if webhook_id in self._webhook_configs:
            del self._webhook_configs[webhook_id]
            logger.info(f"Unregistered webhook {webhook_id}")

    async def send_webhook(
        self,
        config: WebhookConfig,
        payload: WebhookPayload,
        retry: bool = None
    ) -> WebhookDeliveryResult:
        """
        Send a webhook with optional retry logic.
        """
        retry = retry if retry is not None else config.retry_enabled

        result = WebhookDeliveryResult(
            webhook_id=payload.webhook_id,
            event_id=payload.event_id,
            status=WebhookStatus.PENDING,
            url=str(config.url)
        )

        if retry and config.max_retries > 0:
            result = await self._send_with_retry(config, payload, result)
        else:
            result = await self._send_once(config, payload, result)

        # Cache delivery result
        self._delivery_cache[f"{payload.webhook_id}:{payload.event_id}"] = result

        return result

    async def _send_with_retry(
        self,
        config: WebhookConfig,
        payload: WebhookPayload,
        result: WebhookDeliveryResult
    ) -> WebhookDeliveryResult:
        """Send webhook with exponential backoff retry."""
        for attempt in range(config.max_retries + 1):
            try:
                return await self._send_once(config, payload, result)
            except Exception as e:
                result.retry_count = attempt
                result.error = str(e)

                if attempt < config.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    result.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)

                    logger.warning(
                        f"Webhook send attempt {attempt + 1} failed for {result.event_id}: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Webhook send failed after {config.max_retries + 1} attempts for {result.event_id}: {e}"
                    )
                    result.status = WebhookStatus.FAILED

        return result

    async def _send_once(
        self,
        config: WebhookConfig,
        payload: WebhookPayload,
        result: WebhookDeliveryResult
    ) -> WebhookDeliveryResult:
        """Send webhook once via HTTP."""
        start_time = datetime.utcnow()

        # In development mode, just log the webhook
        if getattr(settings, 'ENVIRONMENT', 'development') == 'development' or not httpx:
            logger.info(f"DEV MODE: Webhook would be sent to {config.url}")
            logger.info(f"Event: {payload.event_type.value}")
            logger.info(f"Data: {payload.data}")

            result.status = WebhookStatus.SUCCESS
            result.status_code = 200
            result.delivered_at = datetime.utcnow()
            result.duration_ms = 50  # Mock duration
            result.error = None

            return result

        async with httpx.AsyncClient(
            timeout=self.http_timeout,
            limits=self.http_limits,
            verify=config.verify_ssl
        ) as client:
            try:
                # Prepare headers
                headers = self._prepare_headers(config, payload)

                # Prepare request
                response = await client.post(
                    str(config.url),
                    json=payload.dict(),
                    headers=headers,
                    timeout=config.timeout
                )

                # Calculate duration
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Update result
                result.status_code = response.status_code
                result.response_body = response.text[:1000]  # Limit response size
                result.delivered_at = datetime.utcnow()
                result.duration_ms = int(duration)

                # Check response status
                if 200 <= response.status_code < 300:
                    result.status = WebhookStatus.SUCCESS
                    result.error = None
                    logger.info(
                        f"Webhook delivered successfully: {result.event_id} to {config.url} "
                        f"(status: {response.status_code}, duration: {duration}ms)"
                    )
                else:
                    result.status = WebhookStatus.INVALID_RESPONSE
                    result.error = f"HTTP {response.status_code}: {response.text[:200]}"
                    raise NotificationError(f"Webhook returned status {response.status_code}")

                return result

            except (httpx.TimeoutException if httpx else Exception) as e:
                logger.error(f"Webhook timeout for {result.event_id}: {e}")
                result.status = WebhookStatus.TIMEOUT
                result.error = "Request timeout"
                raise

            except (httpx.HTTPError if httpx else Exception) as e:
                logger.error(f"HTTP error for webhook {result.event_id}: {e}")
                result.error = f"HTTP error: {str(e)}"
                raise

            except Exception as e:
                logger.error(f"Unexpected error sending webhook {result.event_id}: {e}")
                result.error = str(e)
                raise

    def _prepare_headers(
        self,
        config: WebhookConfig,
        payload: WebhookPayload
    ) -> Dict[str, str]:
        """Prepare HTTP headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Goldleaves-Webhook/{getattr(settings, 'VERSION', '1.0.0')}",
            "X-Webhook-ID": payload.webhook_id,
            "X-Event-ID": payload.event_id,
            "X-Event-Type": payload.event_type.value,
            "X-Event-Timestamp": payload.timestamp.isoformat()
        }

        # Add custom headers
        if config.headers:
            headers.update(config.headers)

        # Add authentication
        if config.auth_type != WebhookAuthType.NONE and config.auth_credentials:
            if config.auth_type == WebhookAuthType.BEARER:
                token = config.auth_credentials.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            elif config.auth_type == WebhookAuthType.BASIC:
                username = config.auth_credentials.get("username")
                password = config.auth_credentials.get("password")
                if username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    headers["Authorization"] = f"Basic {credentials}"

            elif config.auth_type == WebhookAuthType.API_KEY:
                key_name = config.auth_credentials.get("header_name", "X-API-Key")
                api_key = config.auth_credentials.get("api_key")
                if api_key:
                    headers[key_name] = api_key

            elif config.auth_type == WebhookAuthType.HMAC:
                # Generate HMAC signature
                secret = config.auth_credentials.get("secret", self.webhook_secret)
                signature = self._generate_hmac_signature(payload, secret)
                headers["X-Webhook-Signature"] = signature

        return headers

    def _generate_hmac_signature(self, payload: WebhookPayload, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        payload_json = json.dumps(payload.dict(), sort_keys=True, default=str)
        signature = hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def broadcast_event(
        self,
        event_type: WebhookEvent,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[WebhookDeliveryResult]:
        """
        Broadcast an event to all registered webhooks that subscribe to it.
        """
        payload = WebhookPayload(
            event_type=event_type,
            data=data,
            metadata=metadata
        )

        results = []
        tasks = []

        # Find all active webhooks subscribed to this event
        for webhook_id, config in self._webhook_configs.items():
            if config.active and (not config.events or event_type in config.events):
                task = self.send_webhook(config, payload)
                tasks.append(task)

        # Send webhooks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to failed results
            processed_results = []
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_result = WebhookDeliveryResult(
                        webhook_id=payload.webhook_id,
                        event_id=payload.event_id,
                        status=WebhookStatus.FAILED,
                        url="unknown",
                        error=str(result)
                    )
                    processed_results.append(failed_result)
                else:
                    processed_results.append(result)

            return processed_results

        return []

    def get_delivery_status(
        self,
        webhook_id: str,
        event_id: str
    ) -> Optional[WebhookDeliveryResult]:
        """Get delivery status by webhook and event ID."""
        return self._delivery_cache.get(f"{webhook_id}:{event_id}")

    async def retry_failed_webhooks(
        self,
        since: Optional[datetime] = None,
        max_webhooks: int = 100
    ) -> List[WebhookDeliveryResult]:
        """Retry failed webhooks that are due for retry."""
        now = datetime.utcnow()
        if not since:
            since = now - timedelta(hours=24)

        results = []
        retry_count = 0

        for key, result in list(self._delivery_cache.items()):
            if retry_count >= max_webhooks:
                break

            # Check if webhook should be retried
            if (result.status == WebhookStatus.FAILED and
                result.next_retry_at and
                result.next_retry_at <= now and
                result.delivered_at and
                result.delivered_at >= since):

                # Find config
                webhook_id = key.split(':')[0]
                if webhook_id in self._webhook_configs:
                    config = self._webhook_configs[webhook_id]

                    # Recreate payload (in production, this would be stored)
                    payload = WebhookPayload(
                        webhook_id=result.webhook_id,
                        event_id=result.event_id,
                        event_type=WebhookEvent.CUSTOM,
                        data={"retry": True}
                    )

                    # Retry webhook
                    new_result = await self.send_webhook(config, payload)
                    results.append(new_result)
                    retry_count += 1

        logger.info(f"Retried {len(results)} failed webhooks")
        return results

    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook delivery statistics."""
        total = len(self._delivery_cache)
        if total == 0:
            return {
                "total_sent": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0,
                "by_status": {}
            }

        by_status = {}
        durations = []

        for result in self._delivery_cache.values():
            status = result.status.value
            by_status[status] = by_status.get(status, 0) + 1

            if result.duration_ms:
                durations.append(result.duration_ms)

        success_count = by_status.get(WebhookStatus.SUCCESS.value, 0)
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_sent": total,
            "success_count": success_count,
            "success_rate": (success_count / total) * 100,
            "average_duration_ms": avg_duration,
            "by_status": by_status,
            "active_webhooks": len([c for c in self._webhook_configs.values() if c.active])
        }


# Global service instance
webhook_service = WebhookService()
