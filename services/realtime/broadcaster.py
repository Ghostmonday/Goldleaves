# services/realtime/broadcaster.py
"""
Real-time event broadcaster service.
Triggers updates when documents are edited or other events occur.
Integrates with Redis Pub/Sub for distributed broadcasting.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import redis.asyncio as redis

from .connection_manager import MessageType, connection_manager

logger = logging.getLogger(__name__)


class BroadcastEvent(str, Enum):
    """Types of broadcast events."""
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_SHARED = "document.shared"
    
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    USER_UPDATED = "user.updated"
    
    COMMENT_ADDED = "comment.added"
    COMMENT_UPDATED = "comment.updated"
    COMMENT_DELETED = "comment.deleted"
    
    NOTIFICATION_SENT = "notification.sent"
    
    CASE_UPDATED = "case.updated"
    CLIENT_UPDATED = "client.updated"


class RealtimeBroadcaster:
    """Handles real-time event broadcasting across the application."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._subscription_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Initialize Redis connection and start listening."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Start Redis subscription handler
            self._subscription_task = asyncio.create_task(self._subscription_handler())
            
            logger.info("RealtimeBroadcaster started")
            
        except Exception as e:
            logger.error(f"Failed to start RealtimeBroadcaster: {e}")
            # Continue without Redis - use in-memory only
    
    async def stop(self):
        """Stop the broadcaster and clean up resources."""
        if self._subscription_task:
            self._subscription_task.cancel()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("RealtimeBroadcaster stopped")
    
    async def _subscription_handler(self):
        """Handle incoming Redis pub/sub messages."""
        if not self.redis_client:
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("realtime_events")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._handle_redis_message(data)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in subscription handler: {e}")
    
    async def _handle_redis_message(self, message: Dict[str, Any]):
        """Process a message from Redis pub/sub."""
        event_type = message.get("event_type")
        data = message.get("data", {})
        
        if event_type:
            await self._trigger_handlers(event_type, data)
            
            # Also broadcast via WebSocket
            await connection_manager.broadcast_to_all(
                MessageType.SYSTEM_MESSAGE,
                {
                    "event_type": event_type,
                    "data": data
                }
            )
    
    async def _trigger_handlers(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event handlers."""
        handlers = self._event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def on_event(self, event_type: str):
        """Decorator to register event handlers."""
        def decorator(func: Callable):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func
        return decorator
    
    async def broadcast(
        self,
        event_type: BroadcastEvent,
        data: Dict[str, Any],
        user_ids: Optional[List[str]] = None,
        room_id: Optional[str] = None
    ):
        """
        Broadcast an event to WebSocket connections and Redis.
        
        Args:
            event_type: Type of event to broadcast
            data: Event data
            user_ids: Specific user IDs to target (optional)
            room_id: Specific room to target (optional)
        """
        message_data = {
            "event_type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast via WebSocket
        if user_ids:
            # Send to specific users
            for user_id in user_ids:
                await connection_manager.send_to_user(
                    user_id,
                    MessageType.SYSTEM_MESSAGE,
                    message_data
                )
        elif room_id:
            # Send to specific room
            await connection_manager.broadcast_to_room(
                room_id,
                MessageType.SYSTEM_MESSAGE,
                message_data
            )
        else:
            # Broadcast to all
            await connection_manager.broadcast_to_all(
                MessageType.SYSTEM_MESSAGE,
                message_data
            )
        
        # Broadcast via Redis for distributed systems
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    "realtime_events",
                    json.dumps(message_data)
                )
            except Exception as e:
                logger.error(f"Error publishing to Redis: {e}")
        
        # Trigger local handlers
        await self._trigger_handlers(event_type.value, data)
    
    # Convenience methods for common broadcasts
    
    async def broadcast_document_update(
        self,
        document_id: str,
        user_id: str,
        update_type: str = "updated",
        changes: Optional[Dict[str, Any]] = None
    ):
        """Broadcast document update event."""
        await self.broadcast(
            BroadcastEvent.DOCUMENT_UPDATED,
            {
                "document_id": document_id,
                "user_id": user_id,
                "update_type": update_type,
                "changes": changes or {}
            },
            room_id=f"document:{document_id}"
        )
    
    async def broadcast_user_update(
        self,
        user_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """Broadcast user update event."""
        await self.broadcast(
            BroadcastEvent.USER_UPDATED,
            {
                "user_id": user_id,
                "update_type": update_type,
                "data": data
            },
            user_ids=[user_id]
        )
    
    async def broadcast_comment(
        self,
        document_id: str,
        comment_id: str,
        user_id: str,
        action: str = "added",
        content: Optional[str] = None
    ):
        """Broadcast comment event."""
        await self.broadcast(
            BroadcastEvent.COMMENT_ADDED if action == "added" else BroadcastEvent.COMMENT_UPDATED,
            {
                "document_id": document_id,
                "comment_id": comment_id,
                "user_id": user_id,
                "action": action,
                "content": content
            },
            room_id=f"document:{document_id}"
        )
    
    async def broadcast_notification(
        self,
        user_id: str,
        notification: Dict[str, Any]
    ):
        """Broadcast notification to specific user."""
        await self.broadcast(
            BroadcastEvent.NOTIFICATION_SENT,
            {
                "user_id": user_id,
                "notification": notification
            },
            user_ids=[user_id]
        )
    
    async def broadcast_user_presence(
        self,
        user_id: str,
        status: str,
        room_id: Optional[str] = None
    ):
        """Broadcast user presence update."""
        event = BroadcastEvent.USER_JOINED if status == "online" else BroadcastEvent.USER_LEFT
        
        data = {
            "user_id": user_id,
            "status": status,
            "room_id": room_id
        }
        
        if room_id:
            await self.broadcast(event, data, room_id=room_id)
        else:
            await self.broadcast(event, data)


# Global broadcaster instance
broadcaster = RealtimeBroadcaster()


# Register default event handlers
@broadcaster.on_event(BroadcastEvent.DOCUMENT_UPDATED)
async def handle_document_update(data: Dict[str, Any]):
    """Handle document update events."""
    document_id = data.get("document_id")
    if document_id:
        # Notify all users viewing the document
        await connection_manager.broadcast_to_room(
            f"document:{document_id}",
            MessageType.DOCUMENT_UPDATE,
            data
        )


@broadcaster.on_event(BroadcastEvent.NOTIFICATION_SENT)
async def handle_notification(data: Dict[str, Any]):
    """Handle notification events."""
    user_id = data.get("user_id")
    notification_data = data.get("notification", {})
    
    if user_id:
        await connection_manager.send_to_user(
            user_id,
            MessageType.NOTIFICATION,
            notification_data
        )
