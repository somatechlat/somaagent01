"""Tool executor service for SomaAgent 01."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any

from jsonschema import ValidationError
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.memory_write_outbox import MemoryWriteOutbox, ensure_schema as ensure_mw_outbox_schema
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.publisher import DurablePublisher
from services.common.idempotency import generate_for_memory_payload
from services.common.requeue_store import RequeueStore
from services.common.schema_validator import validate_event
from services.common.session_repository import PostgresSessionStore
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from services.tool_executor.execution_engine import ExecutionEngine
from services.tool_executor.resource_manager import default_limits, ResourceManager
from services.tool_executor.sandbox_manager import SandboxManager
from services.tool_executor.tool_registry import ToolRegistry
from services.tool_executor.tools import ToolExecutionError

setup_logging()
LOGGER = logging.getLogger(__name__)

SERVICE_SETTINGS = SA01Settings.from_env()
setup_tracing("tool-executor", endpoint=SERVICE_SETTINGS.otlp_endpoint)


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


def ensure_metrics_server(settings: SA01Settings) -> None:
    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return

    default_port = int(getattr(settings, "metrics_port", 9401))
    default_host = str(getattr(settings, "metrics_host", "0.0.0.0"))

    port = int(os.getenv("TOOL_EXECUTOR_METRICS_PORT", str(default_port)))
    if port <= 0:
        LOGGER.warning("Tool executor metrics disabled", extra={"port": port})
        _METRICS_SERVER_STARTED = True
        return

    host = os.getenv("TOOL_EXECUTOR_METRICS_HOST", default_host)
    start_http_server(port, addr=host)
    LOGGER.info("Tool executor metrics server started", extra={"host": host, "port": port})
    _METRICS_SERVER_STARTED = True


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", SERVICE_SETTINGS.kafka_bootstrap_servers
        ),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
    )


def _redis_url() -> str:
    return os.getenv("REDIS_URL", SERVICE_SETTINGS.redis_url)


def _tenant_config_path() -> str:
    return os.getenv(
        "TENANT_CONFIG_PATH",
        SERVICE_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"),
    )


def _policy_requeue_prefix() -> str:
    return os.getenv(
        "POLICY_REQUEUE_PREFIX",
        SERVICE_SETTINGS.extra.get("policy_requeue_prefix", "policy:requeue"),
    )


class ToolExecutor:
    def __init__(self) -> None:
        ensure_metrics_server(SERVICE_SETTINGS)
        self.kafka_settings = _kafka_settings()
        self.bus = KafkaEventBus(self.kafka_settings)
        self.outbox = OutboxStore(dsn=SERVICE_SETTINGS.postgres_dsn)
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        self.tenant_config = TenantConfig(path=_tenant_config_path())
        self.policy = PolicyClient(
            base_url=os.getenv("POLICY_BASE_URL", SERVICE_SETTINGS.opa_url),
            tenant_config=self.tenant_config,
        )
        self.store = PostgresSessionStore(dsn=SERVICE_SETTINGS.postgres_dsn)
        self.requeue = RequeueStore(url=_redis_url(), prefix=_policy_requeue_prefix())
        self.resources = ResourceManager()
        self.sandbox = SandboxManager()
        self.tool_registry = ToolRegistry()
        self.execution_engine = ExecutionEngine(self.sandbox, self.resources)
        telemetry_store = TelemetryStore.from_settings(SERVICE_SETTINGS)
        self.telemetry = TelemetryPublisher(publisher=self.publisher, store=telemetry_store)
        self.requeue_prefix = _policy_requeue_prefix()
        # Use SomaBrain HTTP client for memory persistence
        self.soma = SomaBrainClient.get()
        self.mem_outbox = MemoryWriteOutbox(dsn=SERVICE_SETTINGS.postgres_dsn)
        stream_defaults = SERVICE_SETTINGS.extra.get(
            "tool_executor_topics",
            {
                "requests": "tool.requests",
                "results": "tool.results",
                "group": "tool-executor",
            },
        )
        self.streams = {
            "requests": os.getenv(
                "TOOL_REQUESTS_TOPIC", stream_defaults.get("requests", "tool.requests")
            ),
            "results": os.getenv(
                "TOOL_RESULTS_TOPIC", stream_defaults.get("results", "tool.results")
            ),
            "group": os.getenv(
                "TOOL_EXECUTOR_GROUP", stream_defaults.get("group", "tool-executor")
            ),
        }

    async def start(self) -> None:
        await self.resources.initialize()
        await self.sandbox.initialize()
        await self.tool_registry.load_all_tools()
        try:
            await ensure_outbox_schema(self.outbox)
        except Exception:
            LOGGER.debug("Outbox schema ensure failed", exc_info=True)
        try:
            await ensure_mw_outbox_schema(self.mem_outbox)
        except Exception:
            LOGGER.debug("Memory write outbox schema ensure failed", exc_info=True)
        await self.bus.consume(
            self.streams["requests"],
            self.streams["group"],
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
            LOGGER.error("Tool execution failed", extra={"tool": tool_name, "error": str(exc)})
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
        except Exception as exc:
            LOGGER.error(
                "Error processing tool request",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "tool_name": event.get("tool_name", "unknown"),
                },
            )
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
        await self.publisher.publish(
            self.streams["results"],
            result_event,
            dedupe_key=result_event.get("event_id"),
            session_id=result_event.get("session_id"),
            tenant=(result_event.get("metadata") or {}).get("tenant"),
        )

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

        if status == "success":
            await self._capture_memory(result_event, payload, tenant)

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

    async def _capture_memory(
        self,
        result_event: dict[str, Any],
        payload: dict[str, Any],
        tenant: str,
    ) -> None:
        persona_id = result_event.get("persona_id")
        # Serialize tool payload to a stable string representation
        if isinstance(payload, str):
            content = payload
        else:
            try:
                content = json.dumps(payload, ensure_ascii=False)
            except Exception:
                content = str(payload)

        metadata = result_event.get("metadata") or {}
        str_metadata = {str(key): str(value) for key, value in metadata.items()}
        if result_event.get("tool_name"):
            str_metadata.setdefault("tool_name", str(result_event.get("tool_name")))
        if result_event.get("session_id"):
            str_metadata.setdefault("session_id", str(result_event.get("session_id")))
        if isinstance(payload, dict) and payload.get("model"):
            str_metadata.setdefault("tool_model", str(payload.get("model")))

        # Pre-write OPA memory.write; then persist tool result as a SomaBrain memory
        memory_payload = {
            "id": result_event.get("event_id"),
            "type": "tool_result",
            "tool_name": result_event.get("tool_name"),
            "content": content,
            "session_id": result_event.get("session_id"),
            "persona_id": persona_id,
            "metadata": {
                **str_metadata,
                "agent_profile_id": (result_event.get("metadata") or {}).get("agent_profile_id"),
                "universe_id": (result_event.get("metadata") or {}).get("universe_id") or os.getenv("SOMA_NAMESPACE"),
            },
            "status": result_event.get("status"),
        }
        memory_payload["idempotency_key"] = generate_for_memory_payload(memory_payload)
        try:
            # Fail-closed by default
            allow_memory = False
            try:
                allow_memory = await self.policy.evaluate(
                    PolicyRequest(
                        tenant=tenant,
                        persona_id=persona_id,
                        action="memory.write",
                        resource="somabrain",
                        context={
                            "payload_type": memory_payload.get("type"),
                            "tool_name": memory_payload.get("tool_name"),
                            "session_id": memory_payload.get("session_id"),
                            "metadata": memory_payload.get("metadata", {}),
                        },
                    )
                )
            except Exception:
                LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy", exc_info=True)
            if allow_memory:
                wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
                result = await self.soma.remember(memory_payload)
                try:
                    wal_event = {
                        "type": "memory.write",
                        "role": "tool",
                        "session_id": result_event.get("session_id"),
                        "persona_id": persona_id,
                        "tenant": tenant,
                        "payload": memory_payload,
                        "result": {
                            "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                            "trace_id": (result or {}).get("trace_id"),
                            "request_id": (result or {}).get("request_id"),
                        },
                        "timestamp": time.time(),
                    }
                    await self.publisher.publish(
                        wal_topic,
                        wal_event,
                        dedupe_key=str(memory_payload.get("id")),
                        session_id=str(result_event.get("session_id")),
                        tenant=tenant,
                    )
                except Exception:
                    LOGGER.debug("Failed to publish memory WAL (tool result)", exc_info=True)
            else:
                LOGGER.info(
                    "memory.write denied by policy",
                    extra={
                        "session_id": result_event.get("session_id"),
                        "tool": result_event.get("tool_name"),
                        "event_id": result_event.get("event_id"),
                    },
                )
        except SomaClientError as exc:
            LOGGER.warning(
                "SomaBrain remember failed for tool result",
                extra={
                    "session_id": result_event.get("session_id"),
                    "tool": result_event.get("tool_name"),
                    "error": str(exc),
                },
            )
            try:
                await self.mem_outbox.enqueue(
                    payload=memory_payload,
                    tenant=tenant,
                    session_id=result_event.get("session_id"),
                    persona_id=persona_id,
                    idempotency_key=memory_payload.get("idempotency_key"),
                    dedupe_key=str(memory_payload.get("id")) if memory_payload.get("id") else None,
                )
            except Exception:
                LOGGER.debug("Failed to enqueue memory write for retry (tool)", exc_info=True)
        except Exception:
            LOGGER.debug("SomaBrain remember (tool result) unexpected error", exc_info=True)


async def main() -> None:
    executor = ToolExecutor()
    try:
        await executor.start()
    finally:
        await executor.policy.close()
        await executor.soma.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Tool executor stopped")
