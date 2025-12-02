"""
Messaging utilities for consistent headers, correlation, and idempotency keys.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Dict, Optional


def correlation_id(existing: Optional[str] = None) -> str:
    """Return a correlation id (reuse if provided)."""
    return existing or str(uuid.uuid4())


def idempotency_key(payload: Dict[str, Any], *, seed: Optional[str] = None) -> str:
    """Create a stable idempotency key based on payload + optional seed."""
    raw = f"{seed or ''}|{payload}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


def build_headers(
    *,
    tenant: Optional[str] = None,
    session_id: Optional[str] = None,
    persona_id: Optional[str] = None,
    event_type: Optional[str] = None,
    event_id: Optional[str] = None,
    schema: Optional[str] = None,
    correlation: Optional[str] = None,
) -> Dict[str, str]:
    """Standard header map for Kafka/outbox messages."""
    corr = correlation_id(correlation)
    return {
        "tenant_id": tenant or "",
        "session_id": session_id or "",
        "persona_id": persona_id or "",
        "event_type": event_type or "",
        "event_id": event_id or "",
        "schema": schema or "",
        "correlation_id": corr,
        "timestamp_ms": str(int(time.time() * 1000)),
    }
