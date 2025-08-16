# services/realtime/session_store.py
"""
Frontend session management.
Stores user sessions with preferences and activity tracking.
Provides session persistence across browser refreshes.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user session with preferences and activity."""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        created_at: Optional[datetime] = None,
        last_activity: Optional[datetime] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.last_activity = last_activity or datetime.utcnow()
        self.preferences = preferences or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "preferences": self.preferences,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            preferences=data.get("preferences", {}),
            metadata=data.get("metadata", {})
        )

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences."""
        self.preferences.update(preferences)
        self.update_activity()

    def set_metadata(self, key: str, value: Any):
        """Set metadata value."""
        self.metadata[key] = value
        self.update_activity()

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Check if session is expired."""
        max_age = timedelta(hours=max_age_hours)
        return datetime.utcnow() - self.last_activity > max_age


class SessionStore:
    """Manages user sessions with Redis backing."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._session_cache: Dict[str, UserSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Initialize the session store."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

            logger.info("SessionStore started")

        except Exception as e:
            logger.error(f"Failed to start SessionStore: {e}")
            # Continue without Redis - use in-memory only

    async def stop(self):
        """Stop the session store."""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("SessionStore stopped")

    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._remove_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")

    async def _remove_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = []

        for session_id, session in self._session_cache.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.delete_session(session_id)

    async def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"session:{session_id}"

    async def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user sessions."""
        return f"user_sessions:{user_id}"

    async def _save_to_redis(self, session: UserSession):
        """Save session to Redis."""
        if not self.redis_client:
            return

        try:
            session_key = await self._get_session_key(session.session_id)
            await self.redis_client.setex(
                session_key,
                timedelta(hours=24),
                json.dumps(session.to_dict())
            )

            # Update user sessions list
            user_sessions_key = await self._get_user_sessions_key(session.user_id)
            await self.redis_client.sadd(user_sessions_key, session.session_id)
            await self.redis_client.expire(user_sessions_key, timedelta(hours=24))

        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")

    async def _load_from_redis(self, session_id: str) -> Optional[UserSession]:
        """Load session from Redis."""
        if not self.redis_client:
            return None

        try:
            session_key = await self._get_session_key(session_id)
            data = await self.redis_client.get(session_key)
            if data:
                return UserSession.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Error loading session from Redis: {e}")

        return None

    async def create_session(
        self,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Create a new user session."""
        session_id = str(uuid4())
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            preferences=preferences,
            metadata=metadata
        )

        # Store in cache
        self._session_cache[session_id] = session

        # Update user sessions mapping
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)

        # Save to Redis
        await self._save_to_redis(session)

        logger.info(f"Created session {session_id} for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        # Check cache first
        session = self._session_cache.get(session_id)
        if session:
            return session

        # Load from Redis
        session = await self._load_from_redis(session_id)
        if session:
            self._session_cache[session_id] = session

            # Update user sessions mapping
            if session.user_id not in self._user_sessions:
                self._user_sessions[session.user_id] = []
            if session_id not in self._user_sessions[session.user_id]:
                self._user_sessions[session.user_id].append(session_id)

        return session

    async def update_session_activity(self, session_id: str):
        """Update session last activity."""
        session = await self.get_session(session_id)
        if session:
            session.update_activity()
            await self._save_to_redis(session)

    async def update_session_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update session preferences."""
        session = await self.get_session(session_id)
        if session:
            session.update_preferences(preferences)
            await self._save_to_redis(session)
            return True
        return False

    async def set_session_metadata(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Set session metadata."""
        session = await self.get_session(session_id)
        if session:
            session.set_metadata(key, value)
            await self._save_to_redis(session)
            return True
        return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        # Get session first to find user_id
        session = await self.get_session(session_id)
        if not session:
            return False

        user_id = session.user_id

        # Remove from cache
        if session_id in self._session_cache:
            del self._session_cache[session_id]

        # Remove from user sessions mapping
        if user_id in self._user_sessions:
            if session_id in self._user_sessions[user_id]:
                self._user_sessions[user_id].remove(session_id)
            if not self._user_sessions[user_id]:
                del self._user_sessions[user_id]

        # Remove from Redis
        if self.redis_client:
            try:
                session_key = await self._get_session_key(session_id)
                await self.redis_client.delete(session_key)

                user_sessions_key = await self._get_user_sessions_key(user_id)
                await self.redis_client.srem(user_sessions_key, session_id)

            except Exception as e:
                logger.error(f"Error deleting session from Redis: {e}")

        logger.info(f"Deleted session {session_id} for user {user_id}")
        return True

    async def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all sessions for a user."""
        sessions = []

        # Get session IDs from mapping
        session_ids = self._user_sessions.get(user_id, [])

        # Also check Redis
        if self.redis_client:
            try:
                user_sessions_key = await self._get_user_sessions_key(user_id)
                redis_session_ids = await self.redis_client.smembers(user_sessions_key)
                session_ids.extend(redis_session_ids)
                session_ids = list(set(session_ids))  # Remove duplicates
            except Exception as e:
                logger.error(f"Error getting user sessions from Redis: {e}")

        # Load sessions
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session and not session.is_expired():
                sessions.append(session)

        return sessions

    async def cleanup_user_sessions(self, user_id: str, keep_latest: int = 5):
        """Clean up old sessions for a user, keeping only the most recent."""
        sessions = await self.get_user_sessions(user_id)

        if len(sessions) <= keep_latest:
            return

        # Sort by last activity (newest first)
        sessions.sort(key=lambda s: s.last_activity, reverse=True)

        # Delete old sessions
        for session in sessions[keep_latest:]:
            await self.delete_session(session.session_id)

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(self._session_cache)
        active_users = len(self._user_sessions)

        # Count recent sessions (last hour)
        recent_sessions = 0
        for session in self._session_cache.values():
            if datetime.utcnow() - session.last_activity < timedelta(hours=1):
                recent_sessions += 1

        return {
            "total_sessions": total_sessions,
            "active_users": active_users,
            "recent_sessions": recent_sessions,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global session store instance
session_store = SessionStore()
