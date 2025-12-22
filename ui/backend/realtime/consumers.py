"""
Eye of God Realtime - WebSocket Consumers
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Channels implementation
- JWT authentication
- Redis channel layer
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import jwt
import os

LOGGER = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret')


class AuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    """
    Base WebSocket consumer with JWT authentication.
    
    All authenticated consumers should extend this class.
    """
    
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    
    async def connect(self):
        """Handle WebSocket connection with JWT auth."""
        # Extract token from query string
        query_string = self.scope.get('query_string', b'').decode()
        token = self._extract_token(query_string)
        
        if not token:
            await self.close(code=4001)
            return
        
        # Validate JWT
        user_data = self._validate_token(token)
        if not user_data:
            await self.close(code=4001)
            return
        
        self.user_id = user_data.get('sub')
        self.tenant_id = user_data.get('tenant_id')
        self.role = user_data.get('role', 'member')
        
        await self.accept()
        LOGGER.info(f"WebSocket connected: user={self.user_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        LOGGER.info(f"WebSocket disconnected: user={self.user_id}, code={close_code}")
    
    def _extract_token(self, query_string: str) -> Optional[str]:
        """Extract token from query string."""
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        return params.get('token')
    
    def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            LOGGER.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            LOGGER.warning(f"Invalid JWT token: {e}")
            return None


class EventsConsumer(AuthenticatedConsumer):
    """
    Real-time events consumer for tenant-wide events.
    
    Broadcasts events like:
    - settings.updated
    - theme.applied
    - mode.changed
    - memory.created
    """
    
    async def connect(self):
        """Connect and join tenant group."""
        await super().connect()
        
        if self.tenant_id:
            # Join tenant-specific group
            self.tenant_group = f"tenant_{self.tenant_id}"
            await self.channel_layer.group_add(
                self.tenant_group,
                self.channel_name
            )
            
            # Join user-specific group
            self.user_group = f"user_{self.user_id}"
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )
            
            # Send connection confirmation
            await self.send_json({
                "type": "connection.established",
                "user_id": self.user_id,
                "tenant_id": self.tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
            })
    
    async def disconnect(self, close_code):
        """Leave groups on disconnect."""
        if hasattr(self, 'tenant_group'):
            await self.channel_layer.group_discard(
                self.tenant_group,
                self.channel_name
            )
        
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        await super().disconnect(close_code)
    
    async def receive_json(self, content):
        """Handle incoming messages."""
        msg_type = content.get('type', '')
        
        if msg_type == 'ping':
            await self.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        elif msg_type == 'subscribe':
            # Subscribe to specific event types
            event_types = content.get('events', [])
            await self.send_json({
                "type": "subscribed",
                "events": event_types,
            })
        
        else:
            LOGGER.warning(f"Unknown message type: {msg_type}")
    
    # Event handlers - called when events are broadcast to groups
    
    async def settings_updated(self, event):
        """Handle settings.updated event."""
        await self.send_json({
            "type": "settings.updated",
            "tab": event.get("tab"),
            "version": event.get("version"),
            "timestamp": event.get("timestamp"),
        })
    
    async def theme_applied(self, event):
        """Handle theme.applied event."""
        await self.send_json({
            "type": "theme.applied",
            "theme_id": event.get("theme_id"),
            "theme_name": event.get("theme_name"),
            "user_id": event.get("user_id"),
            "timestamp": event.get("timestamp"),
        })
    
    async def mode_changed(self, event):
        """Handle mode.changed event."""
        await self.send_json({
            "type": "mode.changed",
            "mode": event.get("mode"),
            "user_id": event.get("user_id"),
            "timestamp": event.get("timestamp"),
        })
    
    async def memory_created(self, event):
        """Handle memory.created event."""
        await self.send_json({
            "type": "memory.created",
            "memory_id": event.get("memory_id"),
            "memory_type": event.get("memory_type"),
            "timestamp": event.get("timestamp"),
        })
    
    async def notification(self, event):
        """Handle generic notification event."""
        await self.send_json({
            "type": "notification",
            "level": event.get("level", "info"),
            "message": event.get("message"),
            "data": event.get("data"),
            "timestamp": event.get("timestamp"),
        })


class ChatConsumer(AuthenticatedConsumer):
    """
    Chat consumer for real-time AI conversations.
    
    Handles:
    - Message streaming
    - Tool calls
    - Memory updates
    """
    
    conversation_id: Optional[str] = None
    
    async def connect(self):
        """Connect and optionally join conversation."""
        await super().connect()
        
        if self.user_id:
            await self.send_json({
                "type": "chat.ready",
                "user_id": self.user_id,
            })
    
    async def receive_json(self, content):
        """Handle incoming chat messages."""
        msg_type = content.get('type', '')
        
        if msg_type == 'chat.message':
            await self._handle_chat_message(content)
        
        elif msg_type == 'chat.join':
            await self._handle_join_conversation(content)
        
        elif msg_type == 'chat.leave':
            await self._handle_leave_conversation(content)
        
        elif msg_type == 'chat.typing':
            await self._handle_typing(content)
        
        else:
            LOGGER.warning(f"Unknown chat message type: {msg_type}")
    
    async def _handle_chat_message(self, content):
        """Process incoming chat message and stream response."""
        message = content.get('message', '')
        conversation_id = content.get('conversation_id') or self.conversation_id
        
        if not message:
            return
        
        # Acknowledge message received
        await self.send_json({
            "type": "chat.received",
            "message_id": content.get('message_id'),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Stream response (placeholder - integrate with actual LLM)
        await self.send_json({
            "type": "chat.stream.start",
            "conversation_id": conversation_id,
        })
        
        # Simulated streaming response
        response_chunks = [
            "I understand ",
            "your request. ",
            "Let me help ",
            "you with that.",
        ]
        
        for chunk in response_chunks:
            await self.send_json({
                "type": "chat.stream.chunk",
                "content": chunk,
            })
        
        await self.send_json({
            "type": "chat.stream.end",
            "conversation_id": conversation_id,
        })
    
    async def _handle_join_conversation(self, content):
        """Join a conversation room."""
        conversation_id = content.get('conversation_id')
        
        if not conversation_id:
            return
        
        self.conversation_id = conversation_id
        self.conversation_group = f"conversation_{conversation_id}"
        
        await self.channel_layer.group_add(
            self.conversation_group,
            self.channel_name
        )
        
        await self.send_json({
            "type": "chat.joined",
            "conversation_id": conversation_id,
        })
    
    async def _handle_leave_conversation(self, content):
        """Leave current conversation room."""
        if hasattr(self, 'conversation_group'):
            await self.channel_layer.group_discard(
                self.conversation_group,
                self.channel_name
            )
        
        self.conversation_id = None
        
        await self.send_json({
            "type": "chat.left",
        })
    
    async def _handle_typing(self, content):
        """Broadcast typing indicator."""
        if hasattr(self, 'conversation_group'):
            await self.channel_layer.group_send(
                self.conversation_group,
                {
                    "type": "chat_typing",
                    "user_id": self.user_id,
                    "is_typing": content.get('is_typing', False),
                }
            )
    
    async def chat_typing(self, event):
        """Handle typing event from group."""
        if event.get('user_id') != self.user_id:
            await self.send_json({
                "type": "chat.typing",
                "user_id": event.get("user_id"),
                "is_typing": event.get("is_typing"),
            })
    
    async def chat_message(self, event):
        """Handle message broadcast from group."""
        await self.send_json({
            "type": "chat.message",
            "message": event.get("message"),
            "user_id": event.get("user_id"),
            "timestamp": event.get("timestamp"),
        })


class VoiceConsumer(AuthenticatedConsumer):
    """
    Voice consumer for real-time voice interactions.
    
    Handles:
    - Audio streaming
    - Transcription
    - Voice responses
    """
    
    is_recording: bool = False
    
    async def connect(self):
        """Connect and prepare for voice."""
        await super().connect()
        
        if self.user_id:
            await self.send_json({
                "type": "voice.ready",
                "user_id": self.user_id,
            })
    
    async def receive_json(self, content):
        """Handle incoming voice commands."""
        msg_type = content.get('type', '')
        
        if msg_type == 'voice.start':
            self.is_recording = True
            await self.send_json({
                "type": "voice.recording",
                "status": "started",
            })
        
        elif msg_type == 'voice.stop':
            self.is_recording = False
            await self.send_json({
                "type": "voice.recording",
                "status": "stopped",
            })
        
        elif msg_type == 'voice.audio':
            # Handle audio chunk (would integrate with STT service)
            await self.send_json({
                "type": "voice.transcription",
                "text": "[Transcription placeholder]",
                "is_final": False,
            })
    
    async def voice_response(self, event):
        """Handle voice response from processing."""
        await self.send_json({
            "type": "voice.response",
            "text": event.get("text"),
            "audio_url": event.get("audio_url"),
        })
