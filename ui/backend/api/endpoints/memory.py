"""
Eye of God API - Memory Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- PostgreSQL persistence
- Vector search via Milvus
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Query

from api.schemas import (
    MemoryType,
    MemoryCreate,
    MemoryResponse,
    MemorySearch,
    MemorySearchResult,
    ErrorResponse,
    PaginatedResponse,
)

router = Router(tags=["Memory"])


@router.get(
    "/",
    response={200: List[MemoryResponse]},
    summary="List memories"
)
async def list_memories(
    request: HttpRequest,
    memory_type: Optional[MemoryType] = None,
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> List[MemoryResponse]:
    """
    List memories for the current agent.
    
    Supports filtering by type and minimum importance threshold.
    """
    tenant_id = request.auth.get("tenant_id")
    agent_id = request.auth.get("agent_id", request.auth.get("user_id"))
    
    # Import here to avoid circular imports
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    memories = await client.list_memories(
        tenant_id=tenant_id,
        agent_id=agent_id,
        memory_type=memory_type.value if memory_type else None,
        min_importance=min_importance,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    return [
        MemoryResponse(
            id=m["id"],
            tenant_id=UUID(m["tenant_id"]),
            agent_id=UUID(m["agent_id"]),
            content=m["content"],
            memory_type=MemoryType(m["memory_type"]),
            importance=m["importance"],
            access_count=m.get("access_count", 0),
            last_accessed=m["last_accessed"],
            created_at=m["created_at"],
            metadata=m.get("metadata", {}),
        )
        for m in memories
    ]


@router.post(
    "/",
    response={201: MemoryResponse},
    summary="Create memory"
)
async def create_memory(request: HttpRequest, payload: MemoryCreate) -> MemoryResponse:
    """
    Create a new memory entry.
    
    Memory will be vectorized and stored for semantic search.
    """
    tenant_id = request.auth.get("tenant_id")
    agent_id = request.auth.get("agent_id", request.auth.get("user_id"))
    
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    memory = await client.store_memory(
        tenant_id=tenant_id,
        agent_id=agent_id,
        content=payload.content,
        memory_type=payload.memory_type.value,
        importance=payload.importance,
        metadata=payload.metadata,
    )
    
    return MemoryResponse(
        id=memory["id"],
        tenant_id=UUID(memory["tenant_id"]),
        agent_id=UUID(memory["agent_id"]),
        content=memory["content"],
        memory_type=MemoryType(memory["memory_type"]),
        importance=memory["importance"],
        access_count=0,
        last_accessed=datetime.utcnow(),
        created_at=memory["created_at"],
        metadata=memory.get("metadata", {}),
    )


@router.post(
    "/search",
    response={200: List[MemorySearchResult]},
    summary="Search memories"
)
async def search_memories(
    request: HttpRequest, 
    payload: MemorySearch
) -> List[MemorySearchResult]:
    """
    Semantic search across memories.
    
    Uses vector similarity to find relevant memories.
    """
    tenant_id = request.auth.get("tenant_id")
    agent_id = request.auth.get("agent_id", request.auth.get("user_id"))
    
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    results = await client.search_memories(
        tenant_id=tenant_id,
        agent_id=agent_id,
        query=payload.query,
        memory_type=payload.memory_type.value if payload.memory_type else None,
        limit=payload.limit,
        min_importance=payload.min_importance,
    )
    
    return [
        MemorySearchResult(
            memory=MemoryResponse(
                id=r["memory"]["id"],
                tenant_id=UUID(r["memory"]["tenant_id"]),
                agent_id=UUID(r["memory"]["agent_id"]),
                content=r["memory"]["content"],
                memory_type=MemoryType(r["memory"]["memory_type"]),
                importance=r["memory"]["importance"],
                access_count=r["memory"].get("access_count", 0),
                last_accessed=r["memory"]["last_accessed"],
                created_at=r["memory"]["created_at"],
                metadata=r["memory"].get("metadata", {}),
            ),
            score=r["score"],
        )
        for r in results
    ]


@router.get(
    "/{memory_id}",
    response={200: MemoryResponse, 404: ErrorResponse},
    summary="Get memory by ID"
)
async def get_memory(request: HttpRequest, memory_id: UUID) -> MemoryResponse:
    """
    Get a specific memory and increment access count.
    """
    tenant_id = request.auth.get("tenant_id")
    
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    memory = await client.get_memory(
        tenant_id=tenant_id,
        memory_id=str(memory_id),
        increment_access=True,
    )
    
    if not memory:
        raise ValueError("Memory not found")
    
    return MemoryResponse(
        id=memory["id"],
        tenant_id=UUID(memory["tenant_id"]),
        agent_id=UUID(memory["agent_id"]),
        content=memory["content"],
        memory_type=MemoryType(memory["memory_type"]),
        importance=memory["importance"],
        access_count=memory.get("access_count", 0),
        last_accessed=memory["last_accessed"],
        created_at=memory["created_at"],
        metadata=memory.get("metadata", {}),
    )


@router.delete(
    "/{memory_id}",
    response={204: None, 404: ErrorResponse},
    summary="Delete memory"
)
async def delete_memory(request: HttpRequest, memory_id: UUID) -> None:
    """
    Delete a memory by ID.
    """
    tenant_id = request.auth.get("tenant_id")
    
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    deleted = await client.delete_memory(
        tenant_id=tenant_id,
        memory_id=str(memory_id),
    )
    
    if not deleted:
        raise ValueError("Memory not found")


@router.patch(
    "/{memory_id}/importance",
    response={200: MemoryResponse},
    summary="Update memory importance"
)
async def update_importance(
    request: HttpRequest, 
    memory_id: UUID, 
    importance: float = Query(..., ge=0.0, le=1.0)
) -> MemoryResponse:
    """
    Update the importance score of a memory.
    """
    tenant_id = request.auth.get("tenant_id")
    
    from somabrain.client import SomaBrainClient
    
    client = SomaBrainClient()
    
    memory = await client.update_importance(
        tenant_id=tenant_id,
        memory_id=str(memory_id),
        importance=importance,
    )
    
    if not memory:
        raise ValueError("Memory not found")
    
    return MemoryResponse(
        id=memory["id"],
        tenant_id=UUID(memory["tenant_id"]),
        agent_id=UUID(memory["agent_id"]),
        content=memory["content"],
        memory_type=MemoryType(memory["memory_type"]),
        importance=memory["importance"],
        access_count=memory.get("access_count", 0),
        last_accessed=memory["last_accessed"],
        created_at=memory["created_at"],
        metadata=memory.get("metadata", {}),
    )
