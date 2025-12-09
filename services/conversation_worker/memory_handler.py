"""Memory operations handler for conversation worker.

This module extracts SomaBrain memory operations from the ConversationWorker
to reduce main.py file size.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING

from prometheus_client import Counter, Gauge

from services.common.idempotency import generate_for_memory_payload
from services.common.policy_client import PolicyRequest

if TYPE_CHECKING:
    from services.conversation_worker.main import ConversationWorker

LOGGER = logging.getLogger(__name__)

# Metrics
MEMORY_OPERATIONS_COUNTER = Counter(
    "conversation_worker_memory_ops_total",
    "Total memory operations",
    labelnames=("operation", "result"),
)
MEMORY_BUFFER_GAUGE = Gauge(
    "conversation_worker_memory_buffer_size",
    "Number of buffered memory items",
)


class MemoryHandler:
    """Handle memory operations for conversation worker."""
    
    def __init__(self, worker: "ConversationWorker"):
        """Initialize memory handler.
        
        Args:
            worker: The parent ConversationWorker instance
        """
        self.worker = worker
        self._transient_buffer: list[Dict[str, Any]] = []
    
    async def store_user_message(
        self,
        event: Dict[str, Any],
        session_id: str,
        tenant: str,
        metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Store a user message to SomaBrain memory.
        
        Args:
            event: The user message event
            session_id: Session identifier
            tenant: Tenant identifier
            metadata: Enriched metadata
            
        Returns:
            Memory storage result or None if denied/failed
        """
        payload = self._build_memory_payload(
            event=event,
            session_id=session_id,
            role="user",
            metadata=metadata,
        )
        
        # Check policy
        allowed = await self._check_memory_policy(
            tenant=tenant,
            persona_id=event.get("persona_id"),
            payload=payload,
            session_id=session_id,
        )
        
        if not allowed:
            MEMORY_OPERATIONS_COUNTER.labels(operation="user_store", result="denied").inc()
            return None
        
        return await self._store_memory(
            payload=payload,
            tenant=tenant,
            session_id=session_id,
            persona_id=event.get("persona_id"),
            operation="user_store",
        )
    
    async def store_assistant_response(
        self,
        response_text: str,
        session_id: str,
        persona_id: Optional[str],
        tenant: str,
        metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Store an assistant response to SomaBrain memory.
        
        Args:
            response_text: The assistant's response
            session_id: Session identifier
            persona_id: Persona identifier
            tenant: Tenant identifier
            metadata: Response metadata
            
        Returns:
            Memory storage result or None if denied/failed
        """
        payload = {
            "id": str(uuid.uuid4()),
            "type": "conversation_event",
            "role": "assistant",
            "content": response_text,
            "session_id": session_id,
            "persona_id": persona_id,
            "metadata": metadata,
        }
        payload["idempotency_key"] = generate_for_memory_payload(payload)
        
        # Check policy
        allowed = await self._check_memory_policy(
            tenant=tenant,
            persona_id=persona_id,
            payload=payload,
            session_id=session_id,
        )
        
        if not allowed:
            MEMORY_OPERATIONS_COUNTER.labels(operation="assistant_store", result="denied").inc()
            return None
        
        return await self._store_memory(
            payload=payload,
            tenant=tenant,
            session_id=session_id,
            persona_id=persona_id,
            operation="assistant_store",
        )
    
    def _build_memory_payload(
        self,
        event: Dict[str, Any],
        session_id: str,
        role: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a memory payload from an event.
        
        Args:
            event: The source event
            session_id: Session identifier
            role: Message role (user/assistant)
            metadata: Enriched metadata
            
        Returns:
            Memory payload dict
        """
        from src.core.config import cfg
        
        payload = {
            "id": event.get("event_id") or str(uuid.uuid4()),
            "type": "conversation_event",
            "role": role,
            "content": event.get("message", ""),
            "attachments": event.get("attachments", []) or [],
            "session_id": session_id,
            "persona_id": event.get("persona_id"),
            "metadata": {
                **dict(metadata),
                "agent_profile_id": metadata.get("agent_profile_id"),
                "universe_id": metadata.get("universe_id") or cfg.env("SOMA_NAMESPACE"),
            },
        }
        payload["idempotency_key"] = generate_for_memory_payload(payload)
        return payload
    
    async def _check_memory_policy(
        self,
        tenant: str,
        persona_id: Optional[str],
        payload: Dict[str, Any],
        session_id: str,
    ) -> bool:
        """Check if memory write is allowed by policy.
        
        Args:
            tenant: Tenant identifier
            persona_id: Persona identifier
            payload: Memory payload
            session_id: Session identifier
            
        Returns:
            True if allowed, False otherwise
        """
        from observability.metrics import thinking_policy_seconds
        
        try:
            with thinking_policy_seconds.labels(policy="memory.write").time():
                return await self.worker.policy_client.evaluate(
                    PolicyRequest(
                        tenant=tenant,
                        persona_id=persona_id,
                        action="memory.write",
                        resource="somabrain",
                        context={
                            "payload_type": payload.get("type"),
                            "role": payload.get("role"),
                            "session_id": session_id,
                            "metadata": payload.get("metadata", {}),
                        },
                    )
                )
        except Exception:
            LOGGER.warning(
                "OPA memory.write check failed; denying by fail-closed policy",
                exc_info=True,
            )
            return False
    
    async def _store_memory(
        self,
        payload: Dict[str, Any],
        tenant: str,
        session_id: str,
        persona_id: Optional[str],
        operation: str,
    ) -> Optional[Dict[str, Any]]:
        """Store memory to SomaBrain with fallback to outbox.
        
        Args:
            payload: Memory payload
            tenant: Tenant identifier
            session_id: Session identifier
            persona_id: Persona identifier
            operation: Operation name for metrics
            
        Returns:
            Storage result or None on failure
        """
        try:
            result = await self.worker.soma.remember(payload)
            MEMORY_OPERATIONS_COUNTER.labels(operation=operation, result="success").inc()
            
            # Publish to WAL
            await self._publish_memory_wal(
                payload=payload,
                result=result,
                tenant=tenant,
                session_id=session_id,
                persona_id=persona_id,
            )
            
            return result
            
        except Exception as e:
            LOGGER.warning(f"SomaBrain remember failed: {e}")
            MEMORY_OPERATIONS_COUNTER.labels(operation=operation, result="degraded").inc()
            
            # Mark SomaBrain as degraded
            self.worker._enter_somabrain_degraded("remember_failure")
            
            # Enqueue for retry
            try:
                await self.worker.mem_outbox.enqueue(
                    payload=payload,
                    tenant=tenant,
                    session_id=session_id,
                    persona_id=persona_id,
                    idempotency_key=payload.get("idempotency_key"),
                    dedupe_key=str(payload.get("id")),
                )
            except Exception:
                LOGGER.debug(f"Failed to enqueue memory write for retry ({operation})", exc_info=True)
            
            return None
    
    async def _publish_memory_wal(
        self,
        payload: Dict[str, Any],
        result: Dict[str, Any],
        tenant: str,
        session_id: str,
        persona_id: Optional[str],
    ) -> None:
        """Publish memory write to WAL topic.
        
        Args:
            payload: Memory payload
            result: Storage result
            tenant: Tenant identifier
            session_id: Session identifier
            persona_id: Persona identifier
        """
        from src.core.config import cfg
        
        wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
        
        try:
            wal_event = {
                "type": "memory.write",
                "role": payload.get("role"),
                "session_id": session_id,
                "persona_id": persona_id,
                "tenant": tenant,
                "payload": payload,
                "result": {
                    "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                    "trace_id": (result or {}).get("trace_id"),
                    "request_id": (result or {}).get("request_id"),
                },
                "timestamp": time.time(),
            }
            await self.worker.publisher.publish(
                wal_topic,
                wal_event,
                dedupe_key=str(payload.get("id")),
                session_id=session_id,
                tenant=tenant,
            )
        except Exception:
            LOGGER.debug("Failed to publish memory WAL", exc_info=True)
