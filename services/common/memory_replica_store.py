"""Re-exports for ``MemoryReplicaStore``.

The implementation lives in ``src.core.domain.memory.replica_store``.
This module re‑exports the public symbols from the canonical module.
"""

from __future__ import annotations

# Re‑export the canonical implementation.
from src.core.infrastructure.repositories import (
    ensure_schema,
    MemoryReplicaRow,
    MemoryReplicaStore,
    MIGRATION_SQL,
)

__all__ = [
    "MemoryReplicaRow",
    "MemoryReplicaStore",
    "ensure_schema",
    "MIGRATION_SQL",
]
# module's public interface.
