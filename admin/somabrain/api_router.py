"""SomaBrain Memory API Router.


Per CANONICAL_USER_JOURNEYS_SRS.md UC-05: View/Manage Memories.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Optional

from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.authorization import authorize
from admin.common.exceptions import UnauthorizedError
from admin.common.messages import ErrorCode, get_message, SuccessCode

router = Router(tags=["memory"])
logger = logging.getLogger(__name__)

# Mount cognitive sub-router
from admin.somabrain.cognitive import router as cognitive_router

router.add_router("/cognitive", cognitive_router)

# Mount admin sub-router
from admin.somabrain.admin_api import router as admin_router

router.add_router("/admin", admin_router)

# Mount core brain sub-router (Phase 6.1, 6.2)
from admin.somabrain.core_brain import router as core_brain_router

router.add_router("/brain", core_brain_router)


# =============================================================================
# SCHEMAS
# =============================================================================


class MemoryOut(BaseModel):
    """Memory item response."""

    id: str
    content: str
    memory_type: str  # episodic, semantic, procedural
    created_at: str
    relevance_score: Optional[float] = None
    metadata: Optional[dict] = None


class MemorySearchRequest(BaseModel):
    """Search request."""

    query: str
    limit: int = 10
    memory_type: Optional[str] = None


class MemoryCreateRequest(BaseModel):
    """Create memory request."""

    content: str
    memory_type: str = "episodic"
    metadata: Optional[dict] = None


class MemoryStatsOut(BaseModel):
    """Memory statistics."""

    total_memories: int
    pending_sync: int
    by_type: dict


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/search",
    summary="Search memories",
    auth=AuthBearer(),
)
async def search_memories(request, payload: MemorySearchRequest) -> dict:
    """Semantic search over memories.

    Per SRS UC-05: POST /api/v2/memory/search


    - Real SomaBrain integration
    - Graceful degradation if unavailable
    """
    await authorize(request, action="resource:memory_search", resource="memory")
    from services.common.memory_contract import MemoryRecallUnavailable
    from services.common.memory_gateway import get_memory_gateway

    # Get tenant from auth context (fail-closed if missing)
    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for memory search")
    tenant_id = request.auth.effective_tenant_id

    try:
        gateway = get_memory_gateway()
        hits = await gateway.recall(payload.query, max(1, int(payload.limit)), tenant_id)

        items = []
        for hit in hits:
            if payload.memory_type and hit.kind and hit.kind != payload.memory_type:
                continue
            items.append(
                MemoryOut(
                    id=hit.coord,
                    content=hit.text,
                    memory_type=hit.kind or payload.memory_type or "episodic",
                    created_at=hit.created_at,
                    relevance_score=hit.score,
                    metadata=None,
                ).model_dump()
            )

        return {"memories": items, "query": payload.query}

    except MemoryRecallUnavailable as e:
        logger.error("Memory search failed: %s", e)
        return {
            "memories": [],
            "query": payload.query,
            "error": get_message(ErrorCode.SOMABRAIN_UNAVAILABLE),
        }


@router.post(
    "",
    summary="Create memory",
    auth=AuthBearer(),
)
async def create_memory(request, payload: MemoryCreateRequest) -> dict:
    """Store a new memory.

    Writes through the MemoryGateway seam. Degradation is the seam's own
    outbox (T-6 durable-before-hop) — one path for every memory write.
    """
    await authorize(request, action="resource:memory_write", resource="memory")
    from services.common.memory_contract import get_memory_setting, make_coord
    from services.common.memory_gateway import (
        MEMORY_WAL_TOPIC_DEFAULT,
        durable_accept_memory,
        get_memory_gateway,
    )

    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for memory creation")
    tenant_id = request.auth.effective_tenant_id
    kind = str(payload.memory_type or "episodic")

    try:
        gateway = get_memory_gateway()
        acks = await gateway.remember_text(
            payload.content,
            tenant_id=tenant_id,
            kind=kind,
            source="api",
        )
        accepted = next((a for a in acks if a.ok), None)
        if accepted is not None:
            return {
                "success": True,
                "memory_id": accepted.coord,
                "message": get_message(SuccessCode.MEMORY_STORED),
            }
        # T-6: the seam already accepted this write into the memory.wal outbox
        # before its hop. That row is the degraded record and the one replay
        # authority (outbox drain → memory.wal → memory-replicator). Queuing it
        # again elsewhere would be a second degraded path and a duplicate.
        error = next((a.error for a in acks if a.error), "memory write not accepted")
        coord = next((a.coord for a in acks), "")
        logger.warning("MemoryGateway write unacked (coord=%s): %s", coord, error)
        return {
            "success": True,
            "memory_id": coord,
            "degraded": True,
            "queued": True,
            "queue": get_memory_setting("MEMORY_WAL_TOPIC"),
            "message": get_message(SuccessCode.MEMORY_STORED),
        }

    except Exception as e:
        # The seam could not accept the write at all, so no T-6 row exists yet.
        # Queue it through the same entry point — one degraded path, never a
        # second queue. If the outbox is also down this raises: fail-closed
        # rather than silently dropping the write.
        logger.warning("MemoryGateway could not accept write, queueing: %s", e)
        stamp = datetime.now(UTC)
        coord = make_coord(tenant_id, kind, stamp, payload.content)
        await durable_accept_memory(
            text=payload.content,
            tenant_id=tenant_id,
            kind=kind,
            coord=coord,
            source="api",
            ts=stamp,
            error=str(e),
        )
        return {
            "success": True,
            "memory_id": coord,
            "degraded": True,
            "queued": True,
            "queue": get_memory_setting("MEMORY_WAL_TOPIC"),
            "message": get_message(SuccessCode.MEMORY_STORED),
        }


@router.delete(
    "/{memory_id}",
    summary="Delete memory",
    auth=AuthBearer(),
)
async def delete_memory(request, memory_id: str) -> dict:
    """Delete a memory.

    Per SRS UC-05: DELETE /api/v2/memory/{id}
    """
    await authorize(request, action="resource:memory_delete", resource="memory")
    from services.common.memory_gateway import get_memory_gateway

    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for delete")
    tenant_id = request.auth.effective_tenant_id
    gateway = get_memory_gateway()
    success = await gateway.forget(memory_id, tenant_id)

    return {
        "success": success,
        "memory_id": memory_id,
        "message": (
            get_message(SuccessCode.MEMORY_DELETED)
            if success
            else get_message(ErrorCode.MEMORY_DELETE_FAILED)
        ),
    }


@router.get(
    "/pending",
    summary="Get pending sync count",
    auth=AuthBearer(),
)
async def get_pending_count(request) -> dict:
    """Degraded status for the UI (Kafka WAL queue ownership)."""
    await authorize(request, action="resource:memory_read", resource="memory")
    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for pending count")
    tenant_id = request.auth.effective_tenant_id
    from services.common.degraded_memory_queue import degraded_pending_count

    return await degraded_pending_count(tenant_id)


@router.get(
    "/stats",
    summary="Get memory statistics",
    auth=AuthBearer(),
)
async def get_memory_stats(request) -> dict:
    """Get memory statistics for the current tenant via SomaBrain + Kafka WAL."""
    await authorize(request, action="resource:memory_read", resource="memory")
    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for stats")
    tenant_id = request.auth.effective_tenant_id

    total = 0
    degraded = False
    try:
        from services.common.memory_gateway import get_memory_gateway

        gateway = get_memory_gateway()
        hits = await gateway.recall("*", 1, tenant_id)
        total = len(hits or [])
    except Exception:
        degraded = True

    status = {}
    try:
        from services.common.degraded_memory_queue import degraded_pending_count

        status = await degraded_pending_count(tenant_id)
    except Exception:
        status = {"degraded": True}

    return {
        "tenant_id": tenant_id,
        "total_memories": total,
        "degraded": bool(status.get("degraded") or degraded),
        "queue": status.get("queue"),
        "brain_reachable": bool(status.get("brain_reachable", not degraded)),
    }
