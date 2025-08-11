# services/realtime/connection_manager.py
"""
WebSocket connection manager for real-time communication.
Handles WebSocket connections, disconnections, and message broadcasting.
"""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
import logging
from enum import Enum


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    DOCUMENT_UPDATE = "document_update"
    USER_PRESENCE = "user_presence"
    NOTIFICATION = "notification"
    CHAT_MESSAGE = "chat_message"
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class WebSocketConnection:
    """Represents a single WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data to the WebSocket."""
        try:
            if self.state == ConnectionState.CONNECTED:
                await self.websocket.send_json(data)
                return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.connection_id}: {e}")
            self.state = ConnectionState.DISCONNECTED
        return False
    
    async def send_text(self, text: str) -> bool:
        """Send text data to the WebSocket."""
        try:
            if self.state == ConnectionState.CONNECTED:
                await self.websocket.send_text(text)
                return True
        except Exception as e:
            logger.error(f"Failed to send text to {self.connection_id}: {e}")
            self.state = ConnectionState.DISCONNECTED
        return False
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def is_alive(self, timeout_seconds: int = 60) -> bool:
        """Check if connection is still alive based on heartbeat."""
        time_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return time_since_heartbeat < timeout_seconds


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Connection storage
        self._connections: Dict[str, WebSocketConnection] = {}
        self._user_connections: Dict[str, Set[str]] = {}
        self._room_connections: Dict[str, Set[str]] = {}
        
        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60   # seconds
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background tasks."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("ConnectionManager started")
    
    async def stop(self):
        """Stop background tasks."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all connections
        for connection in list(self._connections.values()):
            await self.disconnect(connection.connection_id)
        
        logger.info("ConnectionManager stopped")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WebSocketConnection:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket instance
            user_id: ID of the connecting user
            connection_id: Unique connection ID
            metadata: Optional connection metadata
            
        Returns:
            WebSocketConnection instance
        """
        await websocket.accept()
        
        # Create connection
        connection = WebSocketConnection(websocket, user_id, connection_id)
        connection.state = ConnectionState.CONNECTED
        if metadata:
            connection.metadata = metadata
        
        # Store connection
        self._connections[connection_id] = connection
        
        # Track user connections
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)
        
        # Send welcome message
        await connection.send_json({
            "type": MessageType.CONNECT,
            "data": {
                "connection_id": connection_id,
                "user_id": user_id,
                "connected_at": connection.connected_at.isoformat(),
                "server_time": datetime.utcnow().isoformat()
            }
        })
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        
        # Broadcast user presence
        await self.broadcast_user_presence(user_id, "online")
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        # Update state
        connection.state = ConnectionState.DISCONNECTING
        
        # Remove from rooms
        for room_id in list(connection.subscriptions):
            await self.leave_room(connection_id, room_id)
        
        # Remove from user connections
        if connection.user_id in self._user_connections:
            self._user_connections[connection.user_id].discard(connection_id)
            if not self._user_connections[connection.user_id]:
                del self._user_connections[connection.user_id]
                # Broadcast user offline if no more connections
                await self.broadcast_user_presence(connection.user_id, "offline")
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket {connection_id}: {e}")
        
        # Remove connection
        del self._connections[connection_id]
        
        logger.info(f"Connection {connection_id} disconnected")
    
    async def join_room(self, connection_id: str, room_id: str):
        """
        Add a connection to a room for targeted broadcasting.
        
        Args:
            connection_id: ID of the connection
            room_id: ID of the room to join
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        # Add to room
        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(connection_id)
        
        # Track subscription
        connection.subscriptions.add(room_id)
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
    
    async def leave_room(self, connection_id: str, room_id: str):
        """
        Remove a connection from a room.
        
        Args:
            connection_id: ID of the connection
            room_id: ID of the room to leave
        """
        connection = self._connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(room_id)
        
        if room_id in self._room_connections:
            self._room_connections[room_id].discard(connection_id)
            if not self._room_connections[room_id]:
                del self._room_connections[room_id]
        
        logger.info(f"Connection {connection_id} left room {room_id}")
    
    async def send_to_user(
        self,
        user_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: ID of the target user
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of connections the message was sent to
        """
        connection_ids = self._user_connections.get(user_id, set())
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(connection_ids):
            connection = self._connections.get(connection_id)
            if connection and await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message_type: MessageType,
        data: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all connections in a room.
        
        Args:
            room_id: ID of the room
            message_type: Type of message
            data: Message data
            exclude_connection: Optional connection ID to exclude
            
        Returns:
            Number of connections the message was sent to
        """
        connection_ids = self._room_connections.get(room_id, set())
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id in list(connection_ids):
            if connection_id == exclude_connection:
                continue
            
            connection = self._connections.get(connection_id)
            if connection and await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(
        self,
        message_type: MessageType,
        data: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message_type: Type of message
            data: Message data
            exclude_connection: Optional connection ID to exclude
            
        Returns:
            Number of connections the message was sent to
        """
        sent_count = 0
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection_id, connection in list(self._connections.items()):
            if connection_id == exclude_connection:
                continue
            
            if await connection.send_json(message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_user_presence(self, user_id: str, status: str):
        """Broadcast user presence update."""
        await self.broadcast_to_all(
            MessageType.USER_PRESENCE,
            {
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ):
        """
        Handle incoming WebSocket message.
        
        Args:
            connection_id: ID of the sending connection
            message: The message data
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        message_type = message.get("type")
        data = message.get("data", {})
        
        # Handle different message types
        if message_type == MessageType.HEARTBEAT:
            connection.update_heartbeat()
            await connection.send_json({
                "type": MessageType.HEARTBEAT,
                "data": {"status": "ok"}
            })
        
        elif message_type == "join_room":
            room_id = data.get("room_id")
            if room_id:
                await self.join_room(connection_id, room_id)
        
        elif message_type == "leave_room":
            room_id = data.get("room_id")
            if room_id:
                await self.leave_room(connection_id, room_id)
        
        elif message_type == MessageType.CHAT_MESSAGE:
            room_id = data.get("room_id")
            if room_id and room_id in connection.subscriptions:
                await self.broadcast_to_room(
                    room_id,
                    MessageType.CHAT_MESSAGE,
                    {
                        "user_id": connection.user_id,
                        "message": data.get("message"),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exclude_connection=connection_id
                )
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to all connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                dead_connections = []
                
                for connection_id, connection in list(self._connections.items()):
                    if not connection.is_alive(self.heartbeat_timeout):
                        dead_connections.append(connection_id)
                    else:
                        await connection.send_json({
                            "type": MessageType.HEARTBEAT,
                            "data": {"ping": True}
                        })
                
                # Remove dead connections
                for connection_id in dead_connections:
                    logger.warning(f"Connection {connection_id} timed out")
                    await self.disconnect(connection_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _cleanup_loop(self):
        """Periodic cleanup of stale connections and data."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up empty room mappings
                empty_rooms = [
                    room_id for room_id, connections in self._room_connections.items()
                    if not connections
                ]
                for room_id in empty_rooms:
                    del self._room_connections[room_id]
                
                # Log statistics
                logger.info(
                    f"ConnectionManager stats - "
                    f"Connections: {len(self._connections)}, "
                    f"Users: {len(self._user_connections)}, "
                    f"Rooms: {len(self._room_connections)}"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            "total_connections": len(self._connections),
            "unique_users": len(self._user_connections),
            "active_rooms": len(self._room_connections),
            "rooms_with_users": {
                room_id: len(connections)
                for room_id, connections in self._room_connections.items()
            }
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user."""
        return list(self._user_connections.get(user_id, set()))
    
    def get_room_connections(self, room_id: str) -> List[str]:
        """Get all connection IDs in a room."""
        return list(self._room_connections.get(room_id, set()))
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0


# Global connection manager instance
connection_manager = ConnectionManager()
