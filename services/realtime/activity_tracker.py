# services/realtime/activity_tracker.py
"""
User activity tracking and analytics.
Tracks user interactions, page views, and feature usage.
Provides insights into user behavior patterns.
"""

from __future__ import annotations
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque


try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    import redis
    redis.asyncio = redis

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of user activities."""
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_EDIT = "document_edit"
    DOCUMENT_SAVE = "document_save"
    SEARCH_QUERY = "search_query"
    FILTER_APPLY = "filter_apply"
    EXPORT_DATA = "export_data"
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    ERROR_OCCURRED = "error_occurred"
    FEATURE_USED = "feature_used"


class ActivityEvent:
    """Represents a user activity event."""
    
    def __init__(
        self,
        user_id: str,
        activity_type: ActivityType,
        timestamp: Optional[datetime] = None,
        page: Optional[str] = None,
        element: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        self.user_id = user_id
        self.activity_type = activity_type
        self.timestamp = timestamp or datetime.utcnow()
        self.page = page
        self.element = element
        self.metadata = metadata or {}
        self.session_id = session_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "activity_type": self.activity_type.value,
            "timestamp": self.timestamp.isoformat(),
            "page": self.page,
            "element": self.element,
            "metadata": self.metadata,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityEvent":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            activity_type=ActivityType(data["activity_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            page=data.get("page"),
            element=data.get("element"),
            metadata=data.get("metadata", {}),
            session_id=data.get("session_id")
        )


class UserAnalytics:
    """User analytics data."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.total_events = 0
        self.last_activity = None
        self.pages_visited = set()
        self.features_used = set()
        self.session_duration = timedelta()
        self.activity_counts = defaultdict(int)
        self.daily_activity = defaultdict(int)
    
    def add_event(self, event: ActivityEvent):
        """Add an activity event to analytics."""
        self.total_events += 1
        self.last_activity = event.timestamp
        
        if event.page:
            self.pages_visited.add(event.page)
        
        if event.activity_type == ActivityType.FEATURE_USED and event.element:
            self.features_used.add(event.element)
        
        self.activity_counts[event.activity_type.value] += 1
        
        # Daily activity
        day_key = event.timestamp.date().isoformat()
        self.daily_activity[day_key] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "total_events": self.total_events,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "pages_visited": list(self.pages_visited),
            "features_used": list(self.features_used),
            "session_duration": self.session_duration.total_seconds(),
            "activity_counts": dict(self.activity_counts),
            "daily_activity": dict(self.daily_activity)
        }


class ActivityTracker:
    """Tracks and analyzes user activity across the application."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._activity_buffer: deque = deque(maxlen=1000)  # Buffer recent events
        self._user_analytics: Dict[str, UserAnalytics] = {}
        self._flush_task: Optional[asyncio.Task] = None
        self._analytics_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Initialize the activity tracker."""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Start background tasks
            self._flush_task = asyncio.create_task(self._flush_activities())
            self._analytics_task = asyncio.create_task(self._update_analytics())
            
            logger.info("ActivityTracker started")
            
        except Exception as e:
            logger.error(f"Failed to start ActivityTracker: {e}")
            # Continue without Redis - use in-memory only
    
    async def stop(self):
        """Stop the activity tracker."""
        if self._flush_task:
            self._flush_task.cancel()
        
        if self._analytics_task:
            self._analytics_task.cancel()
        
        # Flush remaining activities
        await self._flush_buffer()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("ActivityTracker stopped")
    
    async def _flush_activities(self):
        """Background task to flush activity buffer to Redis."""
        while True:
            try:
                await asyncio.sleep(30)  # Flush every 30 seconds
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error flushing activities: {e}")
    
    async def _update_analytics(self):
        """Background task to update user analytics."""
        while True:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                await self._update_user_analytics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating analytics: {e}")
    
    async def _flush_buffer(self):
        """Flush activity buffer to Redis."""
        if not self.redis_client or not self._activity_buffer:
            return
        
        try:
            # Batch activities by date for efficient storage
            activities_by_date = defaultdict(list)
            
            while self._activity_buffer:
                event = self._activity_buffer.popleft()
                date_key = event.timestamp.date().isoformat()
                activities_by_date[date_key].append(event.to_dict())
            
            # Store in Redis
            for date_key, activities in activities_by_date.items():
                redis_key = f"activities:{date_key}"
                for activity in activities:
                    await self.redis_client.lpush(redis_key, json.dumps(activity))
                
                # Set expiration (keep for 30 days)
                await self.redis_client.expire(redis_key, timedelta(days=30))
            
        except Exception as e:
            logger.error(f"Error flushing to Redis: {e}")
    
    async def _update_user_analytics(self):
        """Update user analytics from recent activities."""
        for user_id, analytics in self._user_analytics.items():
            if self.redis_client:
                try:
                    analytics_key = f"analytics:{user_id}"
                    await self.redis_client.setex(
                        analytics_key,
                        timedelta(days=7),
                        json.dumps(analytics.to_dict())
                    )
                except Exception as e:
                    logger.error(f"Error saving analytics for user {user_id}: {e}")
    
    async def track_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        page: Optional[str] = None,
        element: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """Track a user activity event."""
        event = ActivityEvent(
            user_id=user_id,
            activity_type=activity_type,
            page=page,
            element=element,
            metadata=metadata,
            session_id=session_id
        )
        
        # Add to buffer
        self._activity_buffer.append(event)
        
        # Update user analytics
        if user_id not in self._user_analytics:
            self._user_analytics[user_id] = UserAnalytics(user_id)
        
        self._user_analytics[user_id].add_event(event)
        
        logger.debug(f"Tracked activity: {user_id} - {activity_type.value}")
    
    # Convenience methods for common activities
    
    async def track_page_view(
        self,
        user_id: str,
        page: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a page view."""
        await self.track_activity(
            user_id=user_id,
            activity_type=ActivityType.PAGE_VIEW,
            page=page,
            session_id=session_id,
            metadata=metadata
        )
    
    async def track_button_click(
        self,
        user_id: str,
        element: str,
        page: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a button click."""
        await self.track_activity(
            user_id=user_id,
            activity_type=ActivityType.BUTTON_CLICK,
            page=page,
            element=element,
            session_id=session_id,
            metadata=metadata
        )
    
    async def track_document_activity(
        self,
        user_id: str,
        document_id: str,
        action: str,  # "open", "edit", "save"
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track document-related activity."""
        activity_map = {
            "open": ActivityType.DOCUMENT_OPEN,
            "edit": ActivityType.DOCUMENT_EDIT,
            "save": ActivityType.DOCUMENT_SAVE
        }
        
        activity_type = activity_map.get(action, ActivityType.DOCUMENT_EDIT)
        
        await self.track_activity(
            user_id=user_id,
            activity_type=activity_type,
            session_id=session_id,
            metadata={
                "document_id": document_id,
                "action": action,
                **(metadata or {})
            }
        )
    
    async def track_search(
        self,
        user_id: str,
        query: str,
        results_count: int,
        page: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Track a search query."""
        await self.track_activity(
            user_id=user_id,
            activity_type=ActivityType.SEARCH_QUERY,
            page=page,
            session_id=session_id,
            metadata={
                "query": query,
                "results_count": results_count
            }
        )
    
    async def track_error(
        self,
        user_id: str,
        error_type: str,
        error_message: str,
        page: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Track an error occurrence."""
        await self.track_activity(
            user_id=user_id,
            activity_type=ActivityType.ERROR_OCCURRED,
            page=page,
            session_id=session_id,
            metadata={
                "error_type": error_type,
                "error_message": error_message
            }
        )
    
    async def get_user_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific user."""
        # Check in-memory first
        if user_id in self._user_analytics:
            return self._user_analytics[user_id].to_dict()
        
        # Load from Redis
        if self.redis_client:
            try:
                analytics_key = f"analytics:{user_id}"
                data = await self.redis_client.get(analytics_key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Error loading analytics from Redis: {e}")
        
        return None
    
    async def get_activity_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity statistics for a date range."""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=7)
        if not date_to:
            date_to = datetime.utcnow()
        
        stats = {
            "total_events": 0,
            "unique_users": set(),
            "activity_types": defaultdict(int),
            "daily_stats": defaultdict(int),
            "popular_pages": defaultdict(int),
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            }
        }
        
        # Collect from in-memory analytics
        for analytics in self._user_analytics.values():
            stats["unique_users"].add(analytics.user_id)
            
            for activity_type, count in analytics.activity_counts.items():
                stats["activity_types"][activity_type] += count
                stats["total_events"] += count
            
            for page in analytics.pages_visited:
                stats["popular_pages"][page] += 1
        
        # Convert sets to counts
        stats["unique_users"] = len(stats["unique_users"])
        stats["activity_types"] = dict(stats["activity_types"])
        stats["popular_pages"] = dict(stats["popular_pages"])
        stats["daily_stats"] = dict(stats["daily_stats"])
        
        return stats
    
    async def get_user_activity_history(
        self,
        user_id: str,
        limit: int = 100,
        activity_types: Optional[List[ActivityType]] = None
    ) -> List[Dict[str, Any]]:
        """Get recent activity history for a user."""
        activities = []
        
        if not self.redis_client:
            return activities
        
        try:
            # Get activities from the last few days
            for days_back in range(7):  # Look back 7 days
                date = datetime.utcnow().date() - timedelta(days=days_back)
                date_key = date.isoformat()
                redis_key = f"activities:{date_key}"
                
                # Get all activities for this date
                activity_data = await self.redis_client.lrange(redis_key, 0, -1)
                
                for data in activity_data:
                    try:
                        activity_dict = json.loads(data)
                        if activity_dict["user_id"] == user_id:
                            # Filter by activity types if specified
                            if activity_types:
                                activity_type = ActivityType(activity_dict["activity_type"])
                                if activity_type not in activity_types:
                                    continue
                            
                            activities.append(activity_dict)
                            
                            if len(activities) >= limit:
                                break
                    except Exception as e:
                        logger.error(f"Error parsing activity data: {e}")
                
                if len(activities) >= limit:
                    break
            
            # Sort by timestamp (newest first)
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting user activity history: {e}")
        
        return activities[:limit]


# Global activity tracker instance
activity_tracker = ActivityTracker()
