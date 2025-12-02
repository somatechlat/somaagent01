"""Idempotency key generation utilities.

Contract:
  key = f"{tenant}/{namespace}/{session_id}/{role}/{timestamp_iso}/{hash16}"

Where hash16 is a 16‑character hex derived from a stable base string
(e.g., message id + content hash). Suffixing for collisions can be
implemented by the upstream store; we include only the base key here.
"""

from __future__ import annotations

import datetime as _dt
import hashlib as _hashlib
from typing import Any, Mapping, Optional

from src.core.config import cfg


def _iso(ts: float) -> str:
    return _dt.datetime.utcfromtimestamp(ts).replace(microsecond=0).isoformat() + "Z"


def _hash16(text: str) -> str:
    return _hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def generate_key(
    *,
    tenant: str,
    namespace: str,
    session_id: str,
    role: str,
    timestamp_seconds: float,
    base: str,
) -> str:
    ts_iso = _iso(timestamp_seconds)
    return f"{tenant}/{namespace}/{session_id}/{role}/{ts_iso}/{_hash16(base)}"


def generate_for_memory_payload(
    payload: Mapping[str, Any],
    *,
    namespace: Optional[str] = None,
    now_seconds: Optional[float] = None,
) -> str:
    meta = payload.get("metadata") or {}
    tenant = payload.get("tenant") or meta.get("tenant") or cfg.env("SOMA_TENANT_ID") or "default"
    # Memory sub-namespace fallback should use SOMA_MEMORY_NAMESPACE (e.g. "wm")
    ns = (
        payload.get("namespace")
        or meta.get("namespace")
        or namespace
        or cfg.env("SOMA_MEMORY_NAMESPACE", "wm")
    )
    session_id = str(payload.get("session_id") or meta.get("session_id") or "")
    role = str(payload.get("role") or meta.get("role") or "event")
    ts = (
        float(now_seconds if now_seconds is not None else float(meta.get("timestamp") or 0) or 0)
        or __import__("time").time()
    )
    base = str(payload.get("id") or payload.get("message_id") or _hash16(str(payload)))
    return generate_key(
        tenant=str(tenant),
        namespace=str(ns),
        session_id=session_id,
        role=role,
        timestamp_seconds=ts,
        base=base,
    )
