"""Delegation worker that consumes task queue events."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from jsonschema import ValidationError

# Django setup for logging and ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django
django.setup()

from services.common.delegation_store import DelegationStore
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.schema_validator import validate_event
from services.common.tracing import setup_tracing

LOGGER = logging.getLogger(__name__)

# Retrieve settings from the central configuration.
# Django settings used instead
# The OTLP endpoint is now located under the external configuration section.
setup_tracing("delegation-worker", endpoint=APP_SETTINGS.external.otlp_endpoint)


class DelegationWorker:
    def __init__(self) -> None:
        self.topic = os.environ.get("DELEGATION_TOPIC", "somastack.delegation")
        self.group = os.environ.get("DELEGATION_GROUP", "delegation-worker")
        self.bus = KafkaEventBus(
            KafkaSettings(
                bootstrap_servers=os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
                sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
                sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
                sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
            )
        )
        self.store = DelegationStore(dsn=os.environ.get("SA01_DB_DSN", ""))

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
