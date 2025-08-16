"""
Email notification service with template support and retry logic.
Production-grade implementation with delivery tracking.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import jinja2
from pathlib import Path
import uuid
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import settings
from core.logging import get_logger
from core.exceptions import NotificationError


logger = get_logger(__name__)


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EmailAttachment:
    """Email attachment data."""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class EmailMessage(BaseModel):
    """Email message model."""
    to: Union[EmailStr, List[EmailStr]]
    subject: str
    body: str
    html_body: Optional[str] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    reply_to: Optional[EmailStr] = None
    priority: EmailPriority = EmailPriority.NORMAL
    headers: Optional[Dict[str, str]] = None
    attachments: Optional[List[EmailAttachment]] = None
    template_name: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    tracking_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = None


class EmailDeliveryResult(BaseModel):
    """Email delivery result."""
    tracking_id: str
    status: EmailStatus
    message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class EmailService:
    """
    Email notification service with retry logic and template support.
    """

    def __init__(self):
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_tls = getattr(settings, 'SMTP_TLS', True)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@goldleaves.com')
        self.from_name = getattr(settings, 'FROM_NAME', 'Goldleaves')

        # Template configuration
        self.template_dir = Path("templates/email")
        self.template_env = self._setup_template_env()

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.retry_backoff = 2  # exponential backoff multiplier

        # Delivery tracking
        self._delivery_cache: Dict[str, EmailDeliveryResult] = {}

    def _setup_template_env(self) -> jinja2.Environment:
        """Set up Jinja2 template environment."""
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)

        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            enable_async=True
        )

    async def send_email(
        self,
        message: EmailMessage,
        retry: bool = True
    ) -> EmailDeliveryResult:
        """
        Send an email with optional retry logic.
        """
        # Process template if specified
        if message.template_name:
            await self._process_template(message)

        # Convert recipients to list
        recipients = message.to if isinstance(message.to, list) else [message.to]

        # Build email
        msg = MIMEMultipart('mixed')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = message.subject

        if message.cc:
            msg['Cc'] = ', '.join(message.cc)
            recipients.extend(message.cc)

        if message.reply_to:
            msg['Reply-To'] = message.reply_to

        # Set priority
        if message.priority == EmailPriority.HIGH:
            msg['X-Priority'] = '1'
            msg['Importance'] = 'high'
        elif message.priority == EmailPriority.URGENT:
            msg['X-Priority'] = '1'
            msg['Importance'] = 'high'
            msg['X-MSMail-Priority'] = 'High'

        # Add custom headers
        if message.headers:
            for key, value in message.headers.items():
                msg[key] = value

        # Add tracking header
        msg['X-Tracking-ID'] = message.tracking_id

        # Create message body
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # Add text part
        text_part = MIMEText(message.body, 'plain', 'utf-8')
        msg_alternative.attach(text_part)

        # Add HTML part if provided
        if message.html_body:
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            msg_alternative.attach(html_part)

        # Add attachments
        if message.attachments:
            for attachment in message.attachments:
                self._add_attachment(msg, attachment)

        # Send with retry logic
        result = EmailDeliveryResult(
            tracking_id=message.tracking_id,
            status=EmailStatus.PENDING,
            metadata=message.metadata
        )

        if retry:
            result = await self._send_with_retry(msg, recipients, result)
        else:
            result = await self._send_once(msg, recipients, result)

        # Cache delivery result
        self._delivery_cache[result.tracking_id] = result

        return result

    async def _send_with_retry(
        self,
        msg: MIMEMultipart,
        recipients: List[str],
        result: EmailDeliveryResult
    ) -> EmailDeliveryResult:
        """Send email with exponential backoff retry."""
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                return await self._send_once(msg, recipients, result)
            except Exception as e:
                result.retry_count = attempt
                result.error = str(e)

                if attempt < self.max_retries:
                    logger.warning(
                        f"Email send attempt {attempt + 1} failed for {result.tracking_id}: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                    delay *= self.retry_backoff
                else:
                    logger.error(
                        f"Email send failed after {self.max_retries + 1} attempts for {result.tracking_id}: {e}"
                    )
                    result.status = EmailStatus.FAILED

        return result

    async def _send_once(
        self,
        msg: MIMEMultipart,
        recipients: List[str],
        result: EmailDeliveryResult
    ) -> EmailDeliveryResult:
        """Send email once via SMTP."""
        try:
            # In development mode, just log the email
            if getattr(settings, 'ENVIRONMENT', 'development') == 'development':
                logger.info(f"DEV MODE: Email would be sent to {recipients}")
                logger.info(f"Subject: {msg['Subject']}")
                logger.info(f"From: {msg['From']}")

                result.status = EmailStatus.SENT
                result.sent_at = datetime.utcnow()
                result.message_id = f"dev_{uuid.uuid4()}"
                result.error = None

                return result

            # Connect to SMTP server
            if self.smtp_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            # Authenticate if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send email
            send_result = server.send_message(msg, to_addrs=recipients)
            server.quit()

            # Update result
            result.status = EmailStatus.SENT
            result.sent_at = datetime.utcnow()
            result.message_id = msg.get('Message-ID')
            result.error = None

            logger.info(f"Email sent successfully: {result.tracking_id}")

            return result

        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipients refused for {result.tracking_id}: {e}")
            result.status = EmailStatus.BOUNCED
            result.error = "Recipients refused"
            raise

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error for {result.tracking_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error sending email {result.tracking_id}: {e}")
            raise

    async def _process_template(self, message: EmailMessage) -> None:
        """Process email template with data."""
        try:
            # Load templates
            text_template = self.template_env.get_template(f"{message.template_name}.txt")

            # Render text version
            message.body = await text_template.render_async(
                **(message.template_data or {})
            )

            # Try to load HTML template
            try:
                html_template = self.template_env.get_template(f"{message.template_name}.html")
                message.html_body = await html_template.render_async(
                    **(message.template_data or {})
                )
            except jinja2.TemplateNotFound:
                # HTML template is optional
                pass

        except jinja2.TemplateNotFound:
            raise NotificationError(f"Email template not found: {message.template_name}")
        except Exception as e:
            raise NotificationError(f"Error processing email template: {e}")

    def _add_attachment(self, msg: MIMEMultipart, attachment: EmailAttachment) -> None:
        """Add attachment to email message."""
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment.filename}"'
        )
        part.add_header('Content-Type', attachment.content_type)
        msg.attach(part)

    async def send_bulk(
        self,
        messages: List[EmailMessage],
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> List[EmailDeliveryResult]:
        """Send multiple emails in batches."""
        results = []

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]

            # Send batch concurrently
            batch_results = await asyncio.gather(
                *[self.send_email(msg) for msg in batch],
                return_exceptions=True
            )

            # Process results
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Create failed result for exception
                    failed_result = EmailDeliveryResult(
                        tracking_id=batch[idx].tracking_id,
                        status=EmailStatus.FAILED,
                        error=str(result)
                    )
                    results.append(failed_result)
                else:
                    results.append(result)

            # Delay between batches
            if i + batch_size < len(messages):
                await asyncio.sleep(delay_between_batches)

        return results

    def get_delivery_status(self, tracking_id: str) -> Optional[EmailDeliveryResult]:
        """Get delivery status by tracking ID."""
        return self._delivery_cache.get(tracking_id)

    async def send_notification(
        self,
        recipient: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        priority: EmailPriority = EmailPriority.NORMAL,
        attachments: Optional[List[EmailAttachment]] = None
    ) -> EmailDeliveryResult:
        """
        Convenience method to send templated notification emails.
        """
        message = EmailMessage(
            to=recipient,
            subject=subject,
            body="",  # Will be filled by template
            template_name=template_name,
            template_data=template_data,
            priority=priority,
            attachments=attachments
        )

        return await self.send_email(message)

    async def send_system_alert(
        self,
        subject: str,
        message: str,
        priority: EmailPriority = EmailPriority.HIGH,
        recipients: Optional[List[str]] = None
    ) -> EmailDeliveryResult:
        """Send system alert email."""
        # Use admin emails from config if not specified
        if not recipients:
            recipients = getattr(settings, 'ADMIN_EMAILS', [self.from_email])

        email_message = EmailMessage(
            to=recipients,
            subject=f"[System Alert] {subject}",
            body=message,
            priority=priority,
            metadata={"type": "system_alert"}
        )

        return await self.send_email(email_message)


# Global service instance
email_service = EmailService()
