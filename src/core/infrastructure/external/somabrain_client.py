"""SomaBrain client re-exports.

The implementation lives in ``python.integrations.somabrain_client``.
This module re‑exports the public symbols from the canonical location.
"""

from __future__ import annotations

# Re‑export the concrete client and helper functions.
from python.integrations.somabrain_client import (
    build_context,
    build_context_async,
    get_persona,
    get_tenant_flag,
    get_tenant_flag_async,
    get_weights,
    get_weights_async,
    publish_reward_async,
    put_persona,
    SomaBrainClient,
    SomaClientError,
    SomaMemoryRecord,
    update_weights,
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
