"""SomaBrain Client - Django

Production-grade HTTP client for SomaBrain memory service.
100% Django patterns - No FastAPI, No SQLAlchemy.


- Rule 1: NO BULLSHIT - Real implementation, no mocks
- Rule 4: REAL IMPLEMENTATIONS ONLY
- Rule 8: Django/Ninja ONLY
- Rule 13: CENTRALIZED SETTINGS
- Rule 32: HYBRID CONFIGURATION STANDARD
"""

from __future__ import annotations

from typing import Optional

from admin.core.somabrain_base import (
    SomaClientError,
    SomaMemoryRecord,
)
from admin.core.somabrain_chat import _SomaBrainChatClient


class SomaBrainClient(_SomaBrainChatClient):
    """Production SomaBrain HTTP client.

    Thread-safe singleton pattern for connection pooling.
    Uses Django settings for configuration.
    """


# Backwards compatibility aliases
SomaBrainError = SomaClientError


def get_somabrain_client() -> Optional[SomaBrainClient]:
    """Get SomaBrain client singleton (synchronous helper).

    Returns:
        SomaBrainClient instance when configured, or None in standalone mode.
        Callers must check the return value before use.
    """
    return SomaBrainClient.get()


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaMemoryRecord",
    "get_somabrain_client",
]
