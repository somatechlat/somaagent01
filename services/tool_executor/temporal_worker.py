"""Temporal worker entrypoint for tool executor workflows."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from services.common.compensation import compensate_event
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus
from services.common.publisher import DurablePublisher
from services.tool_executor.config import kafka_settings
from services.tool_executor.main import ToolExecutor


@activity.defn
async def handle_tool_request(event: dict) -> dict:
    """Execute handle tool request.

    Args:
        event: The event.
    """

    kcfg = kafka_settings()
    bus = KafkaEventBus(kcfg)
    publisher = DurablePublisher(bus=bus)
    dlq = DeadLetterQueue(os.environ.get("TOOL_REQUESTS_TOPIC", "tool.requests"), bus=bus)
    executor = ToolExecutor(bus=bus, publisher=publisher)

    try:
        await executor.handle_event(event)
        return {"success": True}
    except Exception as exc:
        try:
            await compensate_event(event)
        except Exception:
            pass
        await dlq.send_to_dlq(event, exc)
        return {"success": False, "error": str(exc)}


@workflow.defn
class ToolExecutorWorkflow:
    """ToolExecutorWorkflow for processing tool requests via Temporal."""

    @workflow.run
    async def run(self, event: dict) -> dict:
        """Execute run.

        Args:
            event: The event.
        """

        return await workflow.execute_activity(
            handle_tool_request,
            event,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


async def main() -> None:
    """Execute main."""

    temporal_host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = os.environ.get("SA01_TEMPORAL_TOOL_QUEUE", "tool-executor")
    # outbox_flush removed - feature never implemented
    client = await Client.connect(temporal_host)
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=[handle_tool_request],
        workflows=[ToolExecutorWorkflow],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
