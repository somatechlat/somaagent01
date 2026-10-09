"""Memory API — SomaBrain only (T-1).

Agent never talks to somafractalmemory. All list / recall / save / forget go
through SomaBrain (the sole bridge). No legacy replica tables, no export jobs,
no compatibility shims.
"""

from __future__ import annotations

import logging

from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError, ServiceError
from services.common.authorization import authorize

router = Router(tags=["memory"])
logger = logging.getLogger(__name__)


class MemorySaveIn(BaseModel):
    text: str
    kind: str = "episodic"
    salience: float = 0.7


class MemoryRecallIn(BaseModel):
    query: str
    top_k: int = 10


def _tenant(request) -> str:
    auth = getattr(request, "auth", None)
    tid = getattr(auth, "effective_tenant_id", None) or getattr(auth, "tenant_id", None)
    tid = str(tid or "").strip()
    if tid.lower() in {"", "default", "standalone", "none", "null"}:
        from django.conf import settings

        fallback = str(getattr(settings, "AAAS_DEFAULT_TENANT_ID", "") or "").strip()
        if (
            fallback
            and fallback.lower() not in {"default", "standalone", "none"}
            and len(fallback) >= 8
        ):
            return fallback
        raise ServiceError("Tenant context required for memory operations")
    return tid


async def _gateway():
    from services.common.memory_gateway import get_memory_gateway

    return get_memory_gateway()


@router.get("/status", summary="Honest memory lane status", auth=AuthBearer())
async def memory_status(request) -> dict:
    """Real memory health for the UI indicator — list is not enough.

    Brain ``/health`` reports ``memory_ok`` / ``memory_degraded`` from the
    LTM write path. A green GET /memory/ with ``memory_ok=false`` means
    reads may work while writes 503 — the indicator must not call that ready.
    """
    from admin.core.somabrain_client import SomaBrainClient
    from services.common.circuit_breaker import get_circuit_breaker

    await authorize(request, action="resource:memory_search", resource="memory")

    breaker = get_circuit_breaker("memory_gateway", failure_threshold=5, reset_timeout=30.0)
    circuit = str(getattr(breaker, "state", "") or "")
    gateway_ok = circuit.lower() != "open"

    read_ok = False
    write_ok = False
    memory_degraded = True
    reason = ""
    brain_status = ""

    try:
        await _gateway()
        read_ok = True
    except Exception as exc:  # noqa: BLE001
        reason = f"gateway: {exc}"

    client = await SomaBrainClient.get_async()
    if client is None:
        write_ok = False
        reason = reason or "SomaBrain client not configured"
    else:
        try:
            health = await client.health()
            if isinstance(health, dict):
                brain_status = str(health.get("status") or "")
                write_ok = bool(health.get("memory_ok"))
                memory_degraded = bool(
                    health.get("memory_degraded")
                    or health.get("memory_circuit_open")
                    or not write_ok
                )
                if not write_ok and not reason:
                    reason = str(
                        health.get("memory_error")
                        or "Brain reports memory_ok=false (LTM write path down)"
                    )
            else:
                write_ok = False
                reason = "Brain health payload unexpected shape"
        except Exception as exc:  # noqa: BLE001
            write_ok = False
            memory_degraded = True
            reason = reason or f"brain health: {exc}"

    if write_ok and read_ok and gateway_ok:
        state = "ok"
        summary = "Memory ready"
    elif read_ok and not write_ok:
        state = "warn"
        summary = "Memory degraded — reads may work; writes queue until the brain recovers"
    else:
        state = "warn"
        summary = "Memory unavailable — messages queue until connected"

    return {
        "state": state,
        "summary": summary,
        "read_ok": read_ok,
        "write_ok": write_ok,
        "degraded": memory_degraded,
        "circuit": circuit,
        "brain_status": brain_status,
        "reason": reason,
    }


@router.get("/", summary="List recent memories", auth=AuthBearer())
async def list_memories(request, limit: int = 20) -> dict:
    """Recent memories from SomaBrain (recall-wide)."""
    await authorize(request, action="resource:memory_read", resource="memory")
    gateway = await _gateway()
    tenant_id = _tenant(request)
    try:
        hits = await gateway.recall("*", max(1, min(limit, 100)), tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Memory list failed: {exc}") from exc
    memories = [
        {
            "text": h.text,
            "coord": h.coord,
            "score": h.score,
            "store": h.store,
            "created_at": h.created_at,
        }
        for h in hits
    ]
    return {"memories": memories, "total": len(memories), "tenant_id": tenant_id}


@router.post("/recall", summary="Recall memories", auth=AuthBearer())
async def recall_memories(request, payload: MemoryRecallIn) -> dict:
    """Semantic recall via SomaBrain only."""
    await authorize(request, action="resource:memory_search", resource="memory")
    gateway = await _gateway()
    tenant_id = _tenant(request)
    try:
        hits = await gateway.recall(payload.query, max(1, min(payload.top_k, 50)), tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Memory recall failed: {exc}") from exc
    memories = [
        {
            "text": h.text,
            "coord": h.coord,
            "score": h.score,
            "store": h.store,
            "created_at": h.created_at,
        }
        for h in hits
    ]
    return {"memories": memories, "total": len(memories), "query": payload.query}


@router.post("/save", summary="Save memory", auth=AuthBearer())
async def save_memory(request, payload: MemorySaveIn) -> dict:
    """Persist a memory through SomaBrain (one write lane)."""
    await authorize(request, action="resource:memory_write", resource="memory")
    gateway = await _gateway()
    tenant_id = _tenant(request)
    try:
        acks = await gateway.remember_text(
            payload.text,
            tenant_id=tenant_id,
            kind=payload.kind,
            salience=payload.salience,
        )
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Memory save failed: {exc}") from exc
    ok = any(bool(getattr(a, "ok", False)) for a in acks)
    memory_id = next(
        (str(getattr(a, "coord", "") or "") for a in acks if getattr(a, "coord", None)),
        "",
    )
    return {
        "saved": ok,
        "memory_id": memory_id,
        "tenant_id": tenant_id,
        "acks": [
            {
                "ok": bool(getattr(a, "ok", False)),
                "store": getattr(a, "store", None),
                "coord": getattr(a, "coord", None),
                "error": getattr(a, "error", None),
            }
            for a in acks
        ],
    }


class MemoryForgetIn(BaseModel):
    coord: str


@router.post("/forget", summary="Forget memory by coord (body)", auth=AuthBearer())
async def forget_memory_body(request, payload: MemoryForgetIn) -> dict:
    """Erase a memory via SomaBrain forget. Body form avoids URL-encoding coords."""
    await authorize(request, action="resource:memory_delete", resource="memory")
    gateway = await _gateway()
    tenant_id = _tenant(request)
    coord = (payload.coord or "").strip()
    if not coord:
        raise ServiceError("coord is required")
    try:
        ok = await gateway.forget(coord, tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Memory forget failed: {exc}") from exc
    if not ok:
        raise NotFoundError("memory", coord)
    return {"forgotten": True, "coord": coord, "memory_id": coord}


@router.delete("/{coord}", summary="Forget memory by coord", auth=AuthBearer())
async def forget_memory(request, coord: str) -> dict:
    """Erase a memory via SomaBrain forget. Prefer POST /memory/forget for coords
    containing commas (URL path segments split on them)."""
    await authorize(request, action="resource:memory_delete", resource="memory")
    gateway = await _gateway()
    tenant_id = _tenant(request)
    coord = (coord or "").strip()
    if not coord:
        raise ServiceError("coord is required")
    try:
        ok = await gateway.forget(coord, tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Memory forget failed: {exc}") from exc
    if not ok:
        raise NotFoundError("memory", coord)
    return {"forgotten": True, "coord": coord, "memory_id": coord}

# =============================================================================
# METRICS
# =============================================================================


class MemoryMetricsResponse(BaseModel):
    """Memory subsystem metrics. Measured, not asserted."""

    kafka: dict


@router.get("/metrics", summary="Memory and Kafka metrics", auth=AuthBearer())
async def memory_metrics(request) -> MemoryMetricsResponse:
    """Kafka health for the memory subsystem.

    Moved here from ``admin/core/api/memory.py``: memory has one home, and
    this is it. The orphaned ``/core/memory/metrics`` copy had no callers.
    """
    await authorize(request, action="system:read_metrics", resource="memory")
    from services.common.event_bus import KafkaEventBus, KafkaSettings

    client = KafkaEventBus(KafkaSettings.from_env())
    try:
        result = await client.healthcheck()
    finally:
        await client.close()

    return MemoryMetricsResponse(kafka=result or {})
