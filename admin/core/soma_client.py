"""SomaBrain Client Alias - Backward Compatibility.

This module provides backward-compatible imports for the renamed SomaBrainClient.
The canonical module is admin.core.somabrain_client.

VIBE Compliant - Real implementation, just aliased for import compatibility.
"""

# Re-export all from somabrain_client with legacy names
from admin.core.somabrain_client import (
    SomaBrainClient as SomaClient,
    SomaClientError,
)

__all__ = ["SomaClient", "SomaClientError"]
