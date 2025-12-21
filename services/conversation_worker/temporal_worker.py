"""Temporal worker entrypoint for conversation processing."""

from __future__ import annotations

import asyncio

from temporalio import activity, workflow
from datetime import timedelta
from temporalio.client import Client
from temporalio.worker import Worker

from python.helpers.tokens import count_tokens
from python.integrations.somabrain_client import SomaBrainClient
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState
from services.common import outbox_flush
from services.common.compensation import compensate_event
from services.common.budget_manager import BudgetManager
from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.model_profiles import ModelProfileStore
from services.common.policy_client import PolicyClient
from services.common.publisher import DurablePublisher
from services.common.router_client import RouterClient
from services.common.session_repository import PostgresSessionStore
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
APP = cfg.settings()
setup_tracing("conversation-temporal-worker", endpoint=APP.external.otlp_endpoint)


def _somabrain_health() -> SomabrainHealthState:
    # Minimal health probe until degradation monitor is wired into Temporal context
    return SomabrainHealthState.NORMAL


def _build_use_case():
    kafka = KafkaSettings(
        bootstrap_servers=APP.kafka.bootstrap_servers,
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )
    bus = KafkaEventBus(kafka)
    publisher = DurablePublisher(bus=bus)
    dlq = DeadLetterQueue(cfg.env("CONVERSATION_INBOUND", "conversation.inbound"), bus=bus)
    store = PostgresSessionStore(dsn=APP.database.dsn)
    profiles = ModelProfileStore.from_settings(APP)
    tenants = TenantConfig(
        path=cfg.env("TENANT_CONFIG_PATH", APP.extra.get("tenant_config_path", "conf/tenants.yaml"))
    )
    budgets = BudgetManager(url=APP.redis.url, tenant_config=tenants)
    policy_client = PolicyClient(base_url=APP.external.opa_url, tenant_config=tenants)
    enforcer = ConversationPolicyEnforcer(policy_client)
    telemetry = TelemetryPublisher(publisher=publisher, store=TelemetryStore.from_settings(APP))
    soma = SomaBrainClient.get()
    router = RouterClient(base_url=cfg.env("ROUTER_URL") or APP.extra.get("router_url"))
    ctx_builder = ContextBuilder(
        somabrain=soma,
        metrics=None,
        token_counter=count_tokens,
        health_provider=_somabrain_health,
        use_optimal_budget=cfg.env("CONTEXT_BUILDER_OPTIMAL_BUDGET", "false").lower() == "true",
    )
    gateway_base = cfg.env("SA01_WORKER_GATEWAY_BASE")
    if not gateway_base:
        raise RuntimeError("SA01_WORKER_GATEWAY_BASE is required")
    gen = GenerateResponseUseCase(
        gateway_base=gateway_base,
        internal_token=cfg.env("SA01_GATEWAY_INTERNAL_TOKEN", ""),
        publisher=publisher,
        outbound_topic=cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound"),
        default_model=cfg.env("SA01_LLM_MODEL", "gpt-4o-mini"),
    )
    proc = ProcessMessageUseCase(
        session_repo=store,
        policy_enforcer=enforcer,
        memory_client=soma,
        publisher=publisher,
        context_builder=ctx_builder,
        response_generator=gen,
        outbound_topic=cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound"),
    )
    return proc, dlq, profiles, budgets, telemetry, router


@activity.defn
async def process_message_activity(event: dict) -> dict:
    proc, dlq, _, _, _, _ = _build_use_case()
    try:
        res = await proc.execute(
            ProcessMessageInput(
                event=event,
                session_id=event.get("session_id"),
                tenant=(event.get("metadata") or {}).get("tenant", "default"),
                persona_id=event.get("persona_id"),
                metadata=event.get("metadata", {}),
            )
        )
        return {"success": res.success, "error": res.error}
    except Exception as exc:
        try:
            await compensate_event(event)
        except Exception:
            pass
        await dlq.send_to_dlq(event, exc)
        return {"success": False, "error": str(exc)}


@workflow.defn
class ConversationWorkflow:
    @workflow.run
    async def run(self, event: dict) -> dict:
        return await workflow.execute_activity(
            process_message_activity,
            event,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


async def main() -> None:
    temporal_host = cfg.env("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = cfg.env("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
    await outbox_flush.flush()
    client = await Client.connect(temporal_host)
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=[process_message_activity],
        workflows=[ConversationWorkflow],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
