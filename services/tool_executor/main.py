"""Tool executor service for SomaAgent 01."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from services.common.event_bus import KafkaEventBus
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.session_repository import PostgresSessionStore, RedisSessionCache
from services.tool_executor.tools import AVAILABLE_TOOLS, ToolExecutionError

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


class ToolExecutor:
    def __init__(self) -> None:
        self.bus = KafkaEventBus()
        self.policy = PolicyClient()
        self.store = PostgresSessionStore()
        self.cache = RedisSessionCache()
        self.settings = {
            "requests": os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"),
            "results": os.getenv("TOOL_RESULTS_TOPIC", "tool.results"),
            "group": os.getenv("TOOL_EXECUTOR_GROUP", "tool-executor"),
        }
        self.requeue_prefix = os.getenv("POLICY_REQUEUE_PREFIX", "policy:requeue")

    async def start(self) -> None:
        await self.bus.consume(
            self.settings["requests"],
            self.settings["group"],
            self._handle_request,
        )

    async def _handle_request(self, event: dict[str, Any]) -> None:
        session_id = event.get("session_id")
        tool_name = event.get("tool_name")
        tenant = event.get("metadata", {}).get("tenant", "default")
        persona_id = event.get("persona_id")

        if not session_id or not tool_name:
            LOGGER.error("Invalid tool request", extra={"event": event})
            return

        allow = await self._check_policy(
            tenant=tenant,
            persona_id=persona_id,
            tool_name=tool_name,
            event=event,
        )
        if not allow:
            await self._enqueue_requeue(event)
            await self._publish_result(
                event,
                status="blocked",
                payload={"message": "Policy denied tool execution."},
            )
            return

        tool = AVAILABLE_TOOLS.get(tool_name)
        if not tool:
            await self._publish_result(
                event,
                status="error",
                payload={"message": f"Unknown tool '{tool_name}'"},
            )
            return

        try:
            result_payload = await tool.run(event.get("args", {}))
            await self._publish_result(event, status="success", payload=result_payload)
        except ToolExecutionError as exc:
            LOGGER.error("Tool execution failed", extra={"tool": tool_name, "error": str(exc)})
            await self._publish_result(
                event,
                status="error",
                payload={"message": str(exc)},
            )

    async def _publish_result(self, event: dict[str, Any], status: str, payload: dict[str, Any]) -> None:
        result_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": event.get("session_id"),
            "persona_id": event.get("persona_id"),
            "tool_name": event.get("tool_name"),
            "status": status,
            "payload": payload,
            "metadata": event.get("metadata", {}),
        }
        await self.store.append_event(event.get("session_id", "unknown"), {"type": "tool", **result_event})
        await self.bus.publish(self.settings["results"], result_event)

    async def _check_policy(
        self,
        tenant: str,
        persona_id: str | None,
        tool_name: str,
        event: dict[str, Any],
    ) -> bool:
        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="tool.execute",
            resource=tool_name,
            context={"args": event.get("args", {}), "metadata": event.get("metadata", {})},
        )
        try:
            return await self.policy.evaluate(request)
        except Exception as exc:
            LOGGER.exception("Policy evaluation failed")
            raise RuntimeError("Policy evaluation failed") from exc

    async def _enqueue_requeue(self, event: dict[str, Any]) -> None:
        key = f"{self.requeue_prefix}:{event.get('event_id', uuid.uuid4())}"
        await self.cache.set(key, event)


async def main() -> None:
    executor = ToolExecutor()
    try:
        await executor.start()
    finally:
        await executor.policy.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Tool executor stopped")
