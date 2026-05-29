"""SomaBrain Client Alias - Backward Compatibility.

This module provides backward-compatible imports for the renamed SomaBrainClient.
The canonical module is admin.core.somabrain_client.

DEPRECATED: Import from admin.core.somabrain_client directly.
"""

import warnings

warnings.warn(
    "admin.core.soma_client is deprecated; import from admin.core.somabrain_client instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all from somabrain_client (Adapter Pattern)
from admin.core.somabrain_client import (
    SomaBrainClient as SomaClient,
    SomaClientError,
)

__all__ = ["SomaClient", "SomaClientError"]
