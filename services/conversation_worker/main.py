"""ConversationWorker - Thin Orchestrator (<150 lines).

Delegates all business logic to Use Cases following Clean Architecture.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict

from prometheus_client import start_http_server

from observability.metrics import ContextBuilderMetrics
from python.helpers.tokens import count_tokens
from python.integrations.somabrain_client import SomaBrainClient
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState
from services.common.budget_manager import BudgetManager
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.memory_write_outbox import ensure_schema as ensure_mw_schema, MemoryWriteOutbox
from services.common.model_profiles import ModelProfileStore
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.router_client import RouterClient
from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
    RedisSessionCache,
)
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer
from src.core.application.use_cases.conversation import (
    GenerateResponseUseCase,
    ProcessMessageInput,
    ProcessMessageUseCase,
)
from src.core.config import cfg

setup_logging()
LOGGER = logging.getLogger(__name__)
APP = cfg.settings()
tracer = setup_tracing("conversation-worker", endpoint=APP.external.otlp_endpoint)
_metrics_started = False


def _start_metrics() -> None:
    global _metrics_started
    if _metrics_started:
        return
    port = int(cfg.env("CONVERSATION_METRICS_PORT", str(APP.metrics_port)))
    if port > 0:
        start_http_server(port, addr=cfg.env("CONVERSATION_METRICS_HOST", APP.metrics_host))
    _metrics_started = True


class ConversationWorkerImpl:
    """Thin orchestrator - delegates to Use Cases."""

    def __init__(self) -> None:
        _start_metrics()
        # Kafka
        self.kafka = KafkaSettings(
            bootstrap_servers=APP.kafka.bootstrap_servers,
            security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
            sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
            sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
        )
        self.topics = {
            "in": cfg.env("CONVERSATION_INBOUND", "conversation.inbound"),
            "out": cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": cfg.env("CONVERSATION_GROUP", "conversation-worker"),
        }
        # Infrastructure
        self.bus = KafkaEventBus(self.kafka)
        self.outbox = OutboxStore(dsn=APP.database.dsn)
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        self.dlq = DeadLetterQueue(self.topics["in"], bus=self.bus)
        self.cache = RedisSessionCache(url=APP.redis.url)
        self.store = PostgresSessionStore(dsn=APP.database.dsn)
        self.profiles = ModelProfileStore.from_settings(APP)
        self.tenants = TenantConfig(
            path=cfg.env(
                "TENANT_CONFIG_PATH", APP.extra.get("tenant_config_path", "conf/tenants.yaml")
            )
        )
        self.budgets = BudgetManager(url=APP.redis.url, tenant_config=self.tenants)
        self.policy = PolicyClient(base_url=APP.external.opa_url, tenant_config=self.tenants)
        self.enforcer = ConversationPolicyEnforcer(self.policy)
        self.telemetry = TelemetryPublisher(
            publisher=self.publisher, store=TelemetryStore.from_settings(APP)
        )
        self.soma = SomaBrainClient.get()
        self.mem_outbox = MemoryWriteOutbox(dsn=APP.database.dsn)
        self.router = RouterClient(base_url=cfg.env("ROUTER_URL") or APP.extra.get("router_url"))
        # Context builder
        self.ctx_builder = ContextBuilder(
            somabrain=self.soma,
            metrics=ContextBuilderMetrics(),
            token_counter=count_tokens,
            health_provider=lambda: SomabrainHealthState.NORMAL,
            on_degraded=lambda d: None,
        )
        # Use Cases
        self._gen = GenerateResponseUseCase(
            gateway_base=cfg.env("WORKER_GATEWAY_BASE", "http://gateway:8010"),
            internal_token=cfg.env("GATEWAY_INTERNAL_TOKEN", ""),
            publisher=self.publisher,
            outbound_topic=self.topics["out"],
            default_model=cfg.env("SLM_MODEL", "unknown"),
        )
        self._proc = ProcessMessageUseCase(
            session_repo=self.store,
            policy_enforcer=self.enforcer,
            memory_client=self.soma,
            publisher=self.publisher,
            context_builder=self.ctx_builder,
            response_generator=self._gen,
            outbound_topic=self.topics["out"],
        )

    async def start(self) -> None:
        await ensure_schema(self.store)
        try:
            await ensure_outbox_schema(self.outbox)
        except Exception:
            pass
        try:
            await ensure_mw_schema(self.mem_outbox)
        except Exception:
            pass
        await self.profiles.ensure_schema()
        await self.store.append_event(
            "system", {"type": "worker_start", "event_id": str(uuid.uuid4()), "message": "online"}
        )
        LOGGER.info("Starting", extra={"topic": self.topics["in"], "group": self.topics["group"]})
        await self.bus.consume(self.topics["in"], self.topics["group"], self._handle)

    async def _handle(self, event: Dict[str, Any]) -> None:
        sid = event.get("session_id")
        if not sid:
            return
        tenant = (event.get("metadata") or {}).get("tenant", "default")
        result = await self._proc.execute(
            ProcessMessageInput(
                event=event,
                session_id=sid,
                tenant=tenant,
                persona_id=event.get("persona_id"),
                metadata=event.get("metadata", {}),
            )
        )
        if not result.success:
            LOGGER.warning(f"Failed: {result.error}", extra={"session_id": sid})


async def main() -> None:
    w = ConversationWorkerImpl()
    try:
        await w.start()
    finally:
        await w.soma.close()
        await w.router.close()
        await w.policy.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Stopped")
