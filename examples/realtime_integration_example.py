# examples/realtime_integration_example.py
"""
Example integration of real-time services with FastAPI application.
Shows how to integrate all Phase 11 real-time features.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers
from routers.websocket import router as websocket_router
from routers.api.v2.frontend_sync import router as frontend_router

# Import real-time services
from services.realtime.startup import startup_event, shutdown_event, service_manager

# Create FastAPI app
app = FastAPI(
    title="Goldleaves Legal Platform",
    description="Enhanced with real-time features",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add event handlers
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Include routers
app.include_router(frontend_router, prefix="/api/v2")
app.include_router(websocket_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Application health check."""
    realtime_health = await service_manager.health_check()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": {
            "frontend_api": "enabled",
            "realtime_websocket": "enabled",
            "presence_tracking": "enabled", 
            "session_management": "enabled",
            "activity_tracking": "enabled",
            "real_time_broadcasting": "enabled"
        },
        "realtime_services": realtime_health
    }


# Example endpoint that uses real-time features
@app.post("/api/v2/documents/{document_id}/update")
async def update_document(document_id: str, updates: Dict[str, Any]):
    """Example endpoint that triggers real-time updates."""
    from services.realtime import broadcaster, activity_tracker
    
    # Simulate document update
    # ... perform actual document update logic ...
    
    # Broadcast the update to users viewing this document
    await broadcaster.broadcast_document_update(
        document_id=document_id,
        user_id="current_user_id",  # Get from auth
        update_type="content_changed",
        changes=updates
    )
    
    # Track the activity
    await activity_tracker.track_document_activity(
        user_id="current_user_id",
        document_id=document_id,
        action="edit",
        metadata={"changes": List[Any](updates.keys())}
    )
    
    return {"status": "updated", "document_id": document_id}


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "realtime_integration_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
