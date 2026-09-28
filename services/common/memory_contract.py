"""Seam memory contract — single authority for the triad memory interface.

Implements SOMA-PM-PLAN-TRIAD-001.md section 1 ("THE SEAM"): models, coordinate
scheme, embedding helper and the MemoryGateway protocol. Both store adapters
speak this contract; nothing else may define a second coordinate scheme or
embedding dialect.

Coordinate scheme (one scheme only):
    ``make_coord(tenant_id, kind, ts, text)`` derives a deterministic 3D point
    and returns the canonical comma-separated float string that is exactly
    ``somafractalmemory.admin.core.models.Memory.coord_to_key`` of that point
    (models.py:78-80 joins ``str(c)`` over the parsed float tuple; the same
    string is what SomaBrain sends as the ``coord`` field of its
    ``/memories`` body — somabrain/memory/client/write.py:260).
    The hash input mirrors SomaBrain's live key→coord derivation
    ``_stable_coord(f"{universe}::{key}")`` (BLAKE2b, [-1,1]^3 —
    somabrain/memory/client/serialization.py:9), so a caller that also keeps
    the key material (see ``coord_key_material``) can make SomaBrain place the
    record at this very same point.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, UTC
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

# Universe scope used by SomaBrain's key→coord derivation when the caller does
# not set one (somabrain/memory/client/serialization.py:186 → "real").
COORD_UNIVERSE = "real"

# Default embedding dimension for the shared vector space (PLAN §1 rule 2).
#
# 768 is the shared default and the SFM Milvus collection's existing dim.
# embed_text() is a SHA-256 bag-of-words hash embedder, so more dimensions
# means strictly fewer hash collisions — 768 is not a compromise, it is the
# better setting. Both stores must agree: MEM_EMBED_DIM (agent) ==
# SOMA_VECTOR_DIM (SFM). A mismatch is a hard failure, never a soft one.
DEFAULT_MEM_EMBED_DIM = 768

MemoryStoreName = Literal["somabrain", "somafractalmemory"]


class MemoryConfigurationError(RuntimeError):
    """Raised when a store URL or other required seam setting is missing.

    Fail-closed: adapters raise this instead of silently no-oping or
    falling back to localhost (VIBE Rule 91).
    """


class MemoryRecallUnavailable(RuntimeError):
    """Raised when a memory store cannot answer a recall (outage / transport failure).

    Fail-closed (R-05 / F-10, T-5): never report an outage as an empty recall.
    The orchestrator must surface "memory unavailable" instead of answering as
    if the user has no history.
    """


class MemoryWrite(BaseModel):
    """One memory to persist via the brain (PLAN §1 contract)."""

    text: str
    kind: Literal["episodic", "semantic", "belief"] = "episodic"
    tenant_id: str
    session_id: str | None = None
    coord: str  # make_coord(...)
    embedding: list[float] | None = None  # dim == settings.MEM_EMBED_DIM
    salience: float = 0.5
    source: str = "agent-chat"


class MemoryHit(BaseModel):
    """One recalled memory from the brain (PLAN §1 contract)."""

    text: str
    coord: str
    score: float
    store: MemoryStoreName
    created_at: str
    # Session/conversation scope — used to keep chat history session-local.
    # Never treat unrelated semantic hits as conversation turns.
    session_id: str | None = None
    role: str | None = None


class MemoryAck(BaseModel):
    """Outcome of one write (PLAN §1 contract)."""

    coord: str
    store: MemoryStoreName
    ok: bool
    error: str | None = None


@runtime_checkable
class MemoryGateway(Protocol):
    """Brain-backed memory gateway — one write path, one read path (PLAN §1)."""

    async def remember(self, w: MemoryWrite) -> list[MemoryAck]:
        """Store one memory in the brain; one ack."""
        ...

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Recall from the brain, ranked by score."""
        ...

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Delete one memory from the brain."""
        ...


# =============================================================================
# COORDINATE — one scheme, SFM-key compatible
# =============================================================================


def _norm_ts(ts: str | datetime) -> str:
    """Normalize a timestamp to a stable ISO-8601 string."""

    if isinstance(ts, datetime):
        dt = ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)
        return dt.isoformat()
    return str(ts).strip()


def coord_key_material(tenant_id: str, kind: str, ts: str | datetime, text: str) -> str:
    """Return the canonical preimage hashed into the coordinate.

    Callers that must make SomaBrain place the record at the seam coordinate
    pass this string as the SomaBrain ``key`` (its write path derives
    ``_stable_coord(f"{universe}::{key}")`` — somabrain/memory/client/write.py:21).
    """

    return f"{tenant_id}|{kind}|{_norm_ts(ts)}|{text}"


def _stable_coord(seed: str) -> tuple[float, float, float]:
    """Derive a deterministic 3D point in [-1, 1]^3 from a string seed.

    Same math as SomaBrain's ``_stable_coord`` so both sides of the seam
    agree on placement (somabrain/memory/client/serialization.py:9).
    """

    digest = hashlib.blake2b(seed.encode("utf-8"), digest_size=12).digest()
    a = int.from_bytes(digest[0:4], "big") / 2**32
    b = int.from_bytes(digest[4:8], "big") / 2**32
    c = int.from_bytes(digest[8:12], "big") / 2**32
    return (2 * a - 1, 2 * b - 1, 2 * c - 1)


def coord_from_key_material(material: str, universe: str = COORD_UNIVERSE) -> str:
    """Derive the canonical coord string from key material.

    Must stay identical to ``make_coord``'s internal derivation.
    """

    x, y, z = _stable_coord(f"{universe}::{material}")
    # str(float) round-trips through SFM's coord_to_key(key_to_coord(s)) == s.
    return f"{x},{y},{z}"


def make_coord(tenant_id: str, kind: str, ts: str | datetime, text: str) -> str:
    """Return the one canonical coordinate string for a memory.

    The string is exactly how somafractalmemory keys the row
    (``Memory.coord_to_key`` of the parsed float tuple), and exactly the
    ``coord`` field SomaBrain's memory client posts to ``/memories``.
    """

    return coord_from_key_material(coord_key_material(tenant_id, kind, ts, text))


# =============================================================================
# SETTINGS — one resolution path, Django settings is the authority
# =============================================================================


def get_memory_setting(name: str, default: Any = None) -> Any:
    """Resolve one seam setting. Django settings is the authority.

    Authority order (VIBE §4 "NO hardcoded values"; ARCHITECTURE-INVARIANTS §6):

      1. ``config.settings.<name>``  — the Django setting, the one authority
      2. ``<name>`` env var          — only when Django settings are absent
                                       (standalone scripts, non-Django tests)
      3. ``default``                 — the caller's explicit last resort

    ``config/settings.py`` reads the env var itself, so inside Django the
    setting *is* the configured value. Reading env first here would let a
    runtime env var silently outrank the configured setting.

    Use this instead of ``os.environ.get`` anywhere in the seam — a second
    lookup path is a second source of truth.
    """

    try:
        from config import settings as _settings

        value = getattr(_settings, name, None)
        if value is not None and value != "":
            return value
    except Exception:
        pass

    value = os.environ.get(name)
    if value is not None and value != "":
        return value

    return default


# =============================================================================
# EMBEDDING — computed once in the gateway, shared by both stores
# =============================================================================

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def get_mem_embed_dim() -> int:
    """Return the shared embedding dimension (settings.MEM_EMBED_DIM).

    Defaults to 768, matching SFM's ``SOMA_VECTOR_DIM`` and the hidden size of
    SFM's ``SOMA_MODEL_NAME`` (microsoft/codebert-base). Both stores must
    agree; a mismatch is a hard failure (ARCHITECTURE-INVARIANTS §2).
    """

    try:
        dim = int(get_memory_setting("MEM_EMBED_DIM", DEFAULT_MEM_EMBED_DIM) or 0)
        return dim if dim > 0 else DEFAULT_MEM_EMBED_DIM
    except (TypeError, ValueError):
        return DEFAULT_MEM_EMBED_DIM


def embed_text(text: str, dim: int | None = None) -> list[float]:
    """Return a deterministic L2-normalized embedding of ``text``.

    Local feature-hashing embedder: no network, no secrets, reproducible.
    It gives both stores one shared vector space (PLAN §1 rule 2). Swap in a
    semantic embedder at the gateway (``embed_fn``) once one is configured.
    """

    dim = dim or get_mem_embed_dim()
    vec = [0.0] * dim
    tokens = _TOKEN_RE.findall(text.lower()) or ["__empty__"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for offset in (0, 8, 16, 24):
            idx = int.from_bytes(digest[offset : offset + 4], "big") % dim
            sign = 1.0 if digest[offset + 4] & 1 else -1.0
            vec[idx] += sign
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0.0:
        vec = [v / norm for v in vec]
    return vec


__all__ = [
    "COORD_UNIVERSE",
    "DEFAULT_MEM_EMBED_DIM",
    "MemoryAck",
    "MemoryConfigurationError",
    "MemoryGateway",
    "MemoryHit",
    "MemoryRecallUnavailable",
    "MemoryStoreName",
    "MemoryWrite",
    "coord_from_key_material",
    "coord_key_material",
    "embed_text",
    "get_mem_embed_dim",
    "get_memory_setting",
    "make_coord",
]
