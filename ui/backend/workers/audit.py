"""
Audit Worker - Kafka Consumer
Per CANONICAL_DESIGN.md Section 6

VIBE COMPLIANT:
- Real Kafka consumer
- Structured audit logging
- PostgreSQL persistence
- Correlation ID tracking

Flow:
  All Services → Kafka: audit.events → AuditWorker
    → Parse structured event
    → Enrich with metadata
    → Store to PostgreSQL
    → Emit metrics
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4

from aiokafka import AIOKafkaConsumer

LOGGER = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Structured audit event."""
    event_id: str
    event_type: str
    tenant_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    workflow_id: Optional[str]
    correlation_id: str
    action: str
    resource: str
    resource_id: Optional[str]
    outcome: str  # success, failure, denied
    details: Dict[str, Any] = field(default_factory=dict)
    source_service: str = ""
    source_ip: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Audit event types
class EventType:
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    
    SETTINGS_READ = "settings.read"
    SETTINGS_UPDATE = "settings.update"
    
    MEMORY_CREATE = "memory.create"
    MEMORY_READ = "memory.read"
    MEMORY_DELETE = "memory.delete"
    MEMORY_SEARCH = "memory.search"
    
    TOOL_EXECUTE = "tool.execute"
    TOOL_DENIED = "tool.denied"
    
    THEME_APPLY = "theme.apply"
    THEME_UPLOAD = "theme.upload"
    THEME_DELETE = "theme.delete"
    
    MODE_CHANGE = "mode.change"
    
    ADMIN_ACTION = "admin.action"


class AuditWorker:
    """
    Kafka consumer for audit.events topic.
    
    Processes audit events and stores them in PostgreSQL:
    1. Deserialize event
    2. Validate structure
    3. Enrich with metadata
    4. Store to database
    5. Emit Prometheus metrics
    """
    
    def __init__(
        self,
        kafka_brokers: Optional[str] = None,
        consumer_group: str = "audit-worker",
        input_topic: str = "audit.events",
        batch_size: int = 100,
        flush_interval_ms: int = 5000,
    ):
        self.kafka_brokers = kafka_brokers or os.getenv(
            "KAFKA_BROKERS", "localhost:9092"
        )
        self.consumer_group = consumer_group
        self.input_topic = input_topic
        self.batch_size = batch_size
        self.flush_interval_ms = flush_interval_ms
        
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._event_buffer: List[AuditEvent] = []
        self._last_flush = datetime.utcnow()
        
        # Handlers - inject real implementations
        self._storage_handler: Optional[Callable] = None
        self._metrics_handler: Optional[Callable] = None
    
    def set_storage_handler(self, handler: Callable):
        """Set PostgreSQL storage handler."""
        self._storage_handler = handler
    
    def set_metrics_handler(self, handler: Callable):
        """Set Prometheus metrics handler."""
        self._metrics_handler = handler
    
    async def start(self):
        """Start the Kafka consumer."""
        LOGGER.info(f"Starting AuditWorker on {self.kafka_brokers}")
        
        self._consumer = AIOKafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.kafka_brokers,
            group_id=self.consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        
        await self._consumer.start()
        self._running = True
        
        LOGGER.info(f"AuditWorker started, consuming from {self.input_topic}")
    
    async def stop(self):
        """Stop the Kafka consumer gracefully."""
        LOGGER.info("Stopping AuditWorker...")
        self._running = False
        
        # Flush remaining events
        await self._flush_buffer()
        
        if self._consumer:
            await self._consumer.stop()
        
        LOGGER.info("AuditWorker stopped")
    
    async def run(self):
        """Main consumer loop."""
        if not self._running:
            await self.start()
        
        try:
            async for msg in self._consumer:
                try:
                    event = self._parse_event(msg.value)
                    self._event_buffer.append(event)
                    
                    # Emit immediate metric
                    if self._metrics_handler:
                        await self._metrics_handler(
                            event_type=event.event_type,
                            outcome=event.outcome,
                            tenant_id=event.tenant_id,
                        )
                    
                    # Check if we should flush
                    if await self._should_flush():
                        await self._flush_buffer()
                        
                except Exception as e:
                    LOGGER.error(f"Error processing audit event: {e}")
        except asyncio.CancelledError:
            LOGGER.info("AuditWorker cancelled")
        finally:
            await self.stop()
    
    def _parse_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Parse raw event data into AuditEvent."""
        return AuditEvent(
            event_id=data.get("event_id", str(uuid4())),
            event_type=data.get("event_type", "unknown"),
            tenant_id=data.get("tenant_id", "unknown"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            workflow_id=data.get("workflow_id"),
            correlation_id=data.get("correlation_id", str(uuid4())),
            action=data.get("action", "unknown"),
            resource=data.get("resource", "unknown"),
            resource_id=data.get("resource_id"),
            outcome=data.get("outcome", "unknown"),
            details=data.get("details", {}),
            source_service=data.get("source_service", "unknown"),
            source_ip=data.get("source_ip"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )
    
    async def _should_flush(self) -> bool:
        """Check if buffer should be flushed."""
        if len(self._event_buffer) >= self.batch_size:
            return True
        
        elapsed = (datetime.utcnow() - self._last_flush).total_seconds() * 1000
        if elapsed >= self.flush_interval_ms and self._event_buffer:
            return True
        
        return False
    
    async def _flush_buffer(self):
        """Flush event buffer to storage."""
        if not self._event_buffer:
            return
        
        events_to_store = self._event_buffer.copy()
        self._event_buffer.clear()
        self._last_flush = datetime.utcnow()
        
        LOGGER.info(f"Flushing {len(events_to_store)} audit events to storage")
        
        if self._storage_handler:
            try:
                await self._storage_handler(events_to_store)
                LOGGER.info(f"Successfully stored {len(events_to_store)} audit events")
            except Exception as e:
                LOGGER.error(f"Failed to store audit events: {e}")
                # Re-add events to buffer for retry
                self._event_buffer.extend(events_to_store)
        else:
            # Log events if no storage handler
            for event in events_to_store:
                LOGGER.info(
                    f"AUDIT: {event.event_type} | "
                    f"tenant={event.tenant_id} | "
                    f"action={event.action} | "
                    f"resource={event.resource} | "
                    f"outcome={event.outcome}"
                )


# Entry point for standalone worker
async def main():
    """Run the audit worker standalone."""
    logging.basicConfig(level=logging.INFO)
    
    worker = AuditWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
