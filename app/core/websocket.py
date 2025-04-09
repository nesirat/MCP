from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        await websocket.accept()
        
        # Add to channel connections
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        
        # Add to user connections if user_id provided
        if user_id is not None:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        # Remove from channel connections
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        
        # Remove from user connections
        if user_id is not None and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def broadcast(self, channel: str, message: Any):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        message_data = {
            "type": "broadcast",
            "channel": channel,
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message_data)
            except:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, channel)

    async def send_to_user(self, user_id: int, message: Any):
        """Send message to specific user's connections"""
        if user_id not in self.user_connections:
            return
        
        message_data = {
            "type": "direct",
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message_data)
            except:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, "user", user_id)

    async def handle_connection(self, websocket: WebSocket, channel: str, user_id: Optional[int] = None):
        """Handle WebSocket connection lifecycle"""
        await self.connect(websocket, channel, user_id)
        try:
            while True:
                # Keep connection alive
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except:
            await self.disconnect(websocket, channel, user_id)


# Create a singleton instance
websocket_manager = WebSocketManager() 