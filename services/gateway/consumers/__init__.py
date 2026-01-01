"""Django Channels WebSocket consumers.

VIBE COMPLIANT - Real WebSocket implementation with Django Channels.
"""

from services.gateway.consumers.chat import ChatConsumer

__all__ = ["ChatConsumer"]
