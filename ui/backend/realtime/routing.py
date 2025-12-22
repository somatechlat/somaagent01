"""
Eye of God Realtime - WebSocket Routing
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Channels routing
- URL pattern matching
"""

from django.urls import re_path
from realtime.consumers import EventsConsumer, ChatConsumer, VoiceConsumer

websocket_urlpatterns = [
    re_path(r'ws/v2/events/?$', EventsConsumer.as_asgi()),
    re_path(r'ws/v2/chat/?$', ChatConsumer.as_asgi()),
    re_path(r'ws/v2/chat/(?P<conversation_id>[^/]+)/?$', ChatConsumer.as_asgi()),
    re_path(r'ws/v2/voice/?$', VoiceConsumer.as_asgi()),
]
