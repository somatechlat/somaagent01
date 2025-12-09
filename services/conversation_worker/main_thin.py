"""ConversationWorker - Thin orchestrator.

This module provides the ConversationWorker class as a thin orchestrator
that delegates to extracted handler modules.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any, Dict

from prometheus_client import start_http_server

from python.integrations.somabrain_client import SomaBrainClient
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState
from services.common.budget_manager import BudgetManager
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.memory_write_outbox import ensure_schema as ensure_mw_outbox_schema, MemoryWriteOutbox
from services.common.model_profiles import ModelProfileStore
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.router_client import RouterClient
from services.common.session_repository import ensure_schema, PostgresSessionStore, RedisSessionCache
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer
from services.tool_executor.tool_registry import ToolRegistry
from src.core.config import cfg

# Import extracted handlers
from .event_handler import EventHandler
from .health_monitor import HealthMonitor, SOMABRAIN_STATUS_GAUGE, SOMABRAIN_BUFFER_GAUGE
from .llm_metrics import normalize_usage, record_llm_success, record_llm_failure
from .memory_handler import MemoryHandler
from .response_handler import ResponseHandler
from .tool_orchestrator import ToolOrchestrator

# Re-export service wrapper
from .service import ConversationWorkerService as ConversationWorker

setup_logging()
LOGGER = logging.getLogger(__name__)
APP_SETTINGS = cfg.settings()
tracer = setup_tracing("conversation-worker", endpoint=APP_SETTINGS.external.otlp_endpoint)

_metrics_started = False


def ensure_metrics_server() -> None:
    """Start Prometheus metrics server if not already running."""
    global _metrics_started
    if _metrics_started:
        return
    port = int(cfg.env("METRICS_PORT", "9102"))
    try:
        start_http_server(port)
        _metrics_started = True
        LOGGER.info(f"Metrics server started on port {port}")
    except Exception as e:
        LOGGER.warning(f"Could not start metrics server: {e}")


class ConversationWorkerImpl:
    """Conversation worker implementation - thin orchestrator."""
    
    def __init__(self) -> None:
        ensure_metrics_server()
        
        # Kafka setup
        self.kafka_settings = KafkaSettings(
            bootstrap_servers=cfg.settings().kafka.bootstrap_servers,
            security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
            sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
            sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
        )
        self.settings = {
            "inbound": cfg.env("CONVERSATION_INBOUND", "conversation.inbound"),
            "outbound": cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": cfg.env("CONVERSATION_GROUP", "conversation-worker"),
        }
        
        # Core infrastructure
        self.bus = KafkaEventBus(self.kafka_settings)
        self.outbox = OutboxStore(dsn=cfg.settings().database.dsn)
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        self.dlq = DeadLetterQueue(self.settings["inbound"], bus=self.bus)
        self.cache = RedisSessionCache(url=cfg.settings().redis.url)
        self.store = PostgresSessionStore(dsn=cfg.settings().database.dsn)
        
        # Model and tenant config
        self.profile_store = ModelProfileStore.from_settings(APP_SETTINGS)
        tenant_config_path = cfg.env("TENANT_CONFIG_PATH", APP_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"))
        self.tenant_config = TenantConfig(path=tenant_config_path)
        self.budgets = BudgetManager(url=cfg.settings().redis.url, tenant_config=self.tenant_config)
        
        # Policy
        self.policy_client = PolicyClient(base_url=cfg.settings().external.opa_url, tenant_config=self.tenant_config)
        self.policy_enforcer = ConversationPolicyEnforcer(self.policy_client)
        
        # Telemetry
        telemetry_store = TelemetryStore.from_settings(APP_SETTINGS)
        self.telemetry = TelemetryPublisher(publisher=self.publisher, store=telemetry_store)
        
        # SomaBrain
        self.soma = SomaBrainClient.get()
        self._soma_brain_up = True
        self._somabrain_degraded_until = 0.0
        
        # Context builder
        from observability.metrics import ContextBuilderMetrics
        self.context_metrics = ContextBuilderMetrics()
        from python.helpers.tokens import count_tokens
        self.context_builder = ContextBuilder(
            somabrain=self.soma,
            metrics=self.context_metrics,
            token_counter=count_tokens,
            health_provider=self._somabrain_health_state,
            on_degraded=self._mark_somabrain_degraded,
        )
        
        # Memory outbox and router
        self.mem_outbox = MemoryWriteOutbox(dsn=cfg.settings().database.dsn)
        router_url = cfg.env("ROUTER_URL") or APP_SETTINGS.extra.get("router_url")
        self.router = RouterClient(base_url=router_url)
        
        # Tool registry
        self.tool_registry = ToolRegistry()
        
        # Initialize handlers
        self.event_handler = EventHandler(self)
        self.memory_handler = MemoryHandler(self)
        self.response_handler = ResponseHandler(self)
        self.health_monitor = HealthMonitor()
        
        # Health monitoring task
        if "pytest" not in __import__("sys").modules and not cfg.env("PYTEST_CURRENT_TEST"):
            self._health_task = asyncio.create_task(self._monitor_health())
        else:
            self._health_task = None
    
    def _somabrain_health_state(self) -> SomabrainHealthState:
        """Get current SomaBrain health state."""
        return SomabrainHealthState(healthy=self._soma_brain_up, degraded_until=self._somabrain_degraded_until)
    
    def _mark_somabrain_degraded(self, duration: float) -> None:
        """Mark SomaBrain as degraded."""
        import time
        self._somabrain_degraded_until = time.time() + duration
    
    def _enter_somabrain_degraded(self, reason: str, duration: float = 60.0) -> None:
        """Enter degraded mode for SomaBrain."""
        if not self._soma_brain_up:
            self._mark_somabrain_degraded(duration)
            return
        LOGGER.warning(f"SomaBrain degraded: {reason}")
        self._soma_brain_up = False
        SOMABRAIN_STATUS_GAUGE.set(0.0)
        self._mark_somabrain_degraded(duration)
    
    async def _monitor_health(self) -> None:
        """Monitor SomaBrain health periodically."""
        while True:
            try:
                if hasattr(self.soma, "health"):
                    await self.soma.health()
                up = True
            except Exception:
                up = False
            
            previous = self._soma_brain_up
            self._soma_brain_up = up
            SOMABRAIN_STATUS_GAUGE.set(1.0 if up else 0.0)
            
            if up and not previous:
                LOGGER.info("SomaBrain recovered")
            
            await asyncio.sleep(5)
    
    async def start(self) -> None:
        """Start the conversation worker."""
        await ensure_schema(self.store)
        try:
            await ensure_outbox_schema(self.outbox)
        except Exception:
            LOGGER.debug("Outbox schema ensure failed", exc_info=True)
        try:
            await ensure_mw_outbox_schema(self.mem_outbox)
        except Exception:
            LOGGER.debug("Memory write outbox schema ensure failed", exc_info=True)
        await self.profile_store.ensure_schema()
        
        await self.store.append_event("system", {
            "type": "worker_start",
            "event_id": str(uuid.uuid4()),
            "message": "Conversation worker online",
        })
        
        LOGGER.info("Starting consumer", extra={
            "topic": self.settings["inbound"],
            "group": self.settings["group"],
        })
        
        await self.bus.consume(
            self.settings["inbound"],
            self.settings["group"],
            self._handle_event,
        )
    
    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle incoming event - delegates to EventHandler."""
        await self.event_handler.handle_event(event)


async def main() -> None:
    """Entry point for conversation worker."""
    worker = ConversationWorkerImpl()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
