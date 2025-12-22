"""
Eye of God Realtime - Event Types
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Typed event definitions
- Helper functions for broadcasting
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EventLevel(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class BaseEvent:
    """Base event with common fields."""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SettingsUpdatedEvent(BaseEvent):
    """Settings updated event."""
    type: str = "settings_updated"
    tab: str = ""
    version: int = 0


@dataclass
class ThemeAppliedEvent(BaseEvent):
    """Theme applied event."""
    type: str = "theme_applied"
    theme_id: str = ""
    theme_name: str = ""
    user_id: str = ""


@dataclass
class ModeChangedEvent(BaseEvent):
    """Mode changed event."""
    type: str = "mode_changed"
    mode: str = ""
    user_id: str = ""
    previous_mode: Optional[str] = None


@dataclass
class MemoryCreatedEvent(BaseEvent):
    """Memory created event."""
    type: str = "memory_created"
    memory_id: str = ""
    memory_type: str = ""
    importance: float = 0.5


@dataclass
class NotificationEvent(BaseEvent):
    """Generic notification event."""
    type: str = "notification"
    level: EventLevel = EventLevel.INFO
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.data is None:
            self.data = {}


@dataclass
class ChatMessageEvent(BaseEvent):
    """Chat message event."""
    type: str = "chat_message"
    message_id: str = ""
    conversation_id: str = ""
    content: str = ""
    role: str = "assistant"  # user, assistant, system


@dataclass
class ChatStreamEvent(BaseEvent):
    """Chat stream chunk event."""
    type: str = "chat.stream.chunk"
    content: str = ""
    is_final: bool = False


@dataclass
class ToolInvocationEvent(BaseEvent):
    """Tool invocation event."""
    type: str = "tool_invocation"
    tool_id: str = ""
    tool_name: str = ""
    status: str = "started"  # started, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Helper functions for broadcasting events

async def broadcast_to_tenant(channel_layer, tenant_id: str, event: BaseEvent):
    """Broadcast event to all users in a tenant."""
    await channel_layer.group_send(
        f"tenant_{tenant_id}",
        event.to_dict()
    )


async def broadcast_to_user(channel_layer, user_id: str, event: BaseEvent):
    """Broadcast event to a specific user."""
    await channel_layer.group_send(
        f"user_{user_id}",
        event.to_dict()
    )


async def broadcast_to_conversation(channel_layer, conversation_id: str, event: BaseEvent):
    """Broadcast event to all participants in a conversation."""
    await channel_layer.group_send(
        f"conversation_{conversation_id}",
        event.to_dict()
    )
