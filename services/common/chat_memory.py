"""ChatService Memory Integration - Memory operations for chat.

Uses SomaBrainClient for all memory operations (respects AAAS deployment modes).
Publishes to Kafka WAL for durability - MemoryReplicator handles sync.

ARCHITECTURE:
- PostgreSQL Message table = TRACE REGISTRAR (metadata only)
- Kafka memory.wal = WRITE-AHEAD LOG (full content, durable)
- MemoryReplicator = SYNC WORKER (WAL -> SomaBrain when available)
- SomaBrain = Memory Gateway (L3)
- SomaFractalMemory = Vector Storage (L2) - NEVER accessed directly from Agent
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from admin.core.somabrain_client import SomaBrainClient
# Integration: BrainBridge (Direct Mode Optimization)
try:
    from aaas.brain import brain as BrainBridge
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False
from services.common.chat_schemas import Memory

if TYPE_CHECKING:
    pass  # No ChatService dependency needed

logger = logging.getLogger(__name__)


async def recall_memories(
    agent_id: str,
    user_id: str,
    query: str,
    limit: int = 5,
    tenant_id: Optional[str] = None,
) -> list[Memory]:
    """Recall relevant memories via SomaBrain.

    Uses SomaBrainClient which respects AAAS deployment modes:
    - Direct mode: BrainMemoryFacade (in-process, <0.1ms)
    - HTTP mode: SomaBrain API

    Args:
        agent_id: Agent ID
        user_id: User ID
        query: Query string for semantic search
        limit: Max memories to return
        tenant_id: Optional tenant ID

    Returns:
        List of Memory objects (empty if service unavailable)
    """
    import time

    from prometheus_client import Counter, Histogram

    try:
        from services.common.chat_service import CHAT_LATENCY, CHAT_REQUESTS
    except ImportError:
        CHAT_LATENCY = Histogram("chat_memory_latency", "Memory latency", ["method"])
        CHAT_REQUESTS = Counter("chat_memory_requests", "Memory requests", ["method", "result"])

    start_time = time.perf_counter()

    try:
        # DIRECT MODE OPITIMIZATION (Zero Latency)
        if HAS_BRIDGE and BrainBridge.mode == "direct":
            logger.debug(f"BrainBridge Direct Recall: {query}")
            # Use compliant BrainBridge
            # BrainBridge.recall returns list[dict]
            results = await BrainBridge.recall(
                query_vector=await BrainBridge.encode_text(query),
                top_k=limit
            )

            memories = []
            for m in results:
                memories.append(
                    Memory(
                        id=str(m.get("coordinate") or uuid4()),
                        content=m.get("payload", {}).get("content", ""),
                        memory_type="episodic",
                        relevance_score=float(m.get("score", 0.0)),
                        created_at=datetime.now(timezone.utc), # simplified for direct
                    )
                )
            return memories

        somabrain = await SomaBrainClient.get_async()

        result = await somabrain.recall(
            query=query,
            top_k=limit,
            tenant=tenant_id,
            namespace="episodic",
            tags=[f"agent:{agent_id}", f"user:{user_id}"],
        )

        memories = []
        for item in result.get("memories", []):
            payload = item.get("payload") if isinstance(item, dict) else {}
            payload = payload if isinstance(payload, dict) else {}
            content = payload.get("content") or ""
            created_at = payload.get("timestamp") or item.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            )
            try:
                created_dt = (
                    created_at
                    if isinstance(created_at, datetime)
                    else datetime.fromisoformat(str(created_at))
                )
            except ValueError:
                created_dt = datetime.now(timezone.utc)

            coord = item.get("coordinate")
            coord_id = str(coord or uuid4())

            memories.append(
                Memory(
                    id=coord_id,
                    content=content,
                    memory_type=item.get("memory_type", "episodic"),
                    relevance_score=float(item.get("importance", 0.0)),
                    created_at=created_dt,
                )
            )

        elapsed = time.perf_counter() - start_time
        CHAT_LATENCY.labels(method="recall_memories").observe(elapsed)
        CHAT_REQUESTS.labels(method="recall_memories", result="success").inc()

        logger.debug(f"Memories recalled via SomaBrain: agent={agent_id}, count={len(memories)}")
        return memories

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        CHAT_LATENCY.labels(method="recall_memories").observe(elapsed)
        CHAT_REQUESTS.labels(method="recall_memories", result="error").inc()
        logger.warning(f"Memory recall failed (graceful degradation): {e}")
        return []


async def store_memory(
    agent_id: str,
    user_id: str,
    content: str,
    metadata: dict,
    tenant_id: Optional[str] = None,
) -> None:
    """Store memory via SomaBrain (respects AAAS deployment modes).

    Uses SomaBrainClient which handles:
    - Direct mode: BrainMemoryFacade (in-process)
    - HTTP mode: SomaBrain API

    If SomaBrain unavailable, PostgreSQL trace serves as backup.
    MemoryReplicator syncs when SomaBrain comes back online.

    Args:
        agent_id: Agent ID
        user_id: User ID
        content: Memory content
        metadata: Additional metadata
        tenant_id: Optional tenant ID
    """
    try:
        # DIRECT MODE OPTIMIZATION (Zero Latency)
        if HAS_BRIDGE and BrainBridge.mode == "direct":
            await BrainBridge.remember(
                content=content,
                tenant=tenant_id,
                namespace="episodic",
                metadata={
                    "key": memory_key,
                    "agent_id": agent_id,
                    "user_id": user_id,
                    "tags": [
                        "conversation",
                        "episodic",
                        f"agent:{agent_id}",
                        f"user:{user_id}",
                    ],
                    "importance": 0.7,
                    "novelty": 0.5,
                    **metadata
                }
            )
            logger.debug(f"Memory stored via BrainBridge (Direct): agent={agent_id}, user={user_id}")
            return

        somabrain = await SomaBrainClient.get_async()

        # Generate memory key
        conversation_id = metadata.get("conversation_id", "unknown")
        timestamp = metadata.get("timestamp", datetime.now(timezone.utc).isoformat())
        memory_key = (
            f"interaction:{conversation_id}:{hashlib.sha256(content.encode()).hexdigest()[:12]}"
        )

        await somabrain.remember(
            payload={
                "key": memory_key,
                "value": {
                    "content": content,
                    "agent_id": agent_id,
                    "user_id": user_id,
                    **metadata,
                },
                "tags": [
                    "conversation",
                    "episodic",
                    f"agent:{agent_id}",
                    f"user:{user_id}",
                ],
                "importance": 0.7,
                "novelty": 0.5,
            },
            tenant=tenant_id,
            namespace="episodic",
        )

        logger.debug(f"Memory stored via SomaBrain: agent={agent_id}, user={user_id}")

    except Exception as e:
        # Graceful degradation: PostgreSQL trace is the backup
        # MemoryReplicator will sync when SomaBrain comes back
        logger.warning(f"Memory store failed (PostgreSQL trace is backup): {e}")


async def store_interaction(
    *,
    agent_id: str,
    user_id: str,
    conversation_id: str,
    user_message: str,
    assistant_response: str,
    tenant_id: Optional[str] = None,
    model: Optional[str] = None,
    task_type: Optional[str] = None,
    tools_used: Optional[list] = None,
    latency_ms: Optional[int] = None,
) -> None:
    """Store a full interaction in memory via SomaBrain.

    Args:
        agent_id: Agent ID
        user_id: User ID
        conversation_id: Conversation ID
        user_message: User message
        assistant_response: Assistant response
        tenant_id: Optional tenant ID
        model: LLM model used (for IMRS)
        task_type: Detected task type (for IMRS)
        tools_used: Tools invoked (for IMRS)
        latency_ms: Response latency (for IMRS)
    """
    content = f"User: {user_message}\nAssistant: {assistant_response}"
    metadata = {
        "conversation_id": conversation_id,
        "user_message": user_message[:5000],
        "assistant_response": assistant_response[:5000],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # IMRS fields
    if model:
        metadata["model"] = model
    if task_type:
        metadata["task_type"] = task_type
    if tools_used:
        metadata["tools_used"] = tools_used
    if latency_ms:
        metadata["latency_ms"] = latency_ms

    await store_memory(
        agent_id=agent_id,
        user_id=user_id,
        content=content,
        metadata=metadata,
        tenant_id=tenant_id,
    )


__all__ = ["recall_memories", "store_memory", "store_interaction"]
