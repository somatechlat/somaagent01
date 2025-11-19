"""Compatibility shim for the SomaBrain client.

The original implementation lives in ``python.integrations.somabrain_client``.
To satisfy the VIBE rule of a single source of truth while keeping existing
imports functional, this module re‑exports the public symbols from the
canonical location.
"""

from __future__ import annotations

# Re‑export the concrete client and helper functions.
from python.integrations.somabrain_client import (
    SomaBrainClient,
    SomaClientError,
    SomaMemoryRecord,
    get_weights,
    update_weights,
    build_context,
    get_tenant_flag,
    get_persona,
    put_persona,
    get_weights_async,
    build_context_async,
    publish_reward_async,
    get_tenant_flag_async,
)

__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaMemoryRecord",
    "get_weights",
    "update_weights",
    "build_context",
    "get_tenant_flag",
    "get_persona",
    "put_persona",
    "get_weights_async",
    "build_context_async",
    "publish_reward_async",
    "get_tenant_flag_async",
]
