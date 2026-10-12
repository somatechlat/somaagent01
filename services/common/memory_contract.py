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
    The hash is the cross-repo shared ``soma_memory_contract`` module (T-2,
    one definition). A caller that also keeps the key material (see
    ``coord_key_material``) can make SomaBrain place the record at this very
    same point.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from enum import StrEnum
from django.core.exceptions import ImproperlyConfigured
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

# T-2: ONE coordinate hash, the cross-repo shared module (W3). Re-exported
# under this contract's historical names so every seam caller keeps working.
from soma_memory_contract import (
    COORD_UNIVERSE,
    DEFAULT_MEM_EMBED_DIM,
    _stable_coord,
    coord_from_key_material,
    coord_key_material,
    coord_to_str,
    make_coord,
)

MemoryStoreName = Literal["somabrain", "somafractalmemory"]


class MemoryDurability(StrEnum):
    """Where a write is durably accepted (T-6). Named vocabulary (AP-06).

    Mirrors somabrain's ``MemoryDurability`` (somabrain/api/memory/models.py)
    verbatim — one vocabulary for one concept. Do NOT invent a second name.
    """

    PERSISTED_LTM = "persisted_ltm"
    DURABLE_OUTBOX = "durable_outbox"
    DEGRADED_JOURNAL = "degraded_journal"


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


class MemoryWriteError(RuntimeError):
    """Write/forget transport or backend failure. Distinct from "not found".

    Fail-closed (T-5 honesty): a transport outage must never be collapsed
    into the boolean "not found" answer.
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
    # Taxonomy the write path set (episodic / semantic / belief / …). Optional
    # because an older store row may not carry it; callers filter only when set.
    kind: str | None = None
    # TRIAD degradation contract (flag, never silent)
    degraded: bool = False
    error_code: str | None = None
    degraded_reason: str | None = None


class MemoryAck(BaseModel):
    """Outcome of one write (PLAN §1 contract).

    ``ok`` alone is never enough — read ``durability`` to know WHERE the write
    was accepted (T-6). ``durability=None`` means the store did not report its
    durability and the write must NOT be treated as durably accepted.
    ``persisted_to_ltm`` / ``queued_for_ltm`` mirror the brain's
    ``MemoryWriteResponse`` verbatim so a fast-ack cannot claim a durable
    accept it did not observe (R-15).
    """

    coord: str
    store: MemoryStoreName
    ok: bool
    error: str | None = None
    durability: MemoryDurability | None = None
    outbox_event_id: int | None = None
    persisted_to_ltm: bool = False
    queued_for_ltm: bool = False
    # TRIAD degradation contract (flag, never silent)
    degraded: bool = False
    error_code: str | None = None
    degraded_reason: str | None = None

    @classmethod
    def from_brain_response(
        cls,
        data: dict[str, Any],
        *,
        coord: str,
        store: MemoryStoreName = "somabrain",
        fallback_coord: str | None = None,
    ) -> "MemoryAck":
        """Map a brain ``/memory/remember`` body to a MemoryAck — R-15 honesty.

        Never hardcodes ``ok=True``. The brain's own ``ok`` (which is
        ``durable_accept``: persisted_to_ltm OR a verified durable outbox row)
        is the authority. A body that omits ``durability`` is an older brain
        and fails closed rather than silently claiming a durable accept.
        """
        stored = data.get("coord") or data.get("coordinate")
        if isinstance(stored, (list, tuple)) and stored:
            stored_coord = ",".join(str(x) for x in stored)
        elif isinstance(stored, str) and stored.strip():
            stored_coord = stored.strip()
        else:
            stored_coord = fallback_coord or coord

        raw_durability = data.get("durability")
        if raw_durability is None:
            return cls(
                coord=stored_coord,
                store=store,
                ok=False,
                durability=None,
                persisted_to_ltm=bool(data.get("persisted_to_ltm")),
                queued_for_ltm=bool(data.get("queued_for_ltm")),
                error=(
                    "brain response omitted durability; cannot confirm "
                    "durable accept (T-6)"
                ),
            )
        try:
            durability = MemoryDurability(raw_durability)
        except ValueError:
            return cls(
                coord=stored_coord,
                store=store,
                ok=False,
                durability=None,
                persisted_to_ltm=bool(data.get("persisted_to_ltm")),
                queued_for_ltm=bool(data.get("queued_for_ltm")),
                error=f"brain reported unknown durability {raw_durability!r} (T-6)",
            )

        outbox_id = data.get("outbox_event_id")
        persisted = bool(data.get("persisted_to_ltm"))
        queued = bool(data.get("queued_for_ltm"))
        # Brain ok is durable_accept. Trust it only when the durability enum
        # agrees; a mismatch is a dishonest ack and must not be smoothed over.
        brain_ok = bool(data.get("ok"))
        durable_accept = persisted or durability == MemoryDurability.DURABLE_OUTBOX
        ok = brain_ok and durable_accept
        error = data.get("error")
        if not ok and not error:
            error = (
                "write not accepted into LTM or the durable outbox (T-6)"
            )
        return cls(
            coord=stored_coord,
            store=store,
            ok=ok,
            error=str(error) if error else None,
            durability=durability,
            outbox_event_id=int(outbox_id) if outbox_id is not None else None,
            persisted_to_ltm=persisted,
            queued_for_ltm=queued,
        )


@runtime_checkable
class MemoryGateway(Protocol):
    """Brain-backed memory gateway — one write path, one read path (PLAN §1)."""

    async def remember(self, w: MemoryWrite) -> list[MemoryAck]:
        """Store one memory in the brain; one ack."""
        ...

    async def remember_text(
        self,
        text: str,
        *,
        tenant_id: str,
        kind: str = "episodic",
        ts: str | datetime | None = None,
        session_id: str | None = None,
        salience: float = 0.5,
        source: str = "agent-chat",
        role: str | None = None,
    ) -> list[MemoryAck]:
        """Write through the seam with coordinate convergence (T-1)."""
        ...

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Recall from the brain, ranked by score.

        Raises ``MemoryRecallUnavailable`` on outage — never an empty list.
        """
        ...

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Delete one memory from the brain. Three honest outcomes (T-5):

        - ``True``  — brain reports deleted
        - ``False`` — brain reports not-found (a real answer, not an error)
        - raises ``MemoryWriteError`` — transport/backend failure

        A transport failure is NEVER collapsed into ``False``.
        """
        ...


# =============================================================================
# COORDINATE — one scheme, SFM-key compatible (authority: soma_memory_contract)
# =============================================================================


# =============================================================================
# SETTINGS — one resolution path, Django settings is the authority
# =============================================================================


def get_memory_setting(name: str, *, capsule: Any = None, agent_id: Any = None) -> Any:
    """Resolve one seam setting through the ONE chain.

    Capsule -> AgentSetting -> InfrastructureConfig -> SettingsModel -> RAISE
    (SOMA-SETTINGS-MODEL-001 R-OWN-01/05). No default parameter: a default is a
    hardcoded value (Rule 1). A missing value is a refusal naming the setting
    (Rule 6 / Rule 91). Pass ``capsule``/``agent_id`` so L2 can apply.
    """
    from admin.core.helpers.service_urls import require_setting

    return require_setting(name, capsule=capsule, agent_id=agent_id)


# =============================================================================
# EMBEDDING — computed once in the gateway, shared by both stores
# =============================================================================

_TOKEN_RE = re.compile(r"[a-z0-9']+")

# Seed salt of the brain's TinyDeterministicEmbedder
# (somabrain/admin/core/embeddings.py:70). This is the embedding-space
# identity, not a tunable: a different salt is a different vector space and
# cosine against stored rows is meaningless (INVARIANTS §2).
_BRAIN_EMBED_SEED_SALT = 1337

# Same epsilon as somabrain.math.normalize_vector (_EPS).
_NORM_EPS = 1e-12


def get_mem_embed_dim() -> int:
    """Return the shared embedding dimension (settings.MEM_EMBED_DIM).

    Defaults to 768, matching SFM's ``SOMA_VECTOR_DIM`` and the hidden size of
    SFM's ``SOMA_MODEL_NAME`` (microsoft/codebert-base). Both stores must
    agree; a mismatch is a hard failure (ARCHITECTURE-INVARIANTS §2).
    """

    # One arg: get_memory_setting resolves the chain and takes no default
    # (Rule 1). DEFAULT_MEM_EMBED_DIM is the single declaration-site constant
    # ADR-001 pins -- tests/unit/test_embed_dim_seam_768.py asserts it is the
    # ONLY place 768 is written as a default -- and is used only when the chain
    # is unreachable (no Django, no DB), never as a silent substitute.
    try:
        dim = int(get_memory_setting("MEM_EMBED_DIM") or 0)
        return dim if dim > 0 else DEFAULT_MEM_EMBED_DIM
    except (TypeError, ValueError, ImproperlyConfigured):
        return DEFAULT_MEM_EMBED_DIM


def _brain_token_digest(token: str) -> bytes:
    """blake2b digest of one token — identical to TinyDeterministicEmbedder."""
    return hashlib.blake2b(
        f"{_BRAIN_EMBED_SEED_SALT}:{token}".encode(), digest_size=16
    ).digest()


def _brain_fold(token: str) -> str:
    """Light morphological fold — identical to TinyDeterministicEmbedder._fold."""
    t = token
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t.endswith("es"):
        return t[:-2]
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    if len(t) > 5 and t.endswith("ing"):
        return t[:-3]
    if len(t) > 4 and t.endswith("ed"):
        return t[:-2]
    return t


def embed_text(text: str, dim: int | None = None) -> list[float]:
    """Return a deterministic L2-normalized embedding of ``text``.

    ONE vector space (INVARIANTS §2 / C2): this is bit-identical to the
    brain's ``TinyDeterministicEmbedder.embed``
    (somabrain/admin/core/embeddings.py:100) — blake2b(seed_salt=1337) token
    hashing, length-based distinctiveness, morphological fold, character
    trigrams, float32 accumulation, then L2 normalize. The gateway embeds
    once; SomaBrain never has to re-embed, and query/stored cosine is
    meaningful across the agent and the brain.
    """
    import numpy as np

    dim = int(dim or get_mem_embed_dim())
    vec = np.zeros(dim, dtype="float32")
    raw = (text or "").lower()
    tokens = [t for t in _TOKEN_RE.findall(raw) if t]
    if not tokens:
        tokens = ["__empty__"]
    for token in tokens:
        folded = _brain_fold(token)
        weight = 1.0 + (len(token) / 4.0)
        for form in (token, folded) if folded != token else (token,):
            digest = _brain_token_digest(form)
            n = len(digest)
            for offset in (0, 4, 8):
                idx = int.from_bytes(digest[offset : offset + 4], "big") % dim
                sign = 1.0 if digest[(offset + 4) % n] & 1 else -1.0
                vec[idx] += sign * weight
        # Character trigrams for morphological robustness. Both forms always
        # contribute — matching the brain — so a token whose fold equals the
        # token gets its trigrams twice.
        for form in (token, folded):
            padded = f"^{form}$"
            for i in range(max(0, len(padded) - 2)):
                gram = padded[i : i + 3]
                gd = _brain_token_digest(f"#{gram}")
                idx = int.from_bytes(gd[0:4], "big") % dim
                sign = 1.0 if gd[4] & 1 else -1.0
                vec[idx] += sign * (0.35 * weight)
    # L2 normalize exactly as somabrain.math.normalize_vector: float64 norm,
    # divide, cast to float32.
    v64 = vec.astype(np.float64)
    norm = float(np.linalg.norm(v64))
    if norm <= _NORM_EPS:
        return [0.0] * dim
    out = (v64 / norm).astype(np.float32)
    return [float(x) for x in out]


__all__ = [
    "COORD_UNIVERSE",
    "DEFAULT_MEM_EMBED_DIM",
    "MemoryAck",
    "MemoryConfigurationError",
    "MemoryDurability",
    "MemoryGateway",
    "MemoryHit",
    "MemoryRecallUnavailable",
    "MemoryStoreName",
    "MemoryWrite",
    "coord_from_key_material",
    "coord_key_material",
    "coord_to_str",
    "embed_text",
    "get_mem_embed_dim",
    "get_memory_setting",
    "make_coord",
]
