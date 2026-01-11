"""SomaBrain Event Bridge - Kafka/Flink Integration.


Captures ALL agent observable events for cognitive learning.

Architecture:
    Agent → Kafka → Flink → SomaBrain

Degraded Mode:
    - Agent remembers CURRENT session (Redis/local)
    - Agent CANNOT recall PAST memories (SomaBrain down)
    - Agent QUEUES memories for later sync
    - Flink CAPTURES everything for later persistence

7-Persona Implementation:
- PhD Dev: Cognitive event patterns
- DevOps: Kafka/Flink integration
- ML Eng: Memory consolidation patterns
- Security Auditor: Event integrity
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import List, Optional
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache  # Django cache (Redis) for session memory
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_BOOTSTRAP_SERVERS  # VIBE: No fallback - fail fast

# Kafka Topics for Agent Events → SomaBrain
SOMABRAIN_KAFKA_TOPICS = {
    # Core cognitive events
    "agent_act": "soma.agent.act",
    "agent_thoughts": "soma.agent.thoughts",
    "agent_output": "soma.agent.output",
    # Memory events
    "memory_create": "soma.memory.create",
    "memory_recall": "soma.memory.recall",
    "memory_queue": "soma.memory.queue",  # Degraded mode queue
    # Neuromodulator events
    "neuromodulators": "soma.neuromodulators.state",
    # Adaptation events
    "adaptation": "soma.adaptation.events",
    # Sleep/consolidation events
    "sleep_cycle": "soma.sleep.cycles",
    # Context events
    "conversation_context": "soma.context.conversation",
    "session_context": "soma.context.session",
    # Learning events
    "learning_signal": "soma.learning.signals",
    "salience": "soma.learning.salience",
}


# =============================================================================
# EVENT SCHEMAS - EVERYTHING THE AGENT DOES
# =============================================================================


@dataclass
class AgentActEvent:
    """Complete agent action event - captures EVERYTHING."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: timezone.now().isoformat())

    # Identity
    tenant_id: str = ""
    agent_id: str = ""
    user_id: str = ""
    session_id: str = ""
    conversation_id: str = ""

    # Input
    input_text: str = ""
    input_tokens: int = 0
    context: dict = field(default_factory=dict)
    mode: str = "FULL"

    # Output
    output_text: str = ""
    output_tokens: int = 0
    thoughts: list = field(default_factory=list)

    # Cognitive state
    salience: float = 0.0
    neuromodulators: dict = field(default_factory=dict)
    adaptation_params: dict = field(default_factory=dict)

    # Performance
    latency_ms: float = 0.0
    model_used: str = ""

    # Processing metadata
    degraded: bool = False  # True if SomaBrain was unavailable
    queued: bool = False  # True if queued for later sync


@dataclass
class MemoryEvent:
    """Memory operation event."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: timezone.now().isoformat())

    tenant_id: str = ""
    agent_id: str = ""
    user_id: str = ""
    session_id: str = ""

    event_type: str = ""  # create, recall, consolidate, queue
    memory_type: str = ""  # episodic, semantic, procedural

    # Memory content
    content: str = ""
    embedding: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # For recall events
    query: str = ""
    recall_score: float = 0.0
    recalled_count: int = 0

    # Status
    synced_to_brain: bool = False
    queued: bool = False


@dataclass
class SessionContext:
    """Session-level context for degraded mode."""

    session_id: str
    tenant_id: str
    agent_id: str
    user_id: str

    # Current conversation
    messages: list = field(default_factory=list)
    context_window: int = 10  # Last N messages

    # Session metadata
    started_at: str = field(default_factory=lambda: timezone.now().isoformat())
    last_activity: str = field(default_factory=lambda: timezone.now().isoformat())

    # Degraded mode flag
    somabrain_available: bool = True

    # Pending queue
    pending_memories: list = field(default_factory=list)


# =============================================================================
# SESSION MEMORY (Redis) - FOR DEGRADED MODE
# =============================================================================


class SessionMemoryStore:
    """Django cache (Redis) based session memory for degraded mode.

    When SomaBrain is unavailable:
    - Stores current session context in Redis
    - Queues memories for later sync
    - Maintains conversation history for current session
    """

    CACHE_PREFIX = "soma:session:"
    QUEUE_PREFIX = "soma:queue:"
    TTL = 3600 * 24  # 24 hours

    @classmethod
    def get_session_key(cls, session_id: str) -> str:
        """Retrieve session key.

        Args:
            session_id: The session_id.
        """

        return f"{cls.CACHE_PREFIX}{session_id}"

    @classmethod
    def get_queue_key(cls, tenant_id: str) -> str:
        """Retrieve queue key.

        Args:
            tenant_id: The tenant_id.
        """

        return f"{cls.QUEUE_PREFIX}{tenant_id}"

    @classmethod
    def save_session(cls, context: SessionContext) -> None:
        """Save session context to Redis."""
        key = cls.get_session_key(context.session_id)
        cache.set(key, asdict(context), cls.TTL)
        logger.debug(f"Session saved: {context.session_id}")

    @classmethod
    def get_session(cls, session_id: str) -> Optional[SessionContext]:
        """Get session context from Redis."""
        key = cls.get_session_key(session_id)
        data = cache.get(key)
        if data:
            return SessionContext(**data)
        return None

    @classmethod
    def add_message(cls, session_id: str, role: str, content: str) -> None:
        """Add message to session history."""
        context = cls.get_session(session_id)
        if context:
            context.messages.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": timezone.now().isoformat(),
                }
            )
            # Trim to context window
            if len(context.messages) > context.context_window * 2:
                context.messages = context.messages[-context.context_window :]
            context.last_activity = timezone.now().isoformat()
            cls.save_session(context)

    @classmethod
    def queue_memory(cls, tenant_id: str, memory: MemoryEvent) -> None:
        """Queue memory for later sync to SomaBrain."""
        key = cls.get_queue_key(tenant_id)
        queue = cache.get(key) or []
        queue.append(asdict(memory))
        cache.set(key, queue, cls.TTL * 7)  # 7 days retention
        logger.info(f"Memory queued for later sync: {memory.event_id}")

    @classmethod
    def get_pending_queue(cls, tenant_id: str) -> List[dict]:
        """Get pending memory queue."""
        key = cls.get_queue_key(tenant_id)
        return cache.get(key) or []

    @classmethod
    def clear_queue(cls, tenant_id: str) -> int:
        """Clear pending queue after successful sync."""
        key = cls.get_queue_key(tenant_id)
        queue = cache.get(key) or []
        count = len(queue)
        cache.delete(key)
        logger.info(f"Cleared {count} pending memories for tenant {tenant_id}")
        return count


# =============================================================================
# KAFKA EVENT PUBLISHER
# =============================================================================


class SomaBrainEventPublisher:
    """Publish ALL agent events to Kafka for Flink processing.

    Everything the agent does is captured and sent to Kafka:
    - Agent act (input/output/thoughts)
    - Memory operations
    - Neuromodulator state changes
    - Adaptation parameter updates
    - Learning signals

    Flink processes these events and persists to SomaBrain.
    """

    _producer = None

    @classmethod
    def get_producer(cls):
        """Get or create Kafka producer."""
        if cls._producer is None:
            try:
                from kafka import KafkaProducer

                cls._producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    acks="all",
                    retries=5,
                    retry_backoff_ms=500,
                )
                logger.info(f"SomaBrain Kafka producer connected: {KAFKA_BOOTSTRAP_SERVERS}")
            except Exception as e:
                logger.warning(f"Kafka producer not available: {e}")
                cls._producer = None
        return cls._producer

    @classmethod
    def publish(cls, topic: str, event: dict, key: str = None) -> bool:
        """Publish event to Kafka topic."""
        producer = cls.get_producer()
        if producer:
            try:
                producer.send(
                    topic,
                    value=event,
                    key=key.encode("utf-8") if key else None,
                )
                producer.flush()
                logger.debug(f"Published to {topic}: {event.get('event_id', 'unknown')}")
                return True
            except Exception as e:
                logger.error(f"Kafka publish failed: {e}")
        return False

    @classmethod
    def publish_agent_act(cls, event: AgentActEvent) -> bool:
        """Publish agent act event - captures EVERYTHING about the action."""
        return cls.publish(
            SOMABRAIN_KAFKA_TOPICS["agent_act"],
            asdict(event),
            key=event.agent_id,
        )

    @classmethod
    def publish_memory_event(cls, event: MemoryEvent) -> bool:
        """Publish memory event."""
        topic_key = "memory_queue" if event.queued else f"memory_{event.event_type}"
        topic = SOMABRAIN_KAFKA_TOPICS.get(topic_key, SOMABRAIN_KAFKA_TOPICS["memory_create"])
        return cls.publish(topic, asdict(event), key=event.tenant_id)

    @classmethod
    def publish_neuromodulators(cls, agent_id: str, tenant_id: str, neuromodulators: dict) -> bool:
        """Publish neuromodulator state for learning."""
        event = {
            "event_id": str(uuid4()),
            "timestamp": timezone.now().isoformat(),
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "neuromodulators": neuromodulators,
        }
        return cls.publish(
            SOMABRAIN_KAFKA_TOPICS["neuromodulators"],
            event,
            key=agent_id,
        )

    @classmethod
    def publish_salience(
        cls, agent_id: str, tenant_id: str, salience: float, context: dict = None
    ) -> bool:
        """Publish salience signal for learning."""
        event = {
            "event_id": str(uuid4()),
            "timestamp": timezone.now().isoformat(),
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "salience": salience,
            "context": context or {},
        }
        return cls.publish(
            SOMABRAIN_KAFKA_TOPICS["salience"],
            event,
            key=agent_id,
        )

    @classmethod
    def publish_session_context(cls, context: SessionContext) -> bool:
        """Publish session context for Flink processing."""
        return cls.publish(
            SOMABRAIN_KAFKA_TOPICS["session_context"],
            asdict(context),
            key=context.session_id,
        )


# =============================================================================
# AGENT EVENT CAPTURE MIDDLEWARE
# =============================================================================


class AgentEventCapture:
    """Capture ALL agent events and publish to Kafka.

    This is the bridge between Agent and SomaBrain via Flink.

    Usage:
        capture = AgentEventCapture(tenant_id, agent_id, user_id, session_id)

        # Before action
        capture.start_act(input_text, context)

        # After action
        capture.complete_act(output, thoughts, neuromodulators, salience, latency_ms)

        # Automatically published to Kafka → Flink → SomaBrain
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        user_id: str,
        session_id: str,
        conversation_id: str = None,
    ):
        """Initialize the instance."""

        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_id = conversation_id or str(uuid4())

        self._current_event: Optional[AgentActEvent] = None
        self._start_time: float = 0.0

        # Initialize or get session
        self._session = SessionMemoryStore.get_session(session_id)
        if not self._session:
            self._session = SessionContext(
                session_id=session_id,
                tenant_id=tenant_id,
                agent_id=agent_id,
                user_id=user_id,
            )
            SessionMemoryStore.save_session(self._session)

    def start_act(self, input_text: str, context: dict = None, mode: str = "FULL") -> None:
        """Start capturing an agent action."""
        self._start_time = time.time()
        self._current_event = AgentActEvent(
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            user_id=self.user_id,
            session_id=self.session_id,
            conversation_id=self.conversation_id,
            input_text=input_text,
            context=context or {},
            mode=mode,
        )

        # Save to session memory
        SessionMemoryStore.add_message(self.session_id, "user", input_text)

    def complete_act(
        self,
        output_text: str,
        thoughts: list = None,
        neuromodulators: dict = None,
        salience: float = 0.0,
        model_used: str = "",
        degraded: bool = False,
    ) -> AgentActEvent:
        """Complete capturing and publish event."""
        if not self._current_event:
            raise ValueError("No action started. Call start_act() first.")

        self._current_event.output_text = output_text
        self._current_event.thoughts = thoughts or []
        self._current_event.neuromodulators = neuromodulators or {}
        self._current_event.salience = salience
        self._current_event.model_used = model_used
        self._current_event.degraded = degraded
        self._current_event.latency_ms = (time.time() - self._start_time) * 1000

        # Save to session memory
        SessionMemoryStore.add_message(self.session_id, "assistant", output_text)

        # Publish to Kafka
        SomaBrainEventPublisher.publish_agent_act(self._current_event)

        # Publish neuromodulators if present
        if neuromodulators:
            SomaBrainEventPublisher.publish_neuromodulators(
                self.agent_id, self.tenant_id, neuromodulators
            )

        # Publish salience
        if salience > 0:
            SomaBrainEventPublisher.publish_salience(
                self.agent_id,
                self.tenant_id,
                salience,
                {"input": self._current_event.input_text[:100]},
            )

        event = self._current_event
        self._current_event = None
        return event

    def queue_memory(
        self, content: str, memory_type: str = "episodic", metadata: dict = None
    ) -> None:
        """Queue memory for later sync when SomaBrain unavailable."""
        memory = MemoryEvent(
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            user_id=self.user_id,
            session_id=self.session_id,
            event_type="create",
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
            queued=True,
            synced_to_brain=False,
        )

        # Save to Redis queue
        SessionMemoryStore.queue_memory(self.tenant_id, memory)

        # Publish to Kafka for Flink processing
        SomaBrainEventPublisher.publish_memory_event(memory)

    def get_session_history(self) -> list:
        """Get current session conversation history."""
        session = SessionMemoryStore.get_session(self.session_id)
        if session:
            return session.messages
        return []

    def is_somabrain_available(self) -> bool:
        """Check if SomaBrain is available."""
        if self._session:
            return self._session.somabrain_available
        return True

    def set_somabrain_status(self, available: bool) -> None:
        """Update SomaBrain availability status."""
        if self._session:
            self._session.somabrain_available = available
            SessionMemoryStore.save_session(self._session)
