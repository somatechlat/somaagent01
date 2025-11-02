"""Test helpers for generating SomaAgent events."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, Callable, Dict, Optional

from aiokafka import AIOKafkaConsumer


def create_test_event(
    session_id: str | None = None,
    message: str = "Test message",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Fabricate a conversation event payload."""

    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id or str(uuid.uuid4()),
        "persona_id": kwargs.get("persona_id"),
        "message": message,
        "attachments": kwargs.get("attachments", []),
        "metadata": kwargs.get("metadata", {}),
        "role": kwargs.get("role", "user"),
    }


def create_test_tool_request(
    tool_name: str,
    args: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Craft a tool execution request envelope."""

    return {
        "event_id": str(uuid.uuid4()),
        "session_id": kwargs.get("session_id", str(uuid.uuid4())),
        "persona_id": kwargs.get("persona_id"),
        "tool_name": tool_name,
        "args": args or {},
        "metadata": kwargs.get("metadata", {}),
    }


async def wait_for_event(
    topic: str,
    *,
    timeout: float = 5.0,
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> Dict[str, Any]:
    """Consume Kafka events until one matches ``predicate`` or timeout expires."""

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    group_id = f"test-consumer-{uuid.uuid4()}"
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    loop = asyncio.get_running_loop()
    start = loop.time()
    try:
        while True:
            remaining = timeout - (loop.time() - start)
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for event on {topic}")
            result = await consumer.getmany(timeout_ms=int(remaining * 1000))
            for records in result.values():
                for record in records:
                    payload = json.loads(record.value.decode("utf-8"))
                    if predicate is None or predicate(payload):
                        return payload
    finally:
        await consumer.stop()
