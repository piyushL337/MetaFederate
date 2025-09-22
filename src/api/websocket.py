"""
MetaFederate WebSocket Manager
Real-time communication for live updates and notifications.

Key Responsibilities:
- Real-time messaging
- Live notifications
- Presence tracking
- Connection management

Author: Piyush Joshi (https://github.com/piyushL337/MetaFederate)
License: MIT
"""

import asyncio
import json
import logging
from typing import Dict, Any, Set, Optional
from aiohttp import web, WSMsgType
from ..core.config import Config
from ..core.database import Database

class WebSocketManager:
    """WebSocket connection management for real-time features."""
    
    def __init__(self, db: Database):
        self.db = db
        self.connections: Dict[str, Set[web.WebSocketResponse]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        user_id = request.get('user_id')
        if not user_id:
            await ws.close(code=1008, message='Authentication required')
            return ws
        
        # Add connection to user's connection set
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.handle_message(user_id, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f'WebSocket error: {ws.exception()}')
        
        finally:
            # Remove connection when done
            if user_id in self.connections:
                self.connections[user_id].discard(ws)
                if not self.connections[user_id]:
                    del self.connections[user_id]
        
        return ws
    
    async def handle_message(self, user_id: str, message: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send_to_user(user_id, {'type': 'pong'})
            elif message_type == 'subscribe':
                await self.handle_subscription(user_id, data)
            elif message_type == 'message':
                await self.handle_chat_message(user_id, data)
                
        except json.JSONDecodeError:
            self.logger.error('Invalid JSON message')
        except Exception as e:
            self.logger.error(f'Error handling message: {e}')
    
    async def handle_subscription(self, user_id: str, data: Dict[str, Any]) -> None:
        """Handle subscription requests."""
        channel = data.get('channel')
        if channel in ['notifications', 'messages', 'updates']:
            # Store subscription in database
            await self.db.execute(
                """INSERT INTO websocket_subscriptions 
                (user_id, channel, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, channel) 
                DO UPDATE SET created_at = $3""",
                user_id, channel, asyncio.get_event_loop().time()
            )
    
    async def handle_chat_message(self, user_id: str, data: Dict[str, Any]) -> None:
        """Handle real-time chat messages."""
        # This would integrate with the messaging system
        pass
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific user's connections."""
        if user_id not in self.connections:
            return False
        
        message_json = json.dumps(message)
        successful = 0
        
        for ws in list(self.connections[user_id]):
            try:
                await ws.send_str(message_json)
                successful += 1
            except Exception as e:
                self.logger.error(f'Error sending to WebSocket: {e}')
                self.connections[user_id].discard(ws)
        
        return successful > 0
    
    async def broadcast(self, message: Dict[str, Any], 
                       channel: Optional[str] = None) -> int:
        """Broadcast message to all connections or specific channel."""
        message_json = json.dumps(message)
        successful = 0
        
        for user_id, connections in list(self.connections.items()):
            for ws in list(connections):
                try:
                    await ws.send_str(message_json)
                    successful += 1
                except Exception as e:
                    self.logger.error(f'Error broadcasting to WebSocket: {e}')
                    connections.discard(ws)
        
        return successful
    
    async def notify_user(self, user_id: str, 
                         notification_type: str,
                         data: Dict[str, Any]) -> bool:
        """Send notification to user."""
        message = {
            'type': 'notification',
            'notification_type': notification_type,
            'data': data,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        return await self.send_to_user(user_id, message)
    
    async def notify_new_message(self, user_id: str, 
                               message_data: Dict[str, Any]) -> bool:
        """Notify user of new message."""
        return await self.notify_user(
            user_id,
            'new_message',
            message_data
        )
    
    async def notify_new_interaction(self, user_id: str,
                                   interaction_type: str,
                                   content_id: str,
                                   from_user: str) -> bool:
        """Notify user of new interaction (like, comment, etc.)."""
        return await self.notify_user(
            user_id,
            'new_interaction',
            {
                'type': interaction_type,
                'content_id': content_id,
                'from_user': from_user
            }
        )
