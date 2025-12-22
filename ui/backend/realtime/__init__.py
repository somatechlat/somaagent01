"""
Eye of God Realtime Package
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT: Real Django Channels package
"""

from realtime.consumers import EventsConsumer, ChatConsumer, VoiceConsumer
from realtime.routing import websocket_urlpatterns
from realtime.events import (
    BaseEvent,
    SettingsUpdatedEvent,
    ThemeAppliedEvent,
    ModeChangedEvent,
    MemoryCreatedEvent,
    NotificationEvent,
    ChatMessageEvent,
    ChatStreamEvent,
    ToolInvocationEvent,
    broadcast_to_tenant,
    broadcast_to_user,
    broadcast_to_conversation,
)

__all__ = [
    # Consumers
    'EventsConsumer',
    'ChatConsumer',
    'VoiceConsumer',
    # Routing
    'websocket_urlpatterns',
    # Events
    'BaseEvent',
    'SettingsUpdatedEvent',
    'ThemeAppliedEvent',
    'ModeChangedEvent',
    'MemoryCreatedEvent',
    'NotificationEvent',
    'ChatMessageEvent',
    'ChatStreamEvent',
    'ToolInvocationEvent',
    # Helpers
    'broadcast_to_tenant',
    'broadcast_to_user',
    'broadcast_to_conversation',
]
