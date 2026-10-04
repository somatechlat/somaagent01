"""ConversationWorker - Thin Orchestrator (<150 lines).

Delegates all business logic to Use Cases following Clean Architecture.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict

# Django setup for logging and ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

from django.conf import settings as django_settings
from prometheus_client import start_http_server

from admin.core.application.use_cases.conversation.generate_response import GenerateResponseUseCase
from admin.core.application.use_cases.conversation.process_message import (
    ProcessMessageInput,
    ProcessMessageUseCase,
)
from services.common.budget_manager import BudgetManager
from services.common.memory_gateway import build_memory_gateway
from services.common.degradation_monitor import degradation_monitor
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import (
    KafkaEventBus,
    KafkaSettings,
    resolve_kafka_sasl_password,
)
from services.common.model_profiles import ModelProfileStore
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.router_client import RouterClient
from services.common.telemetry import TelemetryPublisher
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
    port = int(os.environ.get("CONVERSATION_METRICS_PORT", "9091"))
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
            sasl_password=resolve_kafka_sasl_password(),
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
        self.telemetry = TelemetryPublisher(publisher=self.publisher)
        self.router = RouterClient(base_url=os.environ.get("ROUTER_URL", ""))
        # Initialize use cases
        self._init_use_cases()

    def _init_use_cases(self) -> None:
        """Initialize use cases.

        All config from env, no hardcoded defaults per VIBE rules.
        """
        # No ``or "http://localhost:9000"`` here. That substitute made the
        # required check below unreachable while its own message claimed there
        # were no hardcoded defaults (VIBE Rule 91).
        gateway_base = os.environ.get("SA01_WORKER_GATEWAY_BASE")
        if not gateway_base:
            raise ValueError(
                "SA01_WORKER_GATEWAY_BASE is required. No hardcoded defaults per VIBE rules."
            )
        # VIBE Rule 164: the gateway internal token is a credential and comes
        # from Vault, never from the environment. No ``or ""``: an absent secret
        # is passed through as absent, and GenerateResponseUseCase refuses to
        # run on it. Turning it into an empty string would send an empty
        # X-Internal-Token — a dummy credential on a live request.
        from services.common.unified_secret_manager import get_secret_manager

        # REQUIRED — the model actually sent when a caller names none. No
        # ``or ""``: an empty model is not a model.
        default_model = os.environ.get("SA01_LLM_MODEL")

        self._gen = GenerateResponseUseCase(
            gateway_base=gateway_base,
            internal_token=get_secret_manager().get_credential("gateway_internal_token"),
            publisher=self.publisher,
            outbound_topic=self.topics["out"],
            default_model=default_model,
        )
        self._proc = ProcessMessageUseCase(
            session_repo=self.store,
            policy_enforcer=self.enforcer,
            gateway=build_memory_gateway(),
            publisher=self.publisher,
            response_generator=self._gen,
            outbound_topic=self.topics["out"],
        )

    async def start(self) -> None:
        """Execute start."""

        await degradation_monitor.initialize()
        await degradation_monitor.start_monitoring()
        # ensure_schema not needed - Django migrations handle this
        await self.profiles.ensure_schema()
        #         await self.store.append_event(
        #             "system", {"type": "worker_start", "event_id": str(uuid.uuid4()), "message": "online"}
        #         )
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
                "Received config update for tenant %s. Reloading worker configuration...", tenant
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
            LOGGER.warning("Failed: %s", result.error, extra={"session_id": sid})

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
        await w.router.close()
        await w.policy.close()
        await degradation_monitor.stop_monitoring()


ConversationWorker = ConversationWorkerImpl

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Stopped")
