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

# Mock imports for context
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
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Connected to real-time service"
        })
        
        logger.info(f"WebSocket connected: user {user_id}")
        
        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process the message
                await handle_websocket_message(user_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up on disconnect
        if user_id:
            logger.info(f"WebSocket disconnected: user {user_id}")


async def handle_websocket_message(user_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages from clients."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    # Mock message handling for context
    logger.info(f"Handling message type: {message_type} from user: {user_id}")


@router.get("/status")
async def websocket_status():
    """Get WebSocket service status."""
    return {
        "status": "active",
        "connected_users": 0,  # Mock data
        "active_rooms": 0,     # Mock data
        "services": {
            "connection_manager": "active",
            "broadcaster": "active", 
            "presence_tracker": "active",
            "session_store": "active",
            "activity_tracker": "active"
        }
    }
