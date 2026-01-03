"""ASGI application for SomaAgent01 gateway.

Enables HTTP + WebSocket routing via Django Channels.
"""

from __future__ import annotations

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from services.gateway.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

django_asgi = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
