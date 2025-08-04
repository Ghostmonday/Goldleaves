# services/realtime/startup.py
"""
Real-time services startup and lifecycle management.
Initializes and manages all real-time services.
"""

import asyncio
import logging
from typing import Optional

from .connection_manager import connection_manager
from .broadcaster import broadcaster
from .presence_tracker import presence_tracker
from .session_store import session_store
from .activity_tracker import activity_tracker

logger = logging.getLogger(__name__)


class RealtimeServiceManager:
    """Manages the lifecycle of all real-time services."""
    
    def __init__(self):
        self._started = False
        self._services = [
            ("broadcaster", broadcaster),
            ("presence_tracker", presence_tracker),
            ("session_store", session_store),
            ("activity_tracker", activity_tracker)
        ]
    
    async def start_all(self, redis_url: Optional[str] = None):
        """Start all real-time services."""
        if self._started:
            logger.warning("Real-time services already started")
            return
        
        logger.info("Starting real-time services...")
        
        # Update Redis URL if provided
        if redis_url:
            for service_name, service in self._services:
                if hasattr(service, 'redis_url'):
                    service.redis_url = redis_url
        
        # Start services
        start_tasks = []
        for service_name, service in self._services:
            if hasattr(service, 'start'):
                start_tasks.append(self._start_service(service_name, service))
        
        # Start all services concurrently
        if start_tasks:
            await asyncio.gather(*start_tasks, return_exceptions=True)
        
        self._started = True
        logger.info("All real-time services started successfully")
    
    async def _start_service(self, name: str, service):
        """Start a single service with error handling."""
        try:
            await service.start()
            logger.info(f"Started {name}")
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
    
    async def stop_all(self):
        """Stop all real-time services."""
        if not self._started:
            return
        
        logger.info("Stopping real-time services...")
        
        # Stop services
        stop_tasks = []
        for service_name, service in self._services:
            if hasattr(service, 'stop'):
                stop_tasks.append(self._stop_service(service_name, service))
        
        # Stop all services concurrently
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self._started = False
        logger.info("All real-time services stopped")
    
    async def _stop_service(self, name: str, service):
        """Stop a single service with error handling."""
        try:
            await service.stop()
            logger.info(f"Stopped {name}")
        except Exception as e:
            logger.error(f"Failed to stop {name}: {e}")
    
    def is_started(self) -> bool:
        """Check if services are started."""
        return self._started
    
    async def health_check(self) -> dict:
        """Perform health check on all services."""
        health = {
            "status": "healthy" if self._started else "stopped",
            "services": {}
        }
        
        for service_name, service in self._services:
            try:
                # Check if service has redis client and is connected
                if hasattr(service, 'redis_client') and service.redis_client:
                    # Try a simple Redis operation
                    await service.redis_client.ping()
                    health["services"][service_name] = "healthy"
                else:
                    health["services"][service_name] = "healthy_no_redis"
            except Exception as e:
                health["services"][service_name] = f"error: {str(e)}"
                health["status"] = "degraded"
        
        # Check connection manager
        health["services"]["connection_manager"] = {
            "status": "healthy",
            "connections": len(connection_manager._connections),
            "rooms": len(connection_manager._rooms)
        }
        
        return health


# Global service manager instance
service_manager = RealtimeServiceManager()


# FastAPI event handlers
async def startup_event():
    """FastAPI startup event handler."""
    await service_manager.start_all()


async def shutdown_event():
    """FastAPI shutdown event handler."""
    await service_manager.stop_all()


# Export for use in main app
__all__ = [
    "RealtimeServiceManager",
    "service_manager", 
    "startup_event",
    "shutdown_event"
]
