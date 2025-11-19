"""Compatibility shim for ``MemoryReplicaStore``.

The original implementation now lives in
``src.core.domain.memory.replica_store``.  This module exists solely to
preserve the historic import path ``services.common.memory_replica_store``
used throughout the codebase and external integrations.

We simply re‑export the public symbols from the canonical module so that
existing imports continue to work without pulling in duplicate code.
"""

from __future__ import annotations

# Re‑export the canonical implementation.
from src.core.domain.memory.replica_store import (
    MemoryReplicaRow,
    MemoryReplicaStore,
    ensure_schema,
    MIGRATION_SQL,
)

__all__ = [
    "MemoryReplicaRow",
    "MemoryReplicaStore",
    "ensure_schema",
    "MIGRATION_SQL",
]
# module's public interface.
