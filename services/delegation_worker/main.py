"""Delegation worker that consumes task queue events."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from jsonschema import ValidationError

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.delegation_store import DelegationStore
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.schema_validator import validate_event
from services.common.tracing import setup_tracing

# Legacy settings removed – use central config façade instead.
from src.core.config import cfg

setup_logging()
LOGGER = logging.getLogger(__name__)

# Use the central configuration object.
APP_SETTINGS = cfg.settings()
setup_tracing("delegation-worker", endpoint=APP_SETTINGS.external.otlp_endpoint)


class DelegationWorker:
    def __init__(self) -> None:
        self.topic = cfg.env("DELEGATION_TOPIC", "somastack.delegation")
        self.group = cfg.env("DELEGATION_GROUP", "delegation-worker")
        self.bus = KafkaEventBus(
            KafkaSettings(
                bootstrap_servers=ADMIN_SETTINGS.kafka_bootstrap_servers,
                security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
                sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
                sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
                sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
            )
        )
        self.store = DelegationStore(dsn=ADMIN_SETTINGS.postgres_dsn)

    async def start(self) -> None:
        await self.store.ensure_schema()
        await self.bus.consume(self.topic, self.group, self._handle_event)

    async def _handle_event(self, event: dict[str, Any]) -> None:
        try:
            validate_event(event, "delegation_task")
        except ValidationError as exc:
            LOGGER.error("Invalid delegation event", extra={"error": exc.message, "event": event})
            return

        task_id = event["task_id"]
        await self.store.create_task(
            task_id=task_id,
            payload=event.get("payload", {}),
            status="received",
            callback_url=event.get("callback_url"),
            metadata=event.get("metadata"),
        )
        LOGGER.info("Delegation task received", extra={"task_id": task_id})
        # Worker is intentionally passive – downstream processors should pick up the
        # task from Postgres or Kafka. Keeping this hook allows telemetry/testing.


async def main() -> None:
    worker = DelegationWorker()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Delegation worker stopped")
