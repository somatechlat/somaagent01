"""Voice WebSocket URL Routing.


"""

from django.urls import path

from admin.voice.consumers import VoiceConsumer

websocket_urlpatterns = [
    path("ws/voice/", VoiceConsumer.as_asgi()),
    path("ws/voice/<str:session_id>/", VoiceConsumer.as_asgi()),
]