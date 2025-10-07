"""Tool executor service for SomaAgent 01."""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any

from jsonschema import ValidationError

from services.common.event_bus import KafkaEventBus
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.session_repository import PostgresSessionStore
from services.common.requeue_store import RequeueStore
from services.common.schema_validator import validate_event
from services.common.telemetry import TelemetryPublisher
from services.tool_executor.execution_engine import ExecutionEngine
from services.tool_executor.resource_manager import ResourceManager, default_limits
from services.tool_executor.sandbox_manager import SandboxManager
from services.tool_executor.tool_registry import ToolRegistry
from services.tool_executor.tools import ToolExecutionError
from services.common.tenant_config import TenantConfig
from prometheus_client import Counter, Gauge, Histogram, start_http_server

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


TOOL_REQUEST_COUNTER = Counter(
    "tool_executor_requests_total",
    "Total tool execution requests processed",
    labelnames=("tool", "outcome"),
)
POLICY_DECISIONS = Counter(
    "tool_executor_policy_decisions_total",
    "Policy evaluation outcomes for tool executions",
    labelnames=("tool", "decision"),
)
TOOL_EXECUTION_LATENCY = Histogram(
    "tool_executor_execution_seconds",
    "Execution latency by tool",
    labelnames=("tool",),
)
TOOL_INFLIGHT = Gauge(
    "tool_executor_inflight",
    "Current number of in-flight tool executions",
    labelnames=("tool",),
)
REQUEUE_EVENTS = Counter(
    "tool_executor_requeue_total",
    "Requeue events emitted by the tool executor",
    labelnames=("tool", "reason"),
)

_METRICS_SERVER_STARTED = False


def ensure_metrics_server() -> None:
    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return

    port = int(os.getenv("TOOL_EXECUTOR_METRICS_PORT", "9401"))
    if port <= 0:
        LOGGER.warning("Tool executor metrics disabled", extra={"port": port})
        _METRICS_SERVER_STARTED = True
        return

    host = os.getenv("TOOL_EXECUTOR_METRICS_HOST", "0.0.0.0")
    start_http_server(port, addr=host)
    LOGGER.info(
        "Tool executor metrics server started", extra={"host": host, "port": port}
    )
    _METRICS_SERVER_STARTED = True


class ToolExecutor:
    def __init__(self) -> None:
        ensure_metrics_server()
        self.bus = KafkaEventBus()
        self.tenant_config = TenantConfig()
        self.policy = PolicyClient(tenant_config=self.tenant_config)
        self.store = PostgresSessionStore()
        self.requeue = RequeueStore()
        self.resources = ResourceManager()
        self.sandbox = SandboxManager()
        self.tool_registry = ToolRegistry()
        self.execution_engine = ExecutionEngine(self.sandbox, self.resources)
        self.telemetry = TelemetryPublisher(self.bus)
        self.requeue_prefix = os.getenv("POLICY_REQUEUE_PREFIX", "policy:requeue")
        self.settings = {
            "requests": os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"),
            "results": os.getenv("TOOL_RESULTS_TOPIC", "tool.results"),
            "group": os.getenv("TOOL_EXECUTOR_GROUP", "tool-executor"),
        }

    async def start(self) -> None:
        await self.resources.initialize()
        await self.sandbox.initialize()
        await self.tool_registry.load_all_tools()
        await self.bus.consume(
            self.settings["requests"],
            self.settings["group"],
            self._handle_request,
        )

    async def _handle_request(self, event: dict[str, Any]) -> None:
        session_id = event.get("session_id")
        tool_name = event.get("tool_name")
        tool_label = tool_name or "unknown"
        tenant = event.get("metadata", {}).get("tenant", "default")
        persona_id = event.get("persona_id")

        if not session_id or not tool_name:
            LOGGER.error("Invalid tool request", extra={"event": event})
            TOOL_REQUEST_COUNTER.labels(tool_label, "invalid").inc()
            return

        metadata = dict(event.get("metadata", {}))
        args = dict(event.get("args", {}))
        args.setdefault("session_id", session_id)

        if not metadata.get("requeue_override"):
            try:
                allow = await self._check_policy(
                    tenant=tenant,
                    persona_id=persona_id,
                    tool_name=tool_name,
                    event=event,
                )
            except RuntimeError:
                POLICY_DECISIONS.labels(tool_label, "error").inc()
                TOOL_REQUEST_COUNTER.labels(tool_label, "policy_error").inc()
                await self._publish_result(
                    event,
                    status="error",
                    payload={"message": "Policy evaluation failed."},
                    execution_time=0.0,
                    metadata=metadata,
                )
                return
            decision_label = "allowed" if allow else "denied"
            POLICY_DECISIONS.labels(tool_label, decision_label).inc()
            if not allow:
                await self._enqueue_requeue(event)
                REQUEUE_EVENTS.labels(tool_label, "policy_denied").inc()
                await self._publish_result(
                    event,
                    status="blocked",
                    payload={"message": "Policy denied tool execution."},
                    execution_time=0.0,
                    metadata=metadata,
                )
                return

        tool = self.tool_registry.get(tool_name)
        if not tool:
            await self._publish_result(
                event,
                status="error",
                payload={"message": f"Unknown tool '{tool_name}'"},
                execution_time=0.0,
                metadata=metadata,
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "unknown_tool").inc()
            return

        try:
            TOOL_INFLIGHT.labels(tool_label).inc()
            result = await self.execution_engine.execute(tool, args, default_limits())
        except ToolExecutionError as exc:
            LOGGER.error(
                "Tool execution failed", extra={"tool": tool_name, "error": str(exc)}
            )
            await self._publish_result(
                event,
                status="error",
                payload={"message": str(exc)},
                execution_time=0.0,
                metadata=metadata,
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "execution_error").inc()
            TOOL_INFLIGHT.labels(tool_label).dec()
            return
        except Exception as exc:  # pragma: no cover - defensive catch
            LOGGER.exception("Unexpected tool execution failure")
            await self._publish_result(
                event,
                status="error",
                payload={"message": "Unhandled tool executor error."},
                execution_time=0.0,
                metadata={**metadata, "error": str(exc)},
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "unexpected_error").inc()
            TOOL_INFLIGHT.labels(tool_label).dec()
            return
        else:
            TOOL_INFLIGHT.labels(tool_label).dec()
            TOOL_EXECUTION_LATENCY.labels(tool_label).observe(result.execution_time)
            TOOL_REQUEST_COUNTER.labels(tool_label, result.status).inc()

        result_metadata = dict(metadata)
        if getattr(result, "logs", None):
            result_metadata.setdefault("sandbox_logs", result.logs)

        await self._publish_result(
            event,
            status=result.status,
            payload=result.payload,
            execution_time=result.execution_time,
            metadata=result_metadata,
        )

    async def _publish_result(
        self,
        event: dict[str, Any],
        status: str,
        payload: dict[str, Any],
        *,
        execution_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        result_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": event.get("session_id"),
            "persona_id": event.get("persona_id"),
            "tool_name": event.get("tool_name"),
            "status": status,
            "payload": payload,
            "metadata": metadata if metadata is not None else event.get("metadata", {}),
            "execution_time": execution_time,
        }

        try:
            validate_event(result_event, "tool_result")
        except ValidationError as exc:
            LOGGER.error(
                "Invalid tool result payload",
                extra={"tool": event.get("tool_name"), "error": exc.message},
            )
            return

        await self.store.append_event(
            event.get("session_id", "unknown"), {"type": "tool", **result_event}
        )
        await self.bus.publish(self.settings["results"], result_event)

        tenant_meta = result_event.get("metadata", {})
        tenant = tenant_meta.get("tenant", "default")
        await self.telemetry.emit_tool(
            session_id=result_event["session_id"],
            persona_id=result_event.get("persona_id"),
            tenant=tenant,
            tool_name=result_event.get("tool_name", ""),
            status=status,
            latency_seconds=execution_time,
            metadata=tenant_meta,
        )

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
            context={
                "args": event.get("args", {}),
                "metadata": event.get("metadata", {}),
            },
        )
        try:
            return await self.policy.evaluate(request)
        except Exception as exc:
            LOGGER.exception("Policy evaluation failed")
            raise RuntimeError("Policy evaluation failed") from exc

    async def _enqueue_requeue(self, event: dict[str, Any]) -> None:
        identifier = event.get("event_id") or str(uuid.uuid4())
        payload = dict(event)
        payload["timestamp"] = time.time()
        await self.requeue.add(identifier, payload)


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
