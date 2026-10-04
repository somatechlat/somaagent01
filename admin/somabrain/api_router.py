"""SomaBrain Memory API Router.


Per CANONICAL_USER_JOURNEYS_SRS.md UC-05: View/Manage Memories.
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.authorization import authorize
from admin.common.exceptions import UnauthorizedError
from admin.common.messages import ErrorCode, get_message, SuccessCode
from admin.core.somabrain_client import SomaBrainError

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


@router.get(
    "/recent",
    summary="Get recent memories",
    auth=AuthBearer(),
)
async def get_recent_memories(
    request,
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Get recent memories for the current user.

    Per SRS UC-05: GET /api/v2/memory/recent
    """
    await authorize(request, action="resource:memory_read", resource="memory")
    from admin.core.somabrain_client import get_somabrain_client

    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for recent memories")
    tenant_id = request.auth.effective_tenant_id
    client = get_somabrain_client()
    if client is None:
        raise SomaBrainError("SomaBrain not configured", status_code=503)

    try:
        memories = await client.get_recent(tenant_id=tenant_id, limit=limit)

        items = [
            MemoryOut(
                id=m.get("id", ""),
                content=m.get("content", ""),
                memory_type=m.get("memory_type", "episodic"),
                created_at=m.get("created_at", ""),
                metadata=m.get("metadata"),
            ).model_dump()
            for m in memories
        ]

        return {"memories": items}

    except Exception as e:
        logger.error("Get recent failed: %s", e)
        return {"memories": [], "error": get_message(ErrorCode.SOMABRAIN_UNAVAILABLE)}


@router.post(
    "",
    summary="Create memory",
    auth=AuthBearer(),
)
async def create_memory(request, payload: MemoryCreateRequest) -> dict:
    """Store a new memory.

    Creates a memory record that will be synced to SomaBrain.
    Uses ZDL pattern if SomaBrain is unavailable.
    """
    await authorize(request, action="resource:memory_write", resource="memory")
    from services.common.memory_gateway import get_memory_gateway

    if not getattr(request, "auth", None) or not request.auth.effective_tenant_id:
        raise UnauthorizedError("Tenant context required for memory creation")
    tenant_id = request.auth.effective_tenant_id

    try:
        gateway = get_memory_gateway()
        acks = await gateway.remember_text(
            payload.content,
            tenant_id=tenant_id,
            kind=str(payload.memory_type or "episodic"),
            source="api",
        )
        accepted = next((a for a in acks if a.ok), None)
        if accepted is None:
            # The seam already durable-accepted the write (T-6). Surface the
            # failed ack and queue for replay rather than inventing an id.
            error = next((a.error for a in acks if a.error), "memory write not accepted")
            logger.warning("MemoryGateway write not accepted: %s", error)
            from services.common.degraded_memory_queue import publish_degraded_memory

            queued = await publish_degraded_memory(
                text=payload.content,
                tenant_id=tenant_id,
                namespace="chat_history",
                kind=str(payload.memory_type or "episodic"),
                source="degraded-api",
                error=str(error),
            )
            return {
                "success": True,
                "memory_id": queued.get("id"),
                "degraded": True,
                "queued": True,
                "queue": queued.get("channel"),
                "message": get_message(SuccessCode.MEMORY_STORED),
            }

        return {
            "success": True,
            "memory_id": accepted.coord,
            "message": get_message(SuccessCode.MEMORY_STORED),
        }

    except Exception as e:
        # ZDL: degraded mode — Kafka WAL queue, replayed by memory-replicator.
        logger.warning("MemoryGateway unavailable, queueing memory to Kafka WAL: %s", e)
        from services.common.degraded_memory_queue import publish_degraded_memory

        queued = await publish_degraded_memory(
            text=payload.content,
            tenant_id=tenant_id,
            namespace="chat_history",
            kind=str(payload.memory_type or "episodic"),
            source="degraded-api",
            error=str(e),
        )
        return {
            "success": True,
            "memory_id": queued.get("id"),
            "degraded": True,
            "queued": True,
            "queue": queued.get("channel"),
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
