"""Django Channels WebSocket routing.


Per login-to-chat-journey design.md Section 7.1
"""

from django.urls import re_path

from admin.voice.consumers import VoiceConsumer
from services.gateway.consumers.chat import ChatConsumer

websocket_urlpatterns = [
    # Chat WebSocket endpoints
    # URLs:
    # - /ws/v2/chat
    # - /ws/v2/chat/{agent_id}
    # - /ws/v2/events
    # - /ws/chat/{agent_id} (legacy)
    re_path(r"ws/v2/chat/?$", ChatConsumer.as_asgi()),  # type: ignore[arg-type]
    re_path(r"ws/v2/chat/(?P<agent_id>[^/]+)$", ChatConsumer.as_asgi()),  # type: ignore[arg-type]
    re_path(r"ws/v2/events/?$", ChatConsumer.as_asgi()),  # type: ignore[arg-type]
    re_path(r"ws/chat/(?P<agent_id>[^/]+)$", ChatConsumer.as_asgi()),  # type: ignore[arg-type]
    # Voice WebSocket endpoint
    # URL: /ws/voice/
    re_path(r"ws/voice/?$", VoiceConsumer.as_asgi()),  # type: ignore[arg-type]
]
