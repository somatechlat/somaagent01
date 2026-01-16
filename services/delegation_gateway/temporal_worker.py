"""Temporal worker for A2A / delegation tool processing."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from services.common.compensation import compensate_event
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.delegation_gateway.main import DelegationGateway


@activity.defn
async def handle_a2a(event: dict) -> dict:
    """Execute handle a2a.

    Args:
        event: The event.
    """

    kcfg = KafkaSettings(
        bootstrap_servers=os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS",
            os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        )
    )
    bus = KafkaEventBus(kcfg)
    publisher = DurablePublisher(bus=bus)
    dlq = DeadLetterQueue(os.environ.get("A2A_TOPIC", "a2a"), bus=bus)
    gateway = DelegationGateway()
    try:
        await gateway.handle_event(event, publisher)
        return {"success": True}
    except Exception as exc:
        try:
            await compensate_event(event)
        except Exception:
            pass
        await dlq.send_to_dlq(event, exc)
        return {"success": False, "error": str(exc)}


@workflow.defn
class A2AWorkflow:
    """Temporal workflow for A2A event processing."""

    @workflow.run
    async def run(self, event: dict) -> dict:
        """Execute workflow run.

        Args:
            event: The event to process.

        Returns:
            Result dictionary.
        """
        return await workflow.execute_activity(
            handle_a2a,
            event,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


async def main() -> None:
    """Execute main."""

    temporal_host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = os.environ.get("SA01_TEMPORAL_A2A_QUEUE", "a2a")
    # outbox_flush removed - feature never implemented
    client = await Client.connect(temporal_host)
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=[handle_a2a],
        workflows=[A2AWorkflow],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
