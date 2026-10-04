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

from admin.core.application.use_cases.conversation.generate_response import (
    GenerateResponseUseCase,
)
from admin.core.application.use_cases.conversation.process_message import (
    ProcessMessageInput,
    ProcessMessageUseCase,
)
from services.common.budget_manager import BudgetManager
from services.common.memory_gateway import build_memory_gateway
from services.common.compensation import compensate_event
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
setup_tracing("conversation-temporal-worker", endpoint=os.environ.get("OTLP_ENDPOINT", ""))


def _build_use_case():
    kafka = KafkaSettings(
        bootstrap_servers=django_settings.KAFKA_BOOTSTRAP_SERVERS,
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=resolve_kafka_sasl_password(),
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
    telemetry = TelemetryPublisher(publisher=publisher)
    router = RouterClient(base_url=os.environ.get("ROUTER_URL", ""))

    gateway_base = os.environ.get("SA01_WORKER_GATEWAY_BASE")
    if not gateway_base:
        raise RuntimeError("SA01_WORKER_GATEWAY_BASE is required")
    # VIBE Rule 164: the gateway internal token is a credential and comes from
    # Vault, never from the environment.
    from services.common.unified_secret_manager import get_secret_manager

    gen = GenerateResponseUseCase(
        gateway_base=gateway_base,
        # No ``or ""``: an absent Vault secret is passed through as absent and
        # GenerateResponseUseCase refuses to run on it. Substituting an empty
        # string would send an empty X-Internal-Token — a dummy credential on a
        # live request (VIBE Rule 164).
        internal_token=get_secret_manager().get_credential("gateway_internal_token"),
        publisher=publisher,
        outbound_topic=os.environ.get("CONVERSATION_OUTBOUND", "conversation.outbound"),
        # REQUIRED, and no ``or ""``: an empty model is not a model.
        default_model=os.environ.get("SA01_LLM_MODEL"),
    )
    proc = ProcessMessageUseCase(
        session_repo=store,
        policy_enforcer=enforcer,
        gateway=build_memory_gateway(),
        publisher=publisher,
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
                session_id=event.get("session_id") or "",
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


@activity.defn
async def sleep_cycle_activity(tenant_id: str) -> dict:
    """Run one SomaBrain sleep/consolidation cycle for a tenant."""
    from admin.core.chat_orchestrator import get_chat_orchestrator

    orchestrator = await get_chat_orchestrator()
    await orchestrator.trigger_sleep_cycle(tenant_id=tenant_id, persona_id="")
    return {"tenant_id": tenant_id, "status": "triggered"}


@workflow.defn
class SleepCycleWorkflow:
    """Temporal owns the sleep/consolidation cycle (was un-scheduled)."""

    @workflow.run
    async def run(self, tenant_id: str) -> dict:
        return await workflow.execute_activity(
            sleep_cycle_activity,
            tenant_id,
            schedule_to_close_timeout=timedelta(seconds=600),
        )


@activity.defn
async def advance_jobs_activity(limit: int = 10) -> dict:
    """Claim and execute pending Job rows (JobPlanner created them; nothing advanced).

    Execution is the real MultimodalExecutor — a job is never marked completed
    without being run. If the executor cannot run a plan it is marked failed
    with the error, not silently left pending.
    """
    from services.common.job_planner import JobPlanner, JobStatus

    planner = JobPlanner()
    advanced = 0
    failed = 0
    executor = None
    try:
        from services.tool_executor.multimodal_executor import MultimodalExecutor

        executor = MultimodalExecutor()
        await executor.initialize()
    except Exception as exc:
        LOGGER.warning("MultimodalExecutor unavailable for job advance: %s", exc)

    for _ in range(max(1, int(limit))):
        plan = await planner.claim_next_pending()
        if plan is None or plan.id is None:
            break
        if executor is None:
            await planner.update_status(
                plan.id,
                JobStatus.FAILED,
                error_message="no job executor available",
            )
            failed += 1
            continue
        try:
            ok = await executor.execute_plan(plan.id)
            if ok:
                advanced += 1
            else:
                failed += 1
        except Exception as exc:
            await planner.update_status(plan.id, JobStatus.FAILED, error_message=str(exc))
            failed += 1
            LOGGER.warning("Job %s failed: %s", plan.id, exc)
    return {"advanced": advanced, "failed": failed}


@workflow.defn
class JobAdvanceWorkflow:
    """Temporal owns long-running job advancement."""

    @workflow.run
    async def run(self, limit: int = 10) -> dict:
        return await workflow.execute_activity(
            advance_jobs_activity,
            limit,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


@activity.defn
async def outbox_replay_activity(batch: int = 100) -> dict:
    """Drain the transactional outbox into Kafka (the one replay authority for events)."""
    from django.core.management import call_command
    from asgiref.sync import sync_to_async

    await sync_to_async(call_command)("publish_outbox", "--batch", str(batch))
    return {"batch": batch, "status": "drained"}


@workflow.defn
class OutboxReplayWorkflow:
    """Temporal owns outbox replay orchestration."""

    @workflow.run
    async def run(self, batch: int = 100) -> dict:
        return await workflow.execute_activity(
            outbox_replay_activity,
            batch,
            schedule_to_close_timeout=timedelta(seconds=300),
        )


def _schedule_specs() -> tuple:
    """Interval specs for the async cycle (topology/behaviour via env, not literals)."""
    from temporalio.client import ScheduleIntervalSpec

    sleep_h = float(os.environ.get("SA01_SLEEP_CYCLE_HOURS", "6"))
    jobs_s = float(os.environ.get("SA01_JOB_ADVANCE_SECONDS", "60"))
    outbox_s = float(os.environ.get("SA01_OUTBOX_REPLAY_SECONDS", "30"))
    return (
        ScheduleIntervalSpec(hours=sleep_h),
        ScheduleIntervalSpec(seconds=jobs_s),
        ScheduleIntervalSpec(seconds=outbox_s),
    )


async def _ensure_schedules(client: Client, task_queue: str) -> None:
    """Create the maintenance schedules if they are absent (idempotent)."""
    from temporalio.client import Schedule, ScheduleActionStartWorkflow, ScheduleSpec

    sleep_iv, jobs_iv, outbox_iv = _schedule_specs()
    default_tenant = os.environ.get("SA01_SLEEP_TENANT_ID") or os.environ.get(
        "AAAS_DEFAULT_TENANT_ID", ""
    )
    wanted = {
        "soma-sleep-cycle": ScheduleActionStartWorkflow(
            SleepCycleWorkflow.run,
            default_tenant,
            id="soma-sleep-cycle-tick",
            task_queue=task_queue,
        ),
        "soma-job-advance": ScheduleActionStartWorkflow(
            JobAdvanceWorkflow.run,
            10,
            id="soma-job-advance-tick",
            task_queue=task_queue,
        ),
        "soma-outbox-replay": ScheduleActionStartWorkflow(
            OutboxReplayWorkflow.run,
            100,
            id="soma-outbox-replay-tick",
            task_queue=task_queue,
        ),
    }
    specs = {
        "soma-sleep-cycle": ScheduleSpec(interval=sleep_iv),
        "soma-job-advance": ScheduleSpec(interval=jobs_iv),
        "soma-outbox-replay": ScheduleSpec(interval=outbox_iv),
    }
    for name, action in wanted.items():
        try:
            await client.get_schedule_handle(name).describe()
            continue
        except Exception:
            pass
        try:
            await client.create_schedule(
                name,
                Schedule(action=action, spec=specs[name]),
            )
            LOGGER.info("Temporal schedule created: %s on %s", name, task_queue)
        except Exception as exc:
            LOGGER.warning("Temporal schedule %s not created: %s", name, exc)


async def main() -> None:
    temporal_host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
    task_queue = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
    client = await Client.connect(temporal_host)
    await _ensure_schedules(client, task_queue)
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=[
            process_message_activity,
            sleep_cycle_activity,
            advance_jobs_activity,
            outbox_replay_activity,
        ],
        workflows=[
            ConversationWorkflow,
            SleepCycleWorkflow,
            JobAdvanceWorkflow,
            OutboxReplayWorkflow,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
