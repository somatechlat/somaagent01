"""Tool executor service for SomaAgent 01.

This is a thin entry point that wires up dependencies and starts the Kafka consumer.
All business logic is delegated to extracted modules.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from python.integrations.somabrain_client import SomaBrainClient
from services.common.audit_store import AuditStore as _AuditStore, from_env as audit_store_from_env
from services.common.event_bus import KafkaEventBus
from services.common.logging_config import setup_logging
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.requeue_store import RequeueStore
from services.common.session_repository import PostgresSessionStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing

# Extracted modules
from services.tool_executor.config import (
    get_stream_config,
    kafka_settings,
    policy_requeue_prefix,
    redis_url,
    SERVICE_SETTINGS,
    tenant_config_path,
)
from services.tool_executor.execution_engine import ExecutionEngine
from services.tool_executor.metrics import ensure_metrics_server
from services.tool_executor.request_handler import RequestHandler
from services.tool_executor.resource_manager import ResourceManager
from services.tool_executor.result_publisher import ResultPublisher
from services.tool_executor.sandbox_manager import SandboxManager
from services.tool_executor.telemetry import ToolTelemetryEmitter
from services.tool_executor.tool_registry import ToolRegistry
from services.tool_executor.multimodal_executor import MultimodalExecutor
import os

setup_logging()
LOGGER = logging.getLogger(__name__)

setup_tracing("tool-executor", endpoint=SERVICE_SETTINGS.external.otlp_endpoint)


class ToolExecutor:
    """Tool executor service - thin orchestrator."""

    def __init__(self) -> None:
        ensure_metrics_server(SERVICE_SETTINGS)
        self.kafka_settings = kafka_settings()
        self.bus = KafkaEventBus(self.kafka_settings)
        self.publisher = DurablePublisher(bus=self.bus)
        self.tenant_config = TenantConfig(path=tenant_config_path())
        self.policy = PolicyClient(
            base_url=os.environ.get("POLICY_BASE_URL", SERVICE_SETTINGS.external.opa_url),
            tenant_config=self.tenant_config,
        )
        self.store = PostgresSessionStore(dsn=os.environ.get("SA01_DB_DSN", ""))
        self.requeue = RequeueStore(url=redis_url(), prefix=policy_requeue_prefix())
        self.resources = ResourceManager()
        self.sandbox = SandboxManager()
        self.tool_registry = ToolRegistry()
        self.execution_engine = ExecutionEngine(self.sandbox, self.resources)
        self.telemetry = ToolTelemetryEmitter(publisher=self.publisher, settings=SERVICE_SETTINGS)
        self.soma = SomaBrainClient.get()
        self.streams = get_stream_config()
        self._audit_store: _AuditStore | None = None
        self._multimodal_task: asyncio.Task | None = None
        self._multimodal_executor: MultimodalExecutor | None = None

        # Initialize handlers
        self._request_handler = RequestHandler(self)
        self._result_publisher = ResultPublisher(self)

    def get_audit_store(self) -> _AuditStore:
        if self._audit_store is not None:
            return self._audit_store
        self._audit_store = audit_store_from_env()
        return self._audit_store

    async def publish_result(
        self,
        event: dict[str, Any],
        status: str,
        payload: dict[str, Any],
        *,
        execution_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Delegate result publishing to ResultPublisher."""
        await self._result_publisher.publish(
            event, status, payload, execution_time=execution_time, metadata=metadata
        )

    async def start(self) -> None:
        """Initialize resources and start consuming events."""
        await self.resources.initialize()
        await self.sandbox.initialize()
        await self.tool_registry.load_all_tools()

        # Ensure schemas (best-effort)

        try:
            await self.get_audit_store().ensure_schema()
        except Exception:
            LOGGER.debug("Audit store schema ensure failed (tool-executor)", exc_info=True)

        # Multimodal job executor (polling pending plans)
        if os.environ.get("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() == "true":
            try:
                self._multimodal_executor = MultimodalExecutor(dsn=os.environ.get("SA01_DB_DSN", ""))
                await self._multimodal_executor.initialize()
                poll_raw = os.environ.get("SA01_MULTIMODAL_POLL_INTERVAL", "2.0") or "2.0"
                try:
                    poll_interval = float(poll_raw)
                except ValueError:
                    poll_interval = 2.0
                self._multimodal_task = asyncio.create_task(
                    self._multimodal_executor.run_pending(poll_interval=poll_interval)
                )
                LOGGER.info("Multimodal executor started (poll_interval=%s)", poll_interval)
            except Exception:
                LOGGER.exception("Failed to start multimodal executor loop")

        # Start consuming
        await self.bus.consume(
            self.streams["requests"],
            self.streams["group"],
            self._request_handler.handle,
        )


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
