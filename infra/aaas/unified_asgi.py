"""
ASGI config for Agent-as-a-Service (AAAS) Mode.

Exposes the ASGI application for WebSocket and HTTP/2 support.

Usage:
    uvicorn infra.aaas.unified_asgi:application --host 0.0.0.0 --port 9000
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infra.aaas.unified_settings")
os.environ.setdefault("SOMA_SINGLE_PROCESS", "true")

# Initialize Django ASGI application early to ensure settings are loaded
django_asgi_app = get_asgi_application()

# Import channels routing after Django setup
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack

    # Import WebSocket routes from Agent
    try:
        from services.gateway.routing import websocket_urlpatterns
    except ImportError:
        websocket_urlpatterns = []

    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        }
    )
except ImportError:
    # Fallback to pure Django ASGI if channels not available
    application = django_asgi_app
