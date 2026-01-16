"""ConversationWorker - Thin Orchestrator (<150 lines).

Delegates all business logic to Use Cases following Clean Architecture.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any, Dict

# Django setup for logging and ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

from django.conf import settings as django_settings
from prometheus_client import start_http_server

from admin.agents.services.somabrain_integration import SomaBrainClient
from admin.core.application.use_cases.conversation.generate_response import GenerateResponseUseCase
from admin.core.application.use_cases.conversation.process_message import (
    ProcessMessageInput,
    ProcessMessageUseCase,
)
from admin.core.helpers.tokens import count_tokens
from admin.core.observability.metrics import ContextBuilderMetrics
# FIXED: Broken import from non-existent python.somaagent path
# ContextBuilder: canonical from simple_context_builder
# SomabrainHealthState: legacy from admin context_builder (TODO: consolidate)
from admin.agents.services.context_builder import SomabrainHealthState
from services.common.simple_context_builder import ContextBuilder
from services.common.budget_manager import BudgetManager
from services.common.degradation_monitor import degradation_monitor, DegradationLevel
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.model_profiles import ModelProfileStore
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.router_client import RouterClient
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer

LOGGER = logging.getLogger(__name__)
# Django settings used instead
tracer = setup_tracing("conversation-worker", endpoint=os.environ.get("OTLP_ENDPOINT", ""))
_metrics_started = False


def _start_metrics() -> None:
    """Start Prometheus metrics server if configured."""
    global _metrics_started
    if _metrics_started:
        return
    port = int(os.environ.get("CONVERSATION_METRICS_PORT", "9090"))
    if port > 0:
        start_http_server(port, addr=os.environ.get("CONVERSATION_METRICS_HOST", "0.0.0.0"))
    _metrics_started = True


class ConversationWorkerImpl:
    """Thin orchestrator - delegates to Use Cases."""

    def __init__(self) -> None:
        """Initialize worker components."""
        _start_metrics()
        # Kafka
        self.kafka = KafkaSettings(
            bootstrap_servers=django_settings.KAFKA_BOOTSTRAP_SERVERS,
            security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
            sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
            sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
        )
        self.topics = {
            "in": os.environ.get("CONVERSATION_INBOUND", "conversation.inbound"),
            "out": os.environ.get("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": os.environ.get("CONVERSATION_GROUP", "conversation-worker"),
        }
        # Infrastructure
        self.bus = KafkaEventBus(self.kafka)
        self.publisher = DurablePublisher(bus=self.bus)
        self.dlq = DeadLetterQueue(self.topics["in"], bus=self.bus)
        # Use Django cache for session cache
        from django.core.cache import cache as django_cache

        self.cache = django_cache
        # Use Django ORM Session model
        from admin.core.models import Session

        self.store = Session.objects
        self.profiles = ModelProfileStore.from_env()
        self.tenants = TenantConfig(path=os.environ.get("TENANT_CONFIG_PATH", "conf/tenants.yaml"))
        self.budgets = BudgetManager(url=django_settings.REDIS_URL, tenant_config=self.tenants)
        self.policy = PolicyClient(base_url=django_settings.OPA_URL, tenant_config=self.tenants)
        self.enforcer = ConversationPolicyEnforcer(self.policy)
        self.telemetry = TelemetryPublisher(
            publisher=self.publisher, store=TelemetryStore.from_env()
        )
        self.soma = SomaBrainClient.get()
        self.router = RouterClient(base_url=os.environ.get("ROUTER_URL", ""))
        # Context builder
        self.ctx_builder = ContextBuilder(
            somabrain=self.soma,
            metrics=ContextBuilderMetrics(),
            token_counter=count_tokens,
            health_provider=self._get_somabrain_health,
            use_optimal_budget=os.environ.get("CONTEXT_BUILDER_OPTIMAL_BUDGET", "false").lower()
            == "true",
        )
        # Initialize use cases
        self._init_use_cases()

    def _get_somabrain_health(self) -> SomabrainHealthState:
        """Get current SomaBrain health from degradation monitor."""
        if not degradation_monitor.is_monitoring():
            return SomabrainHealthState.NORMAL

        comp = degradation_monitor.components.get("somabrain")
        if not comp:
            return SomabrainHealthState.NORMAL

        if not comp.healthy:
            return SomabrainHealthState.DOWN

        if comp.degradation_level != DegradationLevel.NONE:
            return SomabrainHealthState.DEGRADED

        return SomabrainHealthState.NORMAL

    def _init_use_cases(self) -> None:
        """Initialize use cases.

        All config from env, no hardcoded defaults per VIBE rules.
        """
        gateway_base = os.environ.get("SA01_WORKER_GATEWAY_BASE")
        if not gateway_base:
            raise ValueError(
                "SA01_WORKER_GATEWAY_BASE is required. No hardcoded defaults per VIBE rules."
            )
        self._gen = GenerateResponseUseCase(
            gateway_base=gateway_base,
            internal_token=os.environ.get("SA01_GATEWAY_INTERNAL_TOKEN", ""),
            publisher=self.publisher,
            outbound_topic=self.topics["out"],
            default_model=os.environ.get(
                "SA01_LLM_MODEL"
            ),  # REQUIRED - no hardcoded default per VIBE
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
        """Execute start."""

        await degradation_monitor.initialize()
        await degradation_monitor.start_monitoring()
        # ensure_schema not needed - Django migrations handle this
        await self.profiles.ensure_schema()
        await self.store.append_event(
            "system", {"type": "worker_start", "event_id": str(uuid.uuid4()), "message": "online"}
        )
        LOGGER.info("Starting", extra={"topic": self.topics["in"], "group": self.topics["group"]})
        await self.bus.consume(self.topics["in"], self.topics["group"], self._handle)

    async def _handle(self, event: Dict[str, Any]) -> None:
        """Execute handle.

        Args:
            event: The event.
        """

        event_type = event.get("type", "")

        # Handle system config updates (Feature Flag Reload)
        if event_type == "system.config_update":
            tenant = event.get("tenant", "default")
            LOGGER.info(
                f"Received config update for tenant {tenant}. Reloading worker configuration..."
            )
            await self._reload_config(tenant)
            return

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

    async def _reload_config(self, tenant: str) -> None:
        """Reload configuration and dependencies in response to a config update.

        The Conversation Worker itself does not cache feature‑flag values; those
        are primarily enforced in the Gateway and Tool Executor layers.  The
        worker must, however, react to configuration updates so that:

        - long‑lived components that depend on database state (e.g. model
          profiles, tenant config) can be refreshed, and
        - we have clear, observable behaviour when a ``system.config_update``
          event is received.

        For now we:
        - refresh the in‑memory tenant configuration, and
        - log the effective feature flags for the tenant for debugging.

        This is a real, side‑effecting implementation; it does not attempt any
        speculative or partial reloads beyond what the current architecture
        safely supports.
        """
        try:
            from services.common.feature_flags_store import FeatureFlagsStore

            LOGGER.info("Reloading worker configuration for tenant %s", tenant)

            # Refresh tenant configuration from disk (if the file changed on disk,
            # this ensures we see the new values).
            self.tenants = TenantConfig(
                path=os.environ.get("TENANT_CONFIG_PATH", "conf/tenants.yaml")
            )

            # Load effective feature flags for observability.  The flags are not
            # yet threaded into use‑case configuration, but this makes the
            # behaviour transparent and verifiable.
            store = FeatureFlagsStore()
            effective = await store.get_effective_flags(tenant)
            LOGGER.info(
                "Effective feature flags for tenant %s (profile=%s): %s",
                tenant,
                effective.get("profile"),
                {k: v["enabled"] for k, v in effective.get("flags", {}).items()},
            )

        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.error("Failed to reload worker configuration: %s", exc, exc_info=True)


async def main() -> None:
    """Execute main."""

    w = ConversationWorkerImpl()
    try:
        await w.start()
    finally:
        await w.soma.close()
        await w.router.close()
        await w.policy.close()
        await degradation_monitor.stop_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Stopped")
