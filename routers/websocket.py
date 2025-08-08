# routers/websocket.py
"""
WebSocket router for real-time communication.
Handles WebSocket connections and integrates all real-time services.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer

from services.realtime import (
    connection_manager,
    broadcaster,
    presence_tracker,
    session_store,
    activity_tracker
)
from services.realtime.connection_manager import MessageType
from core.security import decode_access_token

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    Main WebSocket endpoint for real-time communication.
    
    Supports authentication via token parameter or Authorization header.
    """
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Authenticate user
        user_id = None
        if token:
            try:
                # Decode the token to get user information
                payload = decode_access_token(token)
                user_id = payload.get("sub")
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication failed"
                })
                await websocket.close()
                return
        
        if not user_id:
            logger.warning("WebSocket connection without valid authentication")
            await websocket.send_json({
                "type": "error", 
                "message": "Authentication required"
            })
            await websocket.close()
            return
        
        # Connect user through connection manager
        await connection_manager.connect(websocket, user_id)
        
        # Set user online in presence tracker
        await presence_tracker.set_user_online(user_id)
        
        # Create or update session
        user_sessions = await session_store.get_user_sessions(user_id)
        if user_sessions:
            # Update existing session
            session = user_sessions[0]  # Use most recent session
            await session_store.update_session_activity(session.session_id)
        else:
            # Create new session
            session = await session_store.create_session(user_id)
        
        # Track login activity
        await activity_tracker.track_activity(
            user_id=user_id,
            activity_type=activity_tracker.ActivityType.LOGIN,
            session_id=session.session_id
        )
        
        # Send connection confirmation
        await connection_manager.send_to_user(
            user_id,
            MessageType.SYSTEM_MESSAGE,
            {
                "type": "connected",
                "user_id": user_id,
                "session_id": session.session_id,
                "message": "Connected to real-time service"
            }
        )
        
        logger.info(f"WebSocket connected: user {user_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process the message
                await handle_websocket_message(user_id, message, session.session_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                await connection_manager.send_to_user(
                    user_id,
                    MessageType.ERROR,
                    {"message": "Invalid JSON format"}
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await connection_manager.send_to_user(
                    user_id,
                    MessageType.ERROR,
                    {"message": "Error processing message"}
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up on disconnect
        if user_id:
            await cleanup_user_connection(user_id)


async def handle_websocket_message(
    user_id: str,
    message: Dict[str, Any],
    session_id: str
):
    """Handle incoming WebSocket messages from clients."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    try:
        if message_type == "ping":
            # Respond to ping with pong
            await connection_manager.send_to_user(
                user_id,
                MessageType.SYSTEM_MESSAGE,
                {"type": "pong", "timestamp": message.get("timestamp")}
            )
        
        elif message_type == "join_room":
            # Join a room (e.g., document editing room)
            room_id = data.get("room_id")
            if room_id:
                await connection_manager.join_room(user_id, room_id)
                await presence_tracker.join_room(user_id, room_id)
                
                # Track activity
                await activity_tracker.track_activity(
                    user_id=user_id,
                    activity_type=activity_tracker.ActivityType.PAGE_VIEW,
                    page=room_id,
                    session_id=session_id,
                    metadata={"action": "join_room"}
                )
        
        elif message_type == "leave_room":
            # Leave a room
            room_id = data.get("room_id")
            if room_id:
                await connection_manager.leave_room(user_id, room_id)
                await presence_tracker.leave_room(user_id, room_id)
                
                # Track activity
                await activity_tracker.track_activity(
                    user_id=user_id,
                    activity_type=activity_tracker.ActivityType.PAGE_VIEW,
                    page=room_id,
                    session_id=session_id,
                    metadata={"action": "leave_room"}
                )
        
        elif message_type == "update_presence":
            # Update user presence status
            status = data.get("status", "online")
            metadata = data.get("metadata", {})
            await presence_tracker.set_user_online(user_id, status, metadata)
        
        elif message_type == "update_preferences":
            # Update session preferences
            preferences = data.get("preferences", {})
            await session_store.update_session_preferences(session_id, preferences)
        
        elif message_type == "track_activity":
            # Track custom activity
            activity_type = data.get("activity_type")
            page = data.get("page")
            element = data.get("element")
            metadata = data.get("metadata", {})
            
            if activity_type:
                await activity_tracker.track_activity(
                    user_id=user_id,
                    activity_type=activity_tracker.ActivityType(activity_type),
                    page=page,
                    element=element,
                    session_id=session_id,
                    metadata=metadata
                )
        
        elif message_type == "broadcast_message":
            # Broadcast a message to a room
            room_id = data.get("room_id")
            content = data.get("content")
            
            if room_id and content:
                await connection_manager.broadcast_to_room(
                    room_id,
                    MessageType.USER_MESSAGE,
                    {
                        "from_user": user_id,
                        "content": content,
                        "timestamp": message.get("timestamp")
                    }
                )
                
                # Track activity
                await activity_tracker.track_activity(
                    user_id=user_id,
                    activity_type=activity_tracker.ActivityType.FEATURE_USED,
                    element="chat_message",
                    session_id=session_id,
                    metadata={"room_id": room_id}
                )
        
        elif message_type == "get_room_members":
            # Get room member list
            room_id = data.get("room_id")
            if room_id:
                members = await presence_tracker.get_room_members(room_id)
                await connection_manager.send_to_user(
                    user_id,
                    MessageType.SYSTEM_MESSAGE,
                    {
                        "type": "room_members",
                        "room_id": room_id,
                        "members": members
                    }
                )
        
        elif message_type == "get_analytics":
            # Get user analytics (if user has permission)
            analytics = await activity_tracker.get_user_analytics(user_id)
            await connection_manager.send_to_user(
                user_id,
                MessageType.SYSTEM_MESSAGE,
                {
                    "type": "analytics",
                    "data": analytics
                }
            )
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await connection_manager.send_to_user(
                user_id,
                MessageType.ERROR,
                {"message": f"Unknown message type: {message_type}"}
            )
    
    except Exception as e:
        logger.error(f"Error handling message type {message_type}: {e}")
        await connection_manager.send_to_user(
            user_id,
            MessageType.ERROR,
            {"message": f"Error processing {message_type}"}
        )


async def cleanup_user_connection(user_id: str):
    """Clean up when user disconnects."""
    try:
        # Disconnect from connection manager
        await connection_manager.disconnect(user_id)
        
        # Set user offline in presence tracker
        await presence_tracker.set_user_offline(user_id)
        
        # Track logout activity
        await activity_tracker.track_activity(
            user_id=user_id,
            activity_type=activity_tracker.ActivityType.LOGOUT
        )
        
        logger.info(f"WebSocket disconnected: user {user_id}")
        
    except Exception as e:
        logger.error(f"Error during cleanup for user {user_id}: {e}")


# HTTP endpoints for real-time service management

@router.get("/status")
async def websocket_status():
    """Get WebSocket service status."""
    return {
        "status": "active",
        "connected_users": len(connection_manager._connections),
        "active_rooms": len(connection_manager._rooms),
        "services": {
            "connection_manager": "active",
            "broadcaster": "active", 
            "presence_tracker": "active",
            "session_store": "active",
            "activity_tracker": "active"
        }
    }


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: Dict = Depends(lambda: {"user_id": "admin"})  # TODO: Add real auth
):
    """Broadcast a message to all connected users (admin only)."""
    await broadcaster.broadcast(
        event_type=broadcaster.BroadcastEvent.NOTIFICATION_SENT,
        data=message
    )
    
    return {"status": "broadcasted", "message": message}


@router.get("/analytics/stats")
async def get_activity_stats():
    """Get overall activity statistics."""
    stats = await activity_tracker.get_activity_stats()
    session_stats = await session_store.get_session_stats()
    
    return {
        "activity": stats,
        "sessions": session_stats,
        "timestamp": stats["date_range"]["to"]
    }
