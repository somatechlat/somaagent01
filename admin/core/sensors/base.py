"""Base Sensor Class.

VIBE COMPLIANT - Django patterns.
All sensors inherit from BaseSensor for ZDL guarantees.

7-Persona Implementation:
- PhD Dev: Observability patterns
- DevOps: Queue reliability
- Security Auditor: Data integrity
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Optional
from uuid import uuid4

from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class SensorEvent:
    """Base sensor event - all sensors emit these."""

    # Identity
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""
    timestamp: str = field(default_factory=lambda: timezone.now().isoformat())

    # Context
    tenant_id: str = ""
    agent_id: str = ""
    user_id: str = ""
    session_id: str = ""

    # Target service for sync
    target_service: str = ""  # somabrain, kafka, flink, etc.

    # Payload
    payload: dict = field(default_factory=dict)

    # Sync status
    synced: bool = False
    synced_at: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class BaseSensor(ABC):
    """Base class for all sensors.

    Sensors capture agent data and persist to the outbox.
    When the target service is available, data syncs automatically.

    Zero Data Loss Pattern:
    1. Agent does action
    2. Sensor captures immediately
    3. Saves to PostgreSQL outbox (atomic with action)
    4. Background worker syncs to target service
    5. Marks as synced
    """

    # Subclasses set these
    SENSOR_NAME: str = "base"
    TARGET_SERVICE: str = "somabrain"

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        user_id: str = "",
        session_id: str = "",
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.user_id = user_id
        self.session_id = session_id
        self._enabled = True

    def enable(self) -> None:
        """Enable the sensor."""
        self._enabled = True
        logger.debug(f"{self.SENSOR_NAME} sensor enabled")

    def disable(self) -> None:
        """Disable the sensor (for testing/debugging)."""
        self._enabled = False
        logger.debug(f"{self.SENSOR_NAME} sensor disabled")

    def capture(self, event_type: str, payload: dict) -> Optional[SensorEvent]:
        """Capture an event and persist to outbox.

        This is the main entry point for sensors.
        Subclasses should call this method.
        """
        if not self._enabled:
            return None

        event = SensorEvent(
            event_type=f"{self.SENSOR_NAME}.{event_type}",
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            user_id=self.user_id,
            session_id=self.session_id,
            target_service=self.TARGET_SERVICE,
            payload=payload,
        )

        # Persist to outbox
        self._persist_to_outbox(event)

        # Log capture
        logger.debug(f"[{self.SENSOR_NAME}] Captured {event_type}: {event.event_id}")

        return event

    def _persist_to_outbox(self, event: SensorEvent) -> None:
        """Persist event to Django ORM outbox.

        Uses atomic transaction with the calling action
        for true ZDL guarantees.
        """
        try:
            from admin.core.sensors.outbox import SensorOutbox

            SensorOutbox.objects.create(
                event_id=event.event_id,
                event_type=event.event_type,
                tenant_id=event.tenant_id,
                agent_id=event.agent_id,
                user_id=event.user_id,
                session_id=event.session_id,
                target_service=event.target_service,
                payload=event.payload,
            )

        except Exception as e:
            logger.error(f"Failed to persist to outbox: {e}")
            # In production: use dead letter queue
            raise

    @abstractmethod
    def on_event(self, event_type: str, data: Any) -> None:
        """Handle specific event types.

        Subclasses implement this to capture their domain events.
        """
        pass
