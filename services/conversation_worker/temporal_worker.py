"""Temporal worker entrypoint for conversation processing."""

from __future__ import annotations

import asyncio
import logging
import os

# Django setup for logging and ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

from datetime import timedelta

from django.conf import settings as django_settings
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from admin.agents.services.somabrain_integration import SomaBrainClient
from admin.core.helpers.tokens import count_tokens
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState
from services.common.budget_manager import BudgetManager
from services.common.compensation import compensate_event
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
from services.conversation_worker.service import (
    GenerateResponseUseCase,
    ProcessMessageInput,
    ProcessMessageUseCase,
)

LOGGER = logging.getLogger(__name__)
# Django settings used instead
setup_tracing("conversation-temporal-worker", endpoint=os.environ.get("OTLP_ENDPOINT", ""))


def _somabrain_health() -> SomabrainHealthState:
    # Minimal health probe until degradation monitor is wired into Temporal context
    return SomabrainHealthState.NORMAL


def _build_use_case():
    kafka = KafkaSettings(
        bootstrap_servers=django_settings.KAFKA_BOOTSTRAP_SERVERS,
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
    )
    bus = KafkaEventBus(kafka)
    publisher = DurablePublisher(bus=bus)
    dlq = DeadLetterQueue(os.environ.get("CONVERSATION_INBOUND", "conversation.inbound"), bus=bus)
    # Use Django ORM Session model
    from admin.core.models import Session

    store = Session.objects
    profiles = ModelProfileStore.from_env()
    tenants = TenantConfig(path=os.environ.get("TENANT_CONFIG_PATH", "conf/tenants.yaml"))
    budgets = BudgetManager(url=django_settings.REDIS_URL, tenant_config=tenants)
    policy_client = PolicyClient(base_url=django_settings.OPA_URL, tenant_config=tenants)
    enforcer = ConversationPolicyEnforcer(policy_client)
    telemetry = TelemetryPublisher(publisher=publisher, store=TelemetryStore.from_env())
    soma = SomaBrainClient.get()
    router = RouterClient(base_url=os.environ.get("ROUTER_URL", ""))
    ctx_builder = ContextBuilder(
        somabrain=soma,
        metrics=None,
        token_counter=count_tokens,
        health_provider=_somabrain_health,
        use_optimal_budget=os.environ.get("CONTEXT_BUILDER_OPTIMAL_BUDGET", "false").lower()
        == "true",
    )
    gateway_base = os.environ.get("SA01_WORKER_GATEWAY_BASE")
    if not gateway_base:
        raise RuntimeError("SA01_WORKER_GATEWAY_BASE is required")
    gen = GenerateResponseUseCase(
        gateway_base=gateway_base,
        internal_token=os.environ.get("SA01_GATEWAY_INTERNAL_TOKEN", ""),
        publisher=publisher,
        outbound_topic=os.environ.get("CONVERSATION_OUTBOUND", "conversation.outbound"),
        default_model=os.environ.get("SA01_LLM_MODEL"),  # REQUIRED - no hardcoded default per VIBE
    )
    proc = ProcessMessageUseCase(
        session_repo=store,
        policy_enforcer=enforcer,
        memory_client=soma,
        publisher=publisher,
        context_builder=ctx_builder,
        response_generator=gen,
        outbound_topic=os.environ.get("CONVERSATION_OUTBOUND", "conversation.outbound"),
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
    temporal_host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
    # outbox_flush removed - feature never implemented
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
