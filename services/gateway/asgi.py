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

# Warm the operator's settings layer before the event loop serves anything.
# InfrastructureConfig rows are deployment endpoints an administrator edits;
# holding them means every request path reads a dict instead of the ORM, which
# is both the latency answer at volume and what makes the resolver correct
# from async code. A cold cache on a live request would mean doing ORM work on
# the loop thread — so it is filled here, where there is no loop yet.
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
