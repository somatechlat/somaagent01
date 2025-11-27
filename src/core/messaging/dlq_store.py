"""Compatibility shim for the legacy ``src.core.messaging.dlq_store`` import.

The actual dead‑letter‑queue implementation lives in ``services.common.dlq_store``.
This module re‑exports the public symbols so existing imports continue to work
while keeping a single source of truth.
"""

from services.common.dlq_store import DLQStore, ensure_schema

__all__ = ["DLQStore", "ensure_schema"]
