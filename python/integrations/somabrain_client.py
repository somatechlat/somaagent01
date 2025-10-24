"""SomaBrain client alias.

Temporary shim to allow gradual rename from SomaClient to SomaBrainClient.
Prefer importing SomaBrainClient from this module going forward.
"""
from __future__ import annotations

from python.integrations.soma_client import (
    SomaClient,
    SomaClientError,
    SomaMemoryRecord,
)


class SomaBrainClient(SomaClient):
    """Backwards-compatible alias for the SomaBrain HTTP client."""


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaMemoryRecord",
]
