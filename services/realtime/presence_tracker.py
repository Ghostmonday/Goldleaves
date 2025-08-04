# services/realtime/presence_tracker.py
"""
User presence tracking service.
Tracks which users are online and where they are active.
Provides room-based presence information.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis

from .connection_manager import connection_manager, MessageType

logger = logging.getLogger(__name__)


class PresenceStatus(str, Enum):
    """User presence status options."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


class UserPresence:
    """Represents a user's presence information."""
    
    def __init__(
        self,
        user_id: str,
        status: PresenceStatus = PresenceStatus.ONLINE,
        last_seen: Optional[datetime] = None,
        active_rooms: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.status = status
        self.last_seen = last_seen or datetime.utcnow()
        self.active_rooms = active_rooms or set()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
            "active_rooms": List[Any](self.active_rooms),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPresence":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            status=PresenceStatus(data["status"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            active_rooms=set(data.get("active_rooms", [])),
            metadata=data.get("metadata", {})
        )
    
    def update_activity(self):
        """Update last seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    def join_room(self, room_id: str):
        """Add user to a room."""
        self.active_rooms.add(room_id)
        self.update_activity()
    
    def leave_room(self, room_id: str):
        """Remove user from a room."""
        self.active_rooms.discard(room_id)
        self.update_activity()
    
    def is_active(self, timeout_minutes: int = 5) -> bool:
        """Check if user is considered active."""
        if self.status == PresenceStatus.OFFLINE:
            return False
        
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.last_seen < timeout


class PresenceTracker:
    """Manages user presence across the application."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._presence_cache: Dict[str, UserPresence] = {}
        self._room_members: Dict[str, Set[str]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Initialize the presence tracker."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_users())
            
            logger.info("PresenceTracker started")
            
        except Exception as e:
            logger.error(f"Failed to start PresenceTracker: {e}")
            # Continue without Redis - use in-memory only
    
    async def stop(self):
        """Stop the presence tracker."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("PresenceTracker stopped")
    
    async def _cleanup_inactive_users(self):
        """Background task to clean up inactive users."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._remove_inactive_users()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in presence cleanup: {e}")
    
    async def _remove_inactive_users(self, timeout_minutes: int = 10):
        """Remove users who have been inactive for too long."""
        current_time = datetime.utcnow()
        inactive_users = []
        
        for user_id, presence in self._presence_cache.items():
            if current_time - presence.last_seen > timedelta(minutes=timeout_minutes):
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            await self.set_user_offline(user_id)
    
    async def _get_redis_key(self, user_id: str) -> str:
        """Get Redis key for user presence."""
        return f"presence:{user_id}"
    
    async def _get_room_key(self, room_id: str) -> str:
        """Get Redis key for room members."""
        return f"room:members:{room_id}"
    
    async def _save_to_redis(self, user_id: str, presence: UserPresence):
        """Save presence to Redis."""
        if not self.redis_client:
            return
        
        try:
            key = await self._get_redis_key(user_id)
            await self.redis_client.setex(
                key,
                timedelta(hours=1),  # Expire after 1 hour
                json.dumps(presence.to_dict())
            )
        except Exception as e:
            logger.error(f"Error saving presence to Redis: {e}")
    
    async def _load_from_redis(self, user_id: str) -> Optional[UserPresence]:
        """Load presence from Redis."""
        if not self.redis_client:
            return None
        
        try:
            key = await self._get_redis_key(user_id)
            data = await self.redis_client.get(key)
            if data:
                return UserPresence.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Error loading presence from Redis: {e}")
        
        return None
    
    async def set_user_online(
        self,
        user_id: str,
        status: PresenceStatus = PresenceStatus.ONLINE,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Set user as online."""
        # Load existing presence or create new
        presence = self._presence_cache.get(user_id)
        if not presence:
            presence = await self._load_from_redis(user_id)
        
        if not presence:
            presence = UserPresence(user_id, status, metadata=metadata)
        else:
            presence.status = status
            presence.update_activity()
            if metadata:
                presence.metadata.update(metadata)
        
        self._presence_cache[user_id] = presence
        await self._save_to_redis(user_id, presence)
        
        # Broadcast presence update
        await self._broadcast_presence_update(user_id, presence)
    
    async def set_user_offline(self, user_id: str):
        """Set user as offline."""
        presence = self._presence_cache.get(user_id)
        if not presence:
            presence = await self._load_from_redis(user_id)
        
        if presence:
            # Remove from all rooms
            for room_id in list(presence.active_rooms):
                await self.leave_room(user_id, room_id)
            
            presence.status = PresenceStatus.OFFLINE
            presence.update_activity()
            
            await self._save_to_redis(user_id, presence)
            await self._broadcast_presence_update(user_id, presence)
            
            # Remove from cache after a delay
            if user_id in self._presence_cache:
                del self._presence_cache[user_id]
    
    async def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp."""
        presence = self._presence_cache.get(user_id)
        if not presence:
            presence = await self._load_from_redis(user_id)
        
        if presence:
            presence.update_activity()
            self._presence_cache[user_id] = presence
            await self._save_to_redis(user_id, presence)
    
    async def join_room(self, user_id: str, room_id: str):
        """Add user to a room."""
        presence = self._presence_cache.get(user_id)
        if not presence:
            presence = await self._load_from_redis(user_id)
        
        if not presence:
            # Create presence if user is joining a room
            await self.set_user_online(user_id)
            presence = self._presence_cache[user_id]
        
        presence.join_room(room_id)
        await self._save_to_redis(user_id, presence)
        
        # Update room members
        if room_id not in self._room_members:
            self._room_members[room_id] = set()
        self._room_members[room_id].add(user_id)
        
        # Update Redis room members
        if self.redis_client:
            try:
                room_key = await self._get_room_key(room_id)
                await self.redis_client.sadd(room_key, user_id)
                await self.redis_client.expire(room_key, timedelta(hours=1))
            except Exception as e:
                logger.error(f"Error updating room members in Redis: {e}")
        
        # Broadcast to room
        await self._broadcast_room_update(room_id, user_id, "joined")
    
    async def leave_room(self, user_id: str, room_id: str):
        """Remove user from a room."""
        presence = self._presence_cache.get(user_id)
        if presence:
            presence.leave_room(room_id)
            await self._save_to_redis(user_id, presence)
        
        # Update room members
        if room_id in self._room_members:
            self._room_members[room_id].discard(user_id)
            if not self._room_members[room_id]:
                del self._room_members[room_id]
        
        # Update Redis room members
        if self.redis_client:
            try:
                room_key = await self._get_room_key(room_id)
                await self.redis_client.srem(room_key, user_id)
            except Exception as e:
                logger.error(f"Error removing from room in Redis: {e}")
        
        # Broadcast to room
        await self._broadcast_room_update(room_id, user_id, "left")
    
    async def get_user_presence(self, user_id: str) -> Optional[UserPresence]:
        """Get user's current presence."""
        presence = self._presence_cache.get(user_id)
        if not presence:
            presence = await self._load_from_redis(user_id)
            if presence:
                self._presence_cache[user_id] = presence
        
        return presence
    
    async def get_room_members(self, room_id: str) -> List[Dict[str, Any]]:
        """Get all members in a room with their presence."""
        members = []
        
        # Get from cache first
        user_ids = self._room_members.get(room_id, set())
        
        # Also check Redis if available
        if self.redis_client:
            try:
                room_key = await self._get_room_key(room_id)
                redis_members = await self.redis_client.smembers(room_key)
                user_ids.update(redis_members)
            except Exception as e:
                logger.error(f"Error getting room members from Redis: {e}")
        
        for user_id in user_ids:
            presence = await self.get_user_presence(user_id)
            if presence and presence.is_active():
                members.append(presence.to_dict())
        
        return members
    
    async def get_online_users(self) -> List[Dict[str, Any]]:
        """Get all online users."""
        online_users = []
        
        for presence in self._presence_cache.values():
            if presence.status != PresenceStatus.OFFLINE and presence.is_active():
                online_users.append(presence.to_dict())
        
        return online_users
    
    async def _broadcast_presence_update(self, user_id: str, presence: UserPresence):
        """Broadcast presence update to relevant rooms."""
        presence_data = {
            "user_id": user_id,
            "status": presence.status.value,
            "last_seen": presence.last_seen.isoformat(),
            "metadata": presence.metadata
        }
        
        # Broadcast to all rooms the user is in
        for room_id in presence.active_rooms:
            await connection_manager.broadcast_to_room(
                room_id,
                MessageType.PRESENCE_UPDATE,
                presence_data
            )
        
        # Also send to user's personal channel
        await connection_manager.send_to_user(
            user_id,
            MessageType.PRESENCE_UPDATE,
            presence_data
        )
    
    async def _broadcast_room_update(self, room_id: str, user_id: str, action: str):
        """Broadcast room membership update."""
        await connection_manager.broadcast_to_room(
            room_id,
            MessageType.ROOM_UPDATE,
            {
                "room_id": room_id,
                "user_id": user_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Global presence tracker instance
presence_tracker = PresenceTracker()
