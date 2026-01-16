"""Store memory use case.

This use case handles storing conversation events to SomaBrain memory
with policy enforcement.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol

LOGGER = logging.getLogger(__name__)


class MemoryClientProtocol(Protocol):
    """Protocol for memory operations."""

    async def remember(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Store memory payload.

        Args:
            payload: Memory payload to store.

        Returns:
            Storage result with coordinate.
        """
        ...


class PolicyClientProtocol(Protocol):
    """Protocol for policy evaluation."""

    async def evaluate(self, request: Any) -> bool:
        """Evaluate policy request.

        Args:
            request: Policy evaluation request.

        Returns:
            True if allowed, False otherwise.
        """
        ...


class PublisherProtocol(Protocol):
    """Protocol for event publishing."""

    async def publish(
        self,
        topic: str,
        payload: Any,
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
    ) -> Any:
        """Publish an event.

        Args:
            topic: Target topic.
            payload: Event payload.
            dedupe_key: Deduplication key.
            session_id: Session identifier.
            tenant: Tenant identifier.

        Returns:
            Publish result.
        """
        ...


@dataclass
class StoreMemoryInput:
    """Input for store memory use case."""

    content: str
    role: str  # "user" or "assistant"
    session_id: str
    tenant: str
    persona_id: Optional[str] = None
    event_id: Optional[str] = None
    attachments: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StoreMemoryOutput:
    """Output from store memory use case."""

    success: bool
    coordinate: Optional[str] = None
    policy_denied: bool = False
    error: Optional[str] = None


class StoreMemoryUseCase:
    """Use case for storing conversation memory."""

    def __init__(
        self,
        memory_client: MemoryClientProtocol,
        policy_client: PolicyClientProtocol,
        publisher: PublisherProtocol,
        wal_topic: str = "memory.wal",
        namespace: str = "default",
    ):
        """Initialize the instance."""

        self._memory_client = memory_client
        self._policy_client = policy_client
        self._publisher = publisher
        self._wal_topic = wal_topic
        self._namespace = namespace

    async def execute(self, input_data: StoreMemoryInput) -> StoreMemoryOutput:
        """Store memory with policy check."""
        # Build payload
        payload = self._build_payload(input_data)

        # Check policy
        allowed = await self._check_policy(input_data, payload)
        if not allowed:
            LOGGER.info(
                "memory.write denied by policy",
                extra={"session_id": input_data.session_id, "role": input_data.role},
            )
            return StoreMemoryOutput(success=False, policy_denied=True)

        # Store to memory
        try:
            result = await self._memory_client.remember(payload)
            coordinate = (result or {}).get("coordinate") or (result or {}).get("coord")

            # Publish to WAL
            await self._publish_wal(input_data, payload, result)

            return StoreMemoryOutput(success=True, coordinate=coordinate)

        except Exception as e:
            LOGGER.warning(f"Memory store failed: {e}")
            return StoreMemoryOutput(success=False, error=str(e))

    def _build_payload(self, input_data: StoreMemoryInput) -> Dict[str, Any]:
        """Build memory payload."""
        from services.common.idempotency import generate_for_memory_payload

        payload = {
            "id": input_data.event_id or str(uuid.uuid4()),
            "type": "conversation_event",
            "role": input_data.role,
            "content": input_data.content,
            "attachments": input_data.attachments,
            "session_id": input_data.session_id,
            "persona_id": input_data.persona_id,
            "metadata": {
                **input_data.metadata,
                "agent_profile_id": input_data.metadata.get("agent_profile_id"),
                "universe_id": input_data.metadata.get("universe_id") or self._namespace,
            },
        }
        payload["idempotency_key"] = generate_for_memory_payload(payload)
        return payload

    async def _check_policy(self, input_data: StoreMemoryInput, payload: Dict[str, Any]) -> bool:
        """Check if memory write is allowed by policy."""
        try:
            from services.common.policy_client import PolicyRequest

            return await self._policy_client.evaluate(
                PolicyRequest(
                    tenant=input_data.tenant,
                    persona_id=input_data.persona_id,
                    action="memory.write",
                    resource="somabrain",
                    context={
                        "payload_type": payload.get("type"),
                        "role": payload.get("role"),
                        "session_id": input_data.session_id,
                        "metadata": payload.get("metadata", {}),
                    },
                )
            )
        except Exception:
            LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy")
            return False

    async def _publish_wal(
        self,
        input_data: StoreMemoryInput,
        payload: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """Publish memory write to WAL topic."""
        try:
            wal_event = {
                "type": "memory.write",
                "role": input_data.role,
                "session_id": input_data.session_id,
                "persona_id": input_data.persona_id,
                "tenant": input_data.tenant,
                "payload": payload,
                "result": {
                    "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                    "trace_id": (result or {}).get("trace_id"),
                    "request_id": (result or {}).get("request_id"),
                },
                "timestamp": time.time(),
            }
            await self._publisher.publish(
                self._wal_topic,
                wal_event,
                dedupe_key=str(payload.get("id")),
                session_id=input_data.session_id,
                tenant=input_data.tenant,
            )
        except Exception:
            LOGGER.debug("Failed to publish memory WAL", exc_info=True)
