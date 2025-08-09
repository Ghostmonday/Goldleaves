"""
Core usage tracking module for recording usage events.
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from models.dependencies import SessionLocal
from models.usage_event import UsageEvent

logger = logging.getLogger(__name__)


class UsageTracker:
    """Core usage tracking service."""
    
    def __init__(self):
        self._active_events: Dict[str, UsageEvent] = {}
    
    async def record_usage(
        self,
        feature: str = "unknown",
        jurisdiction: str = "unknown",
        plan: str = "unknown",
        ai: bool = False,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Record a usage event with tags.
        
        Args:
            feature: Feature being used (default: "unknown")
            jurisdiction: Jurisdiction context (default: "unknown") 
            plan: Plan context (default: "unknown")
            ai: AI feature usage flag (default: False)
            event_type: Type of usage event
            user_id: User associated with the event
            request_id: Request ID for correlation
            metadata: Additional event metadata
            
        Returns:
            Event ID if successful, None if failed
        """
        try:
            usage_event = UsageEvent(
                feature=feature,
                jurisdiction=jurisdiction,
                plan=plan,
                ai=ai,
                event_type=event_type,
                user_id=user_id,
                request_id=request_id,
                metadata=metadata or {}
            )
            
            # Save to database
            with SessionLocal() as db:
                db.add(usage_event)
                db.commit()
                db.refresh(usage_event)
                
            logger.info(
                f"Recorded usage event: feature={feature}, jurisdiction={jurisdiction}, "
                f"plan={plan}, ai={ai}, event_id={usage_event.id}"
            )
            
            return str(usage_event.id)
            
        except Exception as e:
            logger.error(f"Failed to record usage event: {e}", exc_info=True)
            return None
    
    async def start_event(
        self,
        feature: str = "unknown",
        jurisdiction: str = "unknown",
        plan: str = "unknown",
        ai: bool = False,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Start a usage event (for tracking duration).
        
        Returns:
            Event ID if successful, None if failed
        """
        try:
            usage_event = UsageEvent(
                feature=feature,
                jurisdiction=jurisdiction,
                plan=plan,
                ai=ai,
                event_type=event_type,
                user_id=user_id,
                request_id=request_id,
                metadata=metadata or {}
            )
            
            # Store temporarily for finalization
            event_id = str(usage_event.id)
            self._active_events[event_id] = usage_event
            
            logger.debug(
                f"Started usage event: feature={feature}, jurisdiction={jurisdiction}, "
                f"plan={plan}, ai={ai}, event_id={event_id}"
            )
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to start usage event: {e}", exc_info=True)
            return None
    
    async def finalize_event(
        self,
        event_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Finalize a usage event (save to database).
        
        Args:
            event_id: ID of the event to finalize
            additional_metadata: Additional metadata to add
            
        Returns:
            True if successful, False if failed
        """
        try:
            if event_id not in self._active_events:
                logger.warning(f"Event {event_id} not found in active events")
                return False
                
            usage_event = self._active_events.pop(event_id)
            
            # Add additional metadata if provided
            if additional_metadata:
                if usage_event.metadata is None:
                    usage_event.metadata = {}
                usage_event.metadata.update(additional_metadata)
            
            # Save to database
            with SessionLocal() as db:
                db.add(usage_event)
                db.commit()
                db.refresh(usage_event)
                
            logger.info(
                f"Finalized usage event: feature={usage_event.feature}, "
                f"jurisdiction={usage_event.jurisdiction}, plan={usage_event.plan}, "
                f"ai={usage_event.ai}, event_id={event_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to finalize usage event {event_id}: {e}", exc_info=True)
            # Remove from active events even if save failed
            self._active_events.pop(event_id, None)
            return False


# Global instance
_usage_tracker = UsageTracker()


# Public API functions
async def record_usage(
    feature: str = "unknown",
    jurisdiction: str = "unknown",
    plan: str = "unknown",
    ai: bool = False,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Record a usage event with tags.
    
    Args:
        feature: Feature being used (default: "unknown")
        jurisdiction: Jurisdiction context (default: "unknown")
        plan: Plan context (default: "unknown") 
        ai: AI feature usage flag (default: False)
        event_type: Type of usage event
        user_id: User associated with the event
        request_id: Request ID for correlation
        metadata: Additional event metadata
        
    Returns:
        Event ID if successful, None if failed
    """
    return await _usage_tracker.record_usage(
        feature=feature,
        jurisdiction=jurisdiction,
        plan=plan,
        ai=ai,
        event_type=event_type,
        user_id=user_id,
        request_id=request_id,
        metadata=metadata
    )


async def start_event(
    feature: str = "unknown",
    jurisdiction: str = "unknown",
    plan: str = "unknown",
    ai: bool = False,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Start a usage event (for tracking duration).
    
    Returns:
        Event ID if successful, None if failed
    """
    return await _usage_tracker.start_event(
        feature=feature,
        jurisdiction=jurisdiction,
        plan=plan,
        ai=ai,
        event_type=event_type,
        user_id=user_id,
        request_id=request_id,
        metadata=metadata
    )


async def finalize_event(
    event_id: str,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Finalize a usage event (save to database).
    
    Args:
        event_id: ID of the event to finalize
        additional_metadata: Additional metadata to add
        
    Returns:
        True if successful, False if failed
    """
    return await _usage_tracker.finalize_event(event_id, additional_metadata)


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    return _usage_tracker