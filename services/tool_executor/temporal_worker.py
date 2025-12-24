"""Temporal worker entrypoint for tool executor workflows."""

from __future__ import annotations

import asyncio

from temporalio import activity, workflow
from datetime import timedelta
from temporalio.client import Client
from temporalio.worker import Worker

from services.common import outbox_flush
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.common.dlq import DeadLetterQueue
from services.common.compensation import compensate_event
from services.tool_executor.main import ToolExecutor
from services.tool_executor.config import kafka_settings
import os


@activity.defn
async def handle_tool_request(event: dict) -> dict:
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
    @workflow.run
    async def run(self, event: dict) -> dict:
        return await workflow.execute_activity(
            handle_tool_request,
            event,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


async def main() -> None:
    temporal_host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = os.environ.get("SA01_TEMPORAL_TOOL_QUEUE", "tool-executor")
    await outbox_flush.flush()
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
