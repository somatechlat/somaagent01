"""ASGI application for development.

Uses config.settings (test/dev) and routes HTTP + WebSocket via Django Channels.
"""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Import routing AFTER django setup
from services.gateway.routing import websocket_urlpatterns

django_asgi = get_asgi_application()

# Warm the operator's settings layer before the event loop serves anything —
# see services/gateway/asgi.py. Held rows mean the request path never touches
# the ORM to resolve a service URL.
from admin.core.helpers.service_urls import (  # noqa: E402
    warm_infraconfig_cache,
)

warm_infraconfig_cache()

application = ProtocolTypeRouter(
    {
        "http": django_asgi,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
