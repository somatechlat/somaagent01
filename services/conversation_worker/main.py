"""Compatibility shim and full implementation for the ConversationWorker.

The original project exposed a ``ConversationWorker`` class directly from this
module.  After the refactor the functional code lives in
``services.conversation_worker.service`` as ``ConversationWorkerService``.  To
maintain backward compatibility (the test suite still imports this path) we
re‑export the service class under the historic name **and** keep the original
implementation here.  The shim is lightweight – it simply aliases the new
class – and does not duplicate any business logic.
"""

from __future__ import annotations

# Re‑export the new service implementation under the legacy name.
from .service import ConversationWorkerService as ConversationWorker

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List
import json
import asyncpg

from jsonschema import ValidationError
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from services.common.memory_write_outbox import MemoryWriteOutbox, ensure_schema as ensure_mw_outbox_schema
from services.common.budget_manager import BudgetManager
from services.common.dlq import DeadLetterQueue
from services.common.escalation import EscalationDecision, should_escalate
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.model_costs import estimate_escalation_cost
from services.common.model_profiles import ModelProfileStore
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.publisher import DurablePublisher
from services.common.schema_validator import validate as validate_schema
from services.common.idempotency import generate_for_memory_payload
from services.common.router_client import RouterClient
from services.common.schema_validator import validate_event
from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
    RedisSessionCache,
)
from services.common.settings_sa01 import SA01Settings
from services.common.admin_settings import ADMIN_SETTINGS
from services.common.slm_client import ChatMessage
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from src.core.config import cfg
from observability.metrics import (
    ContextBuilderMetrics,
    llm_call_latency_seconds,
    llm_calls_total,
    llm_input_tokens_total,
    llm_output_tokens_total,
    thinking_policy_seconds,
    tokens_received_total,
)
from python.helpers.tokens import count_tokens
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState
import httpx
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer
import mimetypes
from pathlib import Path
from services.tool_executor.tool_registry import ToolRegistry

setup_logging()
LOGGER = logging.getLogger(__name__)
APP_SETTINGS = SA01Settings.from_env()
tracer = setup_tracing("conversation-worker", endpoint=APP_SETTINGS.otlp_endpoint)


MESSAGE_PROCESSING_COUNTER = Counter(
    "conversation_worker_messages_total",
    "Total number of conversation events processed",
    labelnames=("result",),
)
MESSAGE_LATENCY = Histogram(
    "conversation_worker_processing_seconds",
    "Time spent handling conversation events",
    labelnames=("path",),
)
SOMABRAIN_STATUS_GAUGE = Gauge(
    "conversation_worker_somabrain_status",
    "Current SomaBrain connectivity status for this worker (1=up, 0=down)",
)
SOMABRAIN_BUFFER_GAUGE = Gauge(
    "conversation_worker_somabrain_buffered_items",
    "Number of memory payloads buffered locally while SomaBrain is unavailable",
)
ESCALATION_ATTEMPTS = Counter(
    "conversation_worker_escalations_total",
    "Count of escalation attempts",
    labelnames=("status",),
)
SESSION_CACHE_SYNC = Counter(
    "conversation_worker_session_cache_sync_total",
    "Conversation worker attempts to synchronise session cache entries",
    labelnames=("result",),
)


def _normalize_usage(raw: Dict[str, Any] | None) -> dict[str, int]:
    """Coerce provider usage payloads into {input_tokens, output_tokens} ints."""
    payload: Dict[str, Any] = raw or {}
    prompt = payload.get("input_tokens", payload.get("prompt_tokens", 0))
    completion = payload.get("output_tokens", payload.get("completion_tokens", 0))
    try:
        prompt_val = int(prompt) if prompt is not None else 0
    except Exception:
        prompt_val = 0
    try:
        completion_val = int(completion) if completion is not None else 0
    except Exception:
        completion_val = 0
    return {"input_tokens": max(prompt_val, 0), "output_tokens": max(completion_val, 0)}


def _record_llm_success(model: str | None, input_tokens: int, output_tokens: int, elapsed: float) -> None:
    label = (model or "unknown").strip() or "unknown"
    llm_calls_total.labels(model=label, result="success").inc()
    llm_call_latency_seconds.labels(model=label).observe(max(elapsed, 0.0))
    if input_tokens:
        llm_input_tokens_total.labels(model=label).inc(max(input_tokens, 0))
    if output_tokens:
        llm_output_tokens_total.labels(model=label).inc(max(output_tokens, 0))


def _record_llm_failure(model: str | None) -> None:
    label = (model or "unknown").strip() or "unknown"
    llm_calls_total.labels(model=label, result="error").inc()

_METRICS_SERVER_STARTED = False


def _compose_outbound_metadata(
    base: Dict[str, Any] | None,
    *,
    source: str,
    status: str | None = None,
    analysis: Dict[str, Any] | None = None,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Merge hydrated session metadata into outbound payloads without mutation."""

    merged: Dict[str, Any] = dict(base or {})
    ingress_source = merged.get("source")
    if ingress_source and ingress_source != source:
        merged.setdefault("ingress_source", ingress_source)
    merged["source"] = source
    if status is not None:
        merged["status"] = status
    if analysis is not None:
        merged["analysis"] = analysis
    if extra:
        merged.update(extra)
    return merged


def ensure_metrics_server() -> None:
    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return
    metrics_port = int(cfg.env("CONVERSATION_METRICS_PORT", str(APP_SETTINGS.metrics_port)))
    if metrics_port <= 0:
        LOGGER.warning("Metrics server disabled", extra={"port": metrics_port})
        _METRICS_SERVER_STARTED = True
        return
    metrics_host = cfg.env("CONVERSATION_METRICS_HOST", APP_SETTINGS.metrics_host)
    start_http_server(metrics_port, addr=metrics_host)
    LOGGER.info(
        "Conversation worker metrics server started",
        extra={"host": metrics_host, "port": metrics_port},
    )
    _METRICS_SERVER_STARTED = True


@dataclass
class AnalysisResult:
    intent: str
    sentiment: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "sentiment": self.sentiment,
            "tags": self.tags,
        }


class ConversationPreprocessor:
    def analyze(self, message: str) -> AnalysisResult:
        text = message.strip()
        lower = text.lower()

        if not text:
            intent = "empty"
        elif lower.startswith(("how", "what", "why", "when", "where", "who")) or text.endswith("?"):
            intent = "question"
        elif any(keyword in lower for keyword in ["create", "build", "implement", "write"]):
            intent = "action_request"
        elif any(keyword in lower for keyword in ["fix", "bug", "issue", "error"]):
            intent = "problem_report"
        else:
            intent = "statement"

        tags: List[str] = []
        if any(word in lower for word in ["code", "python", "function", "class"]):
            tags.append("code")
        if any(word in lower for word in ["deploy", "docker", "kubernetes", "infra"]):
            tags.append("infrastructure")
        if any(word in lower for word in ["test", "validate", "qa"]):
            tags.append("testing")

        negatives = {"fail", "broken", "crash", "error", "issue"}
        positives = {"great", "thanks", "awesome", "good"}
        sentiment = "neutral"
        if any(word in lower for word in negatives):
            sentiment = "negative"
        elif any(word in lower for word in positives):
            sentiment = "positive"

        return AnalysisResult(intent=intent, sentiment=sentiment, tags=tags)


class ConversationWorker:
    def __init__(self) -> None:
        ensure_metrics_server()
        bootstrap_servers = ADMIN_SETTINGS.kafka_bootstrap_servers
        self.kafka_settings = KafkaSettings(
            bootstrap_servers=bootstrap_servers,
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
        self.bus = KafkaEventBus(self.kafka_settings)
        self.outbox = OutboxStore(dsn=ADMIN_SETTINGS.postgres_dsn)
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        redis_url = ADMIN_SETTINGS.redis_url
        self.dlq = DeadLetterQueue(self.settings["inbound"], bus=self.bus)
        self.cache = RedisSessionCache(url=redis_url)
        self.store = PostgresSessionStore(dsn=ADMIN_SETTINGS.postgres_dsn)
        # LLM calls are centralized via Gateway /v1/llm/invoke endpoints (no direct provider calls here)
        self._gateway_base = cfg.env("WORKER_GATEWAY_BASE", "http://gateway:8010").rstrip("/")
        self._internal_token = cfg.env("GATEWAY_INTERNAL_TOKEN")
        self.profile_store = ModelProfileStore.from_settings(APP_SETTINGS)
        tenant_config_path = cfg.env(
            "TENANT_CONFIG_PATH",
            APP_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"),
        )
        self.tenant_config = TenantConfig(path=tenant_config_path)
        self.budgets = BudgetManager(url=redis_url, tenant_config=self.tenant_config)
        policy_base = ADMIN_SETTINGS.opa_url
        self.policy_client = PolicyClient(base_url=policy_base, tenant_config=self.tenant_config)
        self.policy_enforcer = ConversationPolicyEnforcer(self.policy_client)
        telemetry_store = TelemetryStore.from_settings(APP_SETTINGS)
        self.telemetry = TelemetryPublisher(publisher=self.publisher, store=telemetry_store)
        # SomaBrain HTTP client (centralized memory backend)
        self.soma = SomaBrainClient.get()
        self._somabrain_degraded_until = 0.0
        self.context_metrics = ContextBuilderMetrics()
        self.context_builder = ContextBuilder(
            somabrain=self.soma,
            metrics=self.context_metrics,
            token_counter=count_tokens,
            health_provider=self._somabrain_health_state,
            on_degraded=self._mark_somabrain_degraded,
        )
        self.mem_outbox = MemoryWriteOutbox(dsn=ADMIN_SETTINGS.postgres_dsn)
        router_url = cfg.env("ROUTER_URL") or APP_SETTINGS.extra.get("router_url")
        self.router = RouterClient(base_url=router_url)
        self.deployment_mode = cfg.env("SOMA_AGENT_MODE", APP_SETTINGS.deployment_mode).upper()
        self.preprocessor = ConversationPreprocessor()
        self.escalation_enabled = cfg.env("ESCALATION_ENABLED", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.escalation_fallback_enabled = cfg.env(
            "ESCALATION_FALLBACK_ENABLED", "false"
        ).lower() in {"1", "true", "yes", "on"}

        # Tool registry for model‑led orchestration (no network hop)
        self.tool_registry = ToolRegistry()

        # ---------------------------------------------------------------------
        # Fail‑safe state & health monitoring for SomaBrain
        # ---------------------------------------------------------------------
        self._soma_brain_up: bool = True  # optimistic start
        self._transient_memory: list[dict[str, Any]] = []  # buffer when SomaBrain is down
        # Start background health monitor (runs for the lifetime of the worker).
        # In test environments (detected via the presence of the ``pytest`` module
        # or the ``PYTEST_CURRENT_TEST`` environment variable) we skip launching
        # the infinite monitor to avoid dangling asyncio tasks that prevent the
        # test process from exiting.
        import sys
        if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
            self._health_monitor_task = None
        else:
            self._health_monitor_task = asyncio.create_task(self._monitor_soma_brain())
        self._last_degraded_reason: str | None = None

        # ``__init__`` ends here – subsequent methods are defined at the class level.

    # ---------------------------------------------------------------------
    # Helper methods – health monitor & safe SomaBrain wrappers
    # ---------------------------------------------------------------------

    async def _monitor_soma_brain(self) -> None:
        """Periodically ping SomaBrain and update ``self._soma_brain_up``.

        Uses the shared :class:`SomaBrainClient` instance so that health checks
        respect the same base URL, TLS and auth configuration as normal memory
        operations. When the service becomes reachable again, any buffered
        memory items are flushed.
        """
        while True:
            try:
                # ``health()`` raises ``SomaClientError`` (or ``httpx`` errors)
                # on non‑2xx responses, which we treat as "down".
                # In test environments a fake ``soma`` may not implement ``health``.
                if hasattr(self.soma, "health"):
                    await self.soma.health()  # type: ignore[attr-defined]
                up = True
            except Exception:
                up = False
            previous = self._soma_brain_up
            self._soma_brain_up = up
            SOMABRAIN_STATUS_GAUGE.set(1.0 if self._soma_brain_up else 0.0)
            if self._soma_brain_up and not previous:
                await self._flush_transient_memory()
            await asyncio.sleep(5)

    def _enter_somabrain_degraded(self, reason: str, duration: float = 60.0) -> None:
        """Mark SomaBrain as degraded/down and remember the reason."""
        if not self._soma_brain_up:
            # Already marked down; extend degradation window and record latest reason.
            self._mark_somabrain_degraded(duration)
            self._last_degraded_reason = reason
            return
        LOGGER.warning(
            "Somabrain degraded – switching to degraded mode",
            extra={"reason": reason},
        )
        self._soma_brain_up = False
        SOMABRAIN_STATUS_GAUGE.set(0.0)
        self._mark_somabrain_degraded(duration)
        self._last_degraded_reason = reason

    def _degraded_response_text(self, hint: str | None = None) -> str:
        reason = hint or self._last_degraded_reason or "connectivity issues"
        return (
            "SomaBrain is currently unavailable, so I'm answering with the recent "
            f"conversation context only (reason: {reason})."
        )

    async def _flush_transient_memory(self) -> None:
        """Attempt to persist any buffered memory items now that SomaBrain is up."""
        if not self._transient_memory:
            SOMABRAIN_BUFFER_GAUGE.set(0.0)
            return
        pending = list(self._transient_memory)
        self._transient_memory.clear()
        SOMABRAIN_BUFFER_GAUGE.set(0.0)
        for payload in pending:
            try:
                await self.soma.save_memory(payload)
            except Exception:
                # If it fails again, re‑buffer the item and break to avoid busy loop
                self._transient_memory.append(payload)
                SOMABRAIN_BUFFER_GAUGE.set(len(self._transient_memory))
                break

    async def _safe_recall(self, *args, **kwargs) -> dict[str, Any]:
        """Wrap ``self.soma.recall`` with fail‑safe behaviour.

        Returns an empty dict when SomaBrain is unavailable.
        """
        if not self._soma_brain_up:
            return {}
        try:
            return await self.soma.recall(*args, **kwargs)
        except Exception:
            LOGGER.debug("SomaBrain recall failed – entering degraded mode", exc_info=True)
            self._enter_somabrain_degraded("recall_failure")
            return {}

    async def _safe_save_memory(self, payload: dict[str, Any]) -> None:
        """Wrap ``self.soma.save_memory`` with buffering when the service is down."""
        if not self._soma_brain_up:
            self._transient_memory.append(payload)
            SOMABRAIN_BUFFER_GAUGE.set(len(self._transient_memory))
            return
        try:
            await self.soma.save_memory(payload)
        except Exception:
            LOGGER.debug("SomaBrain save_memory failed – buffering payload", exc_info=True)
            self._enter_somabrain_degraded("save_memory_failure")
            self._transient_memory.append(payload)
            SOMABRAIN_STATUS_GAUGE.set(0.0)
            SOMABRAIN_BUFFER_GAUGE.set(len(self._transient_memory))

    def _somabrain_health_state(self) -> SomabrainHealthState:
        if not self._soma_brain_up:
            return SomabrainHealthState.DOWN
        if time.time() < self._somabrain_degraded_until:
            return SomabrainHealthState.DEGRADED
        return SomabrainHealthState.NORMAL

    def _mark_somabrain_degraded(self, duration: float) -> None:
        self._somabrain_degraded_until = max(self._somabrain_degraded_until, time.time() + duration)

    async def _fetch_planner_priors(
        self,
        *,
        tenant_id: Optional[str],
        persona_id: Optional[str],
        session_id: Optional[str],
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Retrieve recent successful tasks/tools from SomaBrain to bias planner."""
        payload = {
            "tenant_id": tenant_id,
            "persona_id": persona_id,
            "session_id": session_id,
            "intent": analysis.get("intent"),
            "tags": analysis.get("tags") or [],
        }
        try:
            resp = await self.soma.plan_suggest(payload)
            priors = resp.get("priors") or resp.get("suggestions") or []
            return priors if isinstance(priors, list) else []
        except Exception:
            LOGGER.debug("planner priors fetch failed", exc_info=True)
            return []

    def _history_events_to_messages(self, events: list[dict[str, Any]]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for entry in events:
            if not isinstance(entry, dict):
                continue
            role = entry.get("type")
            if role == "user":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "user", "content": str(content)})
            elif role == "assistant":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "assistant", "content": str(content)})
        return messages

    def _legacy_prompt_messages(
        self,
        history: list[dict[str, Any]],
        event: dict[str, Any],
        analysis_prompt: ChatMessage,
        priors_prompt: list[ChatMessage] | None = None,
    ) -> list[ChatMessage]:
        messages: list[ChatMessage] = []
        for item in reversed(history):
            if item.get("type") == "user":
                messages.append(ChatMessage(role="user", content=item.get("message", "")))
            elif item.get("type") == "assistant":
                messages.append(ChatMessage(role="assistant", content=item.get("message", "")))
        if not messages or messages[-1].role != "user":
            messages.append(ChatMessage(role="user", content=event.get("message", "")))
        messages.insert(0, analysis_prompt)
        if priors_prompt:
            for msg in reversed(priors_prompt):
                messages.insert(0, msg)
        return messages

    def _context_builder_max_tokens(self) -> int:
        try:
            return max(512, int(cfg.env("CONTEXT_BUILDER_MAX_TOKENS", "4096")))
        except Exception:
            return 4096

    

    async def _background_recall_context(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        base_metadata: dict[str, Any],
        analysis_metadata: dict[str, Any],
        query: str,
        stop_event: asyncio.Event,
    ) -> None:
        """Continuously recall memory for a session and publish updates.

        The recall loop respects the following environment configuration:

        * ``SOMABRAIN_RECALL_TOPK`` – number of results per request.
        * ``SOMABRAIN_RECALL_CHUNK_SIZE`` – page size for paging through results.
        * ``SOMABRAIN_CONTEXT_UPDATE_MAX_ITEMS`` – maximum number of items to include in a single ``context.update`` payload.
        * ``SOMABRAIN_CONTEXT_UPDATE_MAX_STRING`` – maximum length of any string field within the payload.
        * ``SOMABRAIN_CONTEXT_UPDATE_MAX_BYTES`` – overall size limit (UTF‑8 bytes) for the payload.
        """
        top_k = int(cfg.env("SOMABRAIN_RECALL_TOPK", "8"))
        chunk_size = int(cfg.env("SOMABRAIN_RECALL_CHUNK_SIZE", "10"))
        max_items = int(cfg.env("SOMABRAIN_CONTEXT_UPDATE_MAX_ITEMS", "100"))
        max_string = int(cfg.env("SOMABRAIN_CONTEXT_UPDATE_MAX_STRING", "1000"))
        max_bytes = int(cfg.env("SOMABRAIN_CONTEXT_UPDATE_MAX_BYTES", "50000"))

        chunk_index = 0
        while not stop_event.is_set():
            try:
                resp = await self._safe_recall(
                    query,
                    top_k=top_k,
                    chunk_size=chunk_size,
                    chunk_index=chunk_index,
                    session_id=session_id,
                    universe=base_metadata.get("universe_id"),
                )
            except Exception:
                LOGGER.debug("Recall request failed", exc_info=True)
                break
            # When SomaBrain is marked down, _safe_recall returns an empty
            # payload and flips ``self._soma_brain_up`` to ``False``. In that
            # case we stay in a degraded loop and rely on the health monitor
            # to flip the flag back to True instead of treating this as an
            # end-of-stream condition.
            if not self._soma_brain_up:
                await asyncio.sleep(0.5)
                continue
            results = resp.get("results", [])
            if not results:
                break
            # Apply clamping limits
            truncated = False
            if len(results) > max_items:
                results = results[:max_items]
                truncated = True
            # Enforce string length limits on payload fields if present
            for item in results:
                for k, v in list(item.items()):
                    if isinstance(v, str) and len(v) > max_string:
                        item[k] = v[:max_string]
            recall_payload: dict[str, Any] = {"results": results}
            # Enforce total byte size limit
            payload_bytes = len(json.dumps(recall_payload, ensure_ascii=False).encode("utf-8"))
            if payload_bytes > max_bytes:
                recall_payload = {"_summary": "truncated"}
                truncated = True
            if truncated and not recall_payload.get("_summary"):
                recall_payload["_summary"] = f"truncated to {max_items} items"

            event = {
                "type": "context.update",
                "metadata": {
                    "source": "memory",
                    "recall": recall_payload,
                },
                "session_id": session_id,
                "tenant": base_metadata.get("tenant"),
                "persona_id": persona_id,
            }
            # Publish – ignore errors to keep background task alive
            try:
                await self.publisher.publish(
                    self.settings["outbound"],
                    event,
                    session_id=session_id,
                    tenant=base_metadata.get("tenant"),
                )
            except Exception:
                LOGGER.debug("Failed to publish context.update", exc_info=True)
            # Prepare next page
            chunk_index += 1
            await asyncio.sleep(0.05)

    async def _background_recall(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        base_metadata: dict[str, Any],
        analysis_metadata: dict[str, Any],
        query: str,
    ) -> tuple[asyncio.Task, asyncio.Event]:
        """Start a background recall task and return the task and its stop event.

        The caller can cancel the task by setting the returned ``stop_event``.
        """
        stop_event = asyncio.Event()
        task = asyncio.create_task(
            self._background_recall_context(
                session_id=session_id,
                persona_id=persona_id,
                base_metadata=base_metadata,
                analysis_metadata=analysis_metadata,
                query=query,
                stop_event=stop_event,
            )
        )
        return task, stop_event

    async def _extract_text_from_path(self, path: str) -> str:
        """Best-effort text extraction for common file types.

        Uses lightweight heuristics and optional libraries if present. Never raises.
        """
        try:
            p = Path(path)
            if not p.exists() or not p.is_file():
                return ""
            mime, _ = mimetypes.guess_type(str(p))
            mime = mime or "application/octet-stream"
            # Text-like
            if mime.startswith("text/") or mime in {"application/json", "application/xml"}:
                try:
                    return p.read_text(errors="ignore")[:200_000]
                except Exception:
                    try:
                        return p.read_bytes()[:200_000].decode("utf-8", errors="ignore")
                    except Exception:
                        return ""
            # PDF via PyMuPDF if available
            if mime == "application/pdf" or p.suffix.lower() == ".pdf":
                try:
                    import fitz  # PyMuPDF

                    text_parts: list[str] = []
                    with fitz.open(str(p)) as doc:
                        for page in doc:
                            text_parts.append(page.get_text("text"))
                    return "\n".join(text_parts)[:400_000]
                except Exception:
                    return ""
            # Images via pytesseract if available
            if mime.startswith("image/"):
                try:
                    from PIL import Image  # type: ignore
                    import pytesseract  # type: ignore

                    img = Image.open(str(p))
                    return pytesseract.image_to_string(img)[:200_000]
                except Exception:
                    return ""
            # Fallback: return nothing for unknown binary types
            return ""
        except Exception:
            return ""

    async def _ingest_attachment(self, *, path: str, session_id: str, persona_id: str | None, tenant: str, metadata: dict[str, Any]) -> None:
        try:
            text = await self._extract_text_from_path(path)
            if not text:
                return
            payload = {
                "id": str(uuid.uuid4()),
                "type": "attachment_ingest",
                "role": "user",
                "content": text,
                "attachments": [path],
                "session_id": session_id,
                "persona_id": persona_id,
                "metadata": {
                    **dict(metadata or {}),
                    "source": "ingest",
                    "agent_profile_id": (metadata or {}).get("agent_profile_id"),
                    "universe_id": (metadata or {}).get("universe_id") or cfg.env("SOMA_NAMESPACE"),
                },
            }
            payload["idempotency_key"] = generate_for_memory_payload(payload)
            # Fail-closed: default to deny when OPA is unavailable
            allow_memory = False
            try:
                with thinking_policy_seconds.labels(policy="memory.write").time():
                    allow_memory = await self.policy_client.evaluate(
                        PolicyRequest(
                            tenant=tenant,
                            persona_id=persona_id,
                            action="memory.write",
                            resource="somabrain",
                            context={
                                "payload_type": payload.get("type"),
                                "role": payload.get("role"),
                                "session_id": session_id,
                                "metadata": payload.get("metadata", {}),
                            },
                        )
                    )
            except Exception:
                LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy", exc_info=True)
            if not allow_memory:
                return
            wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
            try:
                result = await self.soma.remember(payload)
            except Exception:
                # best-effort: enqueue to mem outbox for retry
                self._enter_somabrain_degraded("remember_failure")
                try:
                    await self.mem_outbox.enqueue(
                        payload=payload,
                        tenant=tenant,
                        session_id=session_id,
                        persona_id=persona_id,
                        idempotency_key=payload.get("idempotency_key"),
                        dedupe_key=str(payload.get("id")),
                    )
                except Exception:
                    pass
                return
            try:
                wal_event = {
                    "type": "memory.write",
                    "role": "user",
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "tenant": tenant,
                    "payload": payload,
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
                    dedupe_key=str(payload.get("id")),
                    session_id=session_id,
                    tenant=tenant,
                )
            except Exception:
                LOGGER.debug("Failed to publish memory WAL (ingest)", exc_info=True)
        except Exception:
            LOGGER.debug("Attachment ingest failed", exc_info=True)

    def _should_offload_ingest(self, path: str) -> bool:
        try:
            threshold_mb = float(cfg.env("INGEST_OFFLOAD_THRESHOLD_MB", "5"))
        except ValueError:
            threshold_mb = 5.0
        try:
            size = Path(path).stat().st_size
        except Exception:
            size = 0
        return size > int(threshold_mb * 1024 * 1024)

    def _attachment_id_from_str(self, value: str) -> str | None:
        try:
            s = (value or "").strip()
            if not s:
                return None
            import re
            # Raw UUID
            if re.fullmatch(r"[0-9a-fA-F-]{36}", s):
                return s
            m = re.search(r"/v1/attachments/([0-9a-fA-F-]{36})", s)
            if m:
                return m.group(1)
        except Exception:
            return None
        return None

    async def _attachment_head(self, att_id: str, tenant: str) -> dict[str, Any]:
        base = cfg.env("WORKER_GATEWAY_BASE", "http://gateway:8010").rstrip("/")
        token = cfg.env("GATEWAY_INTERNAL_TOKEN")
        url = f"{base}/internal/attachments/{att_id}/binary"
        headers = {"X-Internal-Token": token or ""}
        if tenant:
            headers["X-Tenant-Id"] = tenant
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.head(url, headers=headers)
                if resp.status_code in {404, 405}:
                    return {}
                size = int(resp.headers.get("x-attachment-size") or 0)
                return {"size": size}
        except Exception:
            return {}

    def _should_offload_ingest_id(self, size: int | None) -> bool:
        try:
            threshold_mb = float(cfg.env("INGEST_OFFLOAD_THRESHOLD_MB", "5"))
        except ValueError:
            threshold_mb = 5.0
        if size is None or size <= 0:
            return True
        return size > int(threshold_mb * 1024 * 1024)

    async def _fetch_attachment_bytes(self, *, att_id: str, tenant: str) -> tuple[bytes, str, str]:
        base = cfg.env("WORKER_GATEWAY_BASE", "http://gateway:8010").rstrip("/")
        token = cfg.env("GATEWAY_INTERNAL_TOKEN")
        if not token:
            raise RuntimeError("Internal token not configured")
        url = f"{base}/internal/attachments/{att_id}/binary"
        headers = {"X-Internal-Token": token}
        if tenant:
            headers["X-Tenant-Id"] = str(tenant)
        async with httpx.AsyncClient(timeout=float(cfg.env("WORKER_FETCH_TIMEOUT", "10"))) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                raise FileNotFoundError("attachment not found")
            resp.raise_for_status()
            data = resp.content
            mime = resp.headers.get("content-type", "application/octet-stream")
            filename = "attachment"
            try:
                cd = resp.headers.get("content-disposition", "")
                if "filename=" in cd:
                    filename = cd.split("filename=", 1)[1].strip().strip('"')
            except Exception:
                pass
            return data, mime, filename

    async def _extract_text_from_blob(self, *, data: bytes, mime: str, filename: str) -> str:
        try:
            if (mime or "").startswith("text/") or mime in {"application/json", "application/xml"}:
                try:
                    return data.decode("utf-8", errors="ignore")[:200_000]
                except Exception:
                    return data.decode("latin-1", errors="ignore")[:200_000]
            if mime == "application/pdf" or (filename or "").lower().endswith(".pdf"):
                try:
                    import fitz  # type: ignore
                    import io as _io
                    parts: list[str] = []
                    with fitz.open(stream=_io.BytesIO(data), filetype="pdf") as doc:
                        for page in doc:
                            parts.append(page.get_text("text"))
                    return "\n".join(parts)[:400_000]
                except Exception:
                    return ""
            if (mime or "").startswith("image/"):
                try:
                    from PIL import Image  # type: ignore
                    import pytesseract  # type: ignore
                    import io as _io
                    img = Image.open(_io.BytesIO(data))
                    return pytesseract.image_to_string(img)[:200_000]
                except Exception:
                    return ""
            return ""
        except Exception:
            return ""

    async def _ingest_attachment_by_id(self, *, att_id: str, session_id: str, persona_id: str | None, tenant: str, metadata: dict[str, Any]) -> None:
        try:
            data, mime, filename = await self._fetch_attachment_bytes(att_id=att_id, tenant=tenant)
            text = await self._extract_text_from_blob(data=data, mime=mime, filename=filename)
            if not text:
                return
            path_ref = f"/v1/attachments/{att_id}"
            payload = {
                "id": str(uuid.uuid4()),
                "type": "attachment_ingest",
                "role": "user",
                "content": text,
                "attachments": [path_ref],
                "session_id": session_id,
                "persona_id": persona_id,
                "metadata": {
                    **dict(metadata or {}),
                    "source": "ingest",
                    "agent_profile_id": (metadata or {}).get("agent_profile_id"),
                    "universe_id": (metadata or {}).get("universe_id") or cfg.env("SOMA_NAMESPACE"),
                },
            }
            payload["idempotency_key"] = generate_for_memory_payload(payload)
            allow_memory = False
            try:
                with thinking_policy_seconds.labels(policy="memory.write").time():
                    allow_memory = await self.policy_client.evaluate(
                        PolicyRequest(
                            tenant=tenant,
                            persona_id=persona_id,
                            action="memory.write",
                            resource="somabrain",
                            context={
                                "payload_type": payload.get("type"),
                                "role": payload.get("role"),
                                "session_id": session_id,
                                "metadata": payload.get("metadata", {}),
                            },
                        )
                    )
            except Exception:
                LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy", exc_info=True)
            if not allow_memory:
                return
            wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
            try:
                result = await self.soma.remember(payload)
            except Exception:
                self._enter_somabrain_degraded("remember_failure")
                try:
                    await self.mem_outbox.enqueue(
                        payload=payload,
                        tenant=tenant,
                        session_id=session_id,
                        persona_id=persona_id,
                        idempotency_key=payload.get("idempotency_key"),
                        dedupe_key=str(payload.get("id")),
                    )
                except Exception:
                    pass
                return
            try:
                wal_event = {
                    "type": "memory.write",
                    "role": "user",
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "tenant": tenant,
                    "payload": payload,
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
                    dedupe_key=str(payload.get("id")),
                    session_id=session_id,
                    tenant=tenant,
                )
            except Exception:
                LOGGER.debug("Failed to publish memory WAL (ingest by id)", exc_info=True)
        except Exception:
            LOGGER.debug("Attachment ingest by id failed", exc_info=True)

    async def _stream_response_via_gateway(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
        base_metadata: Dict[str, Any],
        role: str = "dialogue",
        model_hint: str | None = None,
    ) -> tuple[str, dict[str, int]]:
        buffer: list[str] = []
        usage = {"input_tokens": 0, "output_tokens": 0}
        url = f"{self._gateway_base}/v1/llm/invoke/stream"
        model_label = (model_hint or slm_kwargs.get("model") or cfg.env("SLM_MODEL", "unknown")).strip() or "unknown"
        start_time = time.perf_counter()

        def _finalize(text_value: str, usage_value: dict[str, int]) -> tuple[str, dict[str, int]]:
            elapsed = time.perf_counter() - start_time
            normalized = _normalize_usage(usage_value)
            _record_llm_success(model_label, normalized["input_tokens"], normalized["output_tokens"], elapsed)
            return text_value, normalized

        # Build overrides but omit empty strings (e.g. base_url="") while allowing 0/0.0
        ov: dict[str, Any] = {}
        for k, v in {
            "model": slm_kwargs.get("model"),
            "base_url": slm_kwargs.get("base_url"),
            "temperature": slm_kwargs.get("temperature"),
            "kwargs": slm_kwargs.get("metadata") or slm_kwargs.get("kwargs"),
        }.items():
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            ov[k] = v

        payload = {
            "role": role,
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": (base_metadata or {}).get("tenant"),
            "messages": [m.__dict__ for m in messages],
            "overrides": ov,
        }
        headers = {"X-Internal-Token": self._internal_token or ""}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.is_error:
                        # Surface upstream error text for telemetry/debugging
                        body = await resp.aread()
                        raise RuntimeError(
                            f"Gateway invoke stream error {resp.status_code}: {body.decode('utf-8', errors='ignore')[:512]}"
                        )
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except Exception:
                            continue
                        # Pass-through OpenAI-style chunk
                        choices = chunk.get("choices")
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content_piece = delta.get("content", "")
                        if content_piece:
                            buffer.append(content_piece)
                            metadata = _compose_outbound_metadata(
                                base_metadata,
                                source="slm",
                                status="streaming",
                                analysis=analysis_metadata,
                                extra={"stream_index": len(buffer)},
                            )
                            streaming_event = {
                                "event_id": str(uuid.uuid4()),
                                "session_id": session_id,
                                "persona_id": persona_id,
                                "role": "assistant",
                                "message": "".join(buffer),
                                "metadata": metadata,
                                "version": "sa01-v1",
                                "type": "assistant.stream",
                            }
                            await self.publisher.publish(
                                self.settings["outbound"],
                                streaming_event,
                                dedupe_key=streaming_event.get("event_id"),
                                session_id=session_id,
                                tenant=(metadata or {}).get("tenant"),
                            )
                        chunk_usage = chunk.get("usage")
                        if isinstance(chunk_usage, dict):
                            usage["input_tokens"] = int(chunk_usage.get("prompt_tokens", usage["input_tokens"]))
                            usage["output_tokens"] = int(chunk_usage.get("completion_tokens", usage["output_tokens"]))
            text = "".join(buffer)
            if not text:
                # Fallback: call non-streaming invoke once to get a definitive answer
                try:
                    url2 = f"{self._gateway_base}/v1/llm/invoke"
                    ov2: dict[str, Any] = {}
                    for k, v in {
                        "model": slm_kwargs.get("model"),
                        "base_url": slm_kwargs.get("base_url"),
                        "temperature": slm_kwargs.get("temperature"),
                        "kwargs": slm_kwargs.get("metadata") or slm_kwargs.get("kwargs"),
                    }.items():
                        if v is None:
                            continue
                        if isinstance(v, str) and v.strip() == "":
                            continue
                        ov2[k] = v
                    body2 = {
                        "role": "dialogue",
                        "session_id": session_id,
                        "persona_id": persona_id,
                        "tenant": (base_metadata or {}).get("tenant"),
                        "messages": [m.__dict__ for m in messages],
                        "overrides": ov2,
                    }
                    headers2 = {"X-Internal-Token": self._internal_token or ""}
                    async with httpx.AsyncClient(timeout=30.0) as client2:
                        resp2 = await client2.post(url2, json=body2, headers=headers2)
                        if resp2.is_error:
                            raise RuntimeError(f"Gateway invoke error {resp2.status_code}: {resp2.text[:512]}")
                        data2 = resp2.json()
                        content2 = data2.get("content", "")
                        usage2 = data2.get("usage", {"input_tokens": 0, "output_tokens": 0})
                        if content2:
                            return _finalize(content2, usage2)
                except Exception:
                    # Bubble up to callers; higher-level handler will surface a meaningful error
                    pass
                raise RuntimeError("Empty response from streaming Gateway/SLM")
            return _finalize(text, usage)
        except Exception:
            _record_llm_failure(model_label)
            raise

    async def _generate_response(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
        base_metadata: Dict[str, Any],
    ) -> tuple[str, dict[str, int]]:
        model_label = (slm_kwargs.get("model") or cfg.env("SLM_MODEL", "unknown")).strip() or "unknown"
        try:
            return await self._stream_response_via_gateway(
                session_id=session_id,
                persona_id=persona_id,
                messages=messages,
                slm_kwargs=slm_kwargs,
                analysis_metadata=analysis_metadata,
                base_metadata=base_metadata,
                role="dialogue",
                model_hint=model_label,
            )
        except Exception as exc:
            LOGGER.warning(
                "Streaming unavailable via Gateway, falling back to non-stream invoke",
                extra={"error": str(exc)},
            )
            # Fallback: non-stream invoke
            url = f"{self._gateway_base}/v1/llm/invoke"
            # Build non-stream overrides similarly to streaming path (omit empty strings)
            ov: dict[str, Any] = {}
            for k, v in {
                "model": slm_kwargs.get("model"),
                "base_url": slm_kwargs.get("base_url"),
                "temperature": slm_kwargs.get("temperature"),
                "kwargs": slm_kwargs.get("metadata") or slm_kwargs.get("kwargs"),
            }.items():
                if v is None:
                    continue
                if isinstance(v, str) and v.strip() == "":
                    continue
                ov[k] = v

            body = {
                "role": "dialogue",
                "session_id": session_id,
                "persona_id": persona_id,
                "tenant": (base_metadata or {}).get("tenant"),
                "messages": [m.__dict__ for m in messages],
                "overrides": ov,
            }
            headers = {"X-Internal-Token": self._internal_token or ""}
            start_time = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=body, headers=headers)
                    if resp.is_error:
                        raise RuntimeError(f"Gateway invoke error {resp.status_code}: {resp.text[:512]}")
                    data = resp.json()
                    content = data.get("content", "")
                    usage = _normalize_usage(data.get("usage"))
                    tool_calls = data.get("tool_calls")
                    if (not content) and isinstance(tool_calls, list) and tool_calls:
                        _record_llm_success(
                            model_label,
                            usage["input_tokens"],
                            usage["output_tokens"],
                            time.perf_counter() - start_time,
                        )
                        for call in tool_calls:
                            try:
                                fn = (call or {}).get("function") or {}
                                tool_name = fn.get("name") or (call.get("name") if isinstance(call, dict) else "")
                                raw_args = fn.get("arguments") if fn else (call.get("arguments") if isinstance(call, dict) else "")
                            except Exception:
                                tool_name = ""
                                raw_args = ""
                            if not tool_name:
                                continue
                            try:
                                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                            except Exception:
                                args = {"_raw": raw_args}

                            req_id = str(uuid.uuid4())
                            metadata = {
                                **dict(base_metadata or {}),
                                "tenant": (base_metadata or {}).get("tenant", "default"),
                                "request_id": req_id,
                                "source": "tool_orchestrator",
                            }
                            event = {
                                "event_id": req_id,
                                "session_id": session_id,
                                "persona_id": persona_id,
                                "tool_name": tool_name,
                                "args": args,
                                "metadata": metadata,
                            }
                            try:
                                await self.publisher.publish(
                                    cfg.env("TOOL_REQUESTS_TOPIC", "tool.requests"),
                                    event,
                                    dedupe_key=req_id,
                                    session_id=session_id,
                                    tenant=metadata.get("tenant"),
                                )
                            except Exception:
                                LOGGER.debug("Failed to publish tool request (non-stream)", exc_info=True)
                                continue

                            result_event = await self._wait_for_tool_result(
                                session_id=session_id,
                                request_id=req_id,
                                timeout_seconds=float(cfg.env("TOOL_RESULT_TIMEOUT", "20")),
                            )
                            if result_event:
                                payload = result_event.get("payload")
                                try:
                                    tool_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
                                except Exception:
                                    tool_text = str(payload)
                                messages.append(
                                    ChatMessage(
                                        role="system",
                                        content=f"Tool {tool_name} result: {tool_text[:4000]}",
                                    )
                                )
                            else:
                                messages.append(
                                    ChatMessage(
                                        role="system",
                                        content=f"Tool {tool_name} did not return a result in time.",
                                    )
                                )

                        body2 = {
                            "role": "dialogue",
                            "session_id": session_id,
                            "persona_id": persona_id,
                            "tenant": (base_metadata or {}).get("tenant"),
                            "messages": [m.__dict__ for m in messages],
                            "overrides": ov,
                        }
                        second_start = time.perf_counter()
                        resp2 = await client.post(url, json=body2, headers=headers)
                        if resp2.is_error:
                            raise RuntimeError(f"Gateway invoke error {resp2.status_code}: {resp2.text[:512]}")
                        data2 = resp2.json()
                        content2 = data2.get("content", "")
                        usage2 = _normalize_usage(data2.get("usage"))
                        if not content2:
                            raise RuntimeError("Empty response from Gateway invoke after tools")
                        _record_llm_success(
                            model_label,
                            usage2["input_tokens"],
                            usage2["output_tokens"],
                            time.perf_counter() - second_start,
                        )
                        return content2, usage2
                    if not content:
                        raise RuntimeError("Empty response from Gateway invoke")
                    _record_llm_success(
                        model_label,
                        usage["input_tokens"],
                        usage["output_tokens"],
                        time.perf_counter() - start_time,
                    )
                    return content, usage
            except Exception:
                _record_llm_failure(model_label)
                raise

    def _tools_openai_schema(self) -> list[dict[str, Any]]:
        """Build OpenAI-style tools array from local registry."""
        tools: list[dict[str, Any]] = []
        try:
            # Lazy load at first use in case dependencies are heavy
            if not list(self.tool_registry.list()):
                # load tools if not already loaded
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # best-effort async call inside running loop
                    # Use ensure_future to avoid blocking
                    loop.create_task(self.tool_registry.load_all_tools())
                else:
                    # Synchronous wait when not in event loop (unlikely here)
                    loop.run_until_complete(self.tool_registry.load_all_tools())
        except Exception:
            LOGGER.debug("Failed to load tools for schema", exc_info=True)
        for t in self.tool_registry.list():
            try:
                schema = None
                handler = getattr(t, "handler", None)
                if handler and hasattr(handler, "input_schema"):
                    schema = handler.input_schema()
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": getattr(t, "description", None) or "",
                            "parameters": schema or {"type": "object"},
                        },
                    }
                )
            except Exception:
                continue
        return tools

    async def _wait_for_tool_result(
        self,
        *,
        session_id: str,
        request_id: str,
        timeout_seconds: float = 20.0,
        poll_interval: float = 0.25,
    ) -> dict[str, Any] | None:
        """Poll session events for a matching tool result with the request_id in metadata."""
        deadline = time.time() + max(0.1, timeout_seconds)
        while time.time() < deadline:
            try:
                events = await self.store.list_events(session_id, limit=100)
            except Exception:
                events = []
            for ev in events:
                try:
                    if ev.get("type") != "tool":
                        continue
                    meta = ev.get("metadata") or {}
                    if meta.get("request_id") == request_id:
                        return ev
                except Exception:
                    continue
            await asyncio.sleep(poll_interval)
        return None

    async def _generate_with_tools(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
        base_metadata: Dict[str, Any],
    ) -> tuple[str, dict[str, int]]:
        """Invoke the LLM with tool schemas; if the model emits tool calls, execute them and continue."""
        # Ensure tool schemas are provided to the model
        tool_defs = self._tools_openai_schema()
        if tool_defs:
            slm_kwargs = dict(slm_kwargs)
            extra_kwargs = dict(slm_kwargs.get("kwargs") or slm_kwargs.get("metadata") or {})
            extra_kwargs["tools"] = tool_defs
            extra_kwargs["tool_choice"] = "auto"
            slm_kwargs["metadata"] = extra_kwargs

        # Stream and detect tool calls
        url = f"{self._gateway_base}/v1/llm/invoke/stream"
        # Build overrides and omit empty-string values (esp. base_url="")
        ov: dict[str, Any] = {}
        for k, v in {
            "model": slm_kwargs.get("model"),
            "base_url": slm_kwargs.get("base_url"),
            "temperature": slm_kwargs.get("temperature"),
            "kwargs": slm_kwargs.get("metadata") or slm_kwargs.get("kwargs"),
        }.items():
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            ov[k] = v

        payload = {
            "role": "dialogue",
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": (base_metadata or {}).get("tenant"),
            "messages": [m.__dict__ for m in messages],
            "overrides": ov,
        }
        headers = {"X-Internal-Token": self._internal_token or ""}

        buffer: list[str] = []
        usage = {"input_tokens": 0, "output_tokens": 0}
        tool_calls: list[dict[str, Any]] = []
        tc_args_acc: dict[int, dict[str, Any]] = {}
        tc_name_acc: dict[int, str] = {}

        model_label = (slm_kwargs.get("model") or cfg.env("SLM_MODEL", "unknown")).strip() or "unknown"
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    if resp.is_error:
                        body = await resp.aread()
                        raise RuntimeError(
                            f"Gateway invoke stream error {resp.status_code}: {body.decode('utf-8', errors='ignore')[:512]}"
                        )
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except Exception:
                            continue
                        choices = chunk.get("choices")
                        if not choices:
                            continue
                        ch0 = choices[0]
                        delta = ch0.get("delta", {})
                        content_piece = delta.get("content")
                        if content_piece:
                            buffer.append(content_piece)
                            metadata = _compose_outbound_metadata(
                                base_metadata,
                                source="slm",
                                status="streaming",
                                analysis=analysis_metadata,
                                extra={"stream_index": len(buffer)},
                            )
                            streaming_event = {
                                "event_id": str(uuid.uuid4()),
                                "session_id": session_id,
                                "persona_id": persona_id,
                                "role": "assistant",
                                "message": "".join(buffer),
                                "metadata": metadata,
                                "version": "sa01-v1",
                                "type": "assistant.stream",
                            }
                            await self.publisher.publish(
                                self.settings["outbound"],
                                streaming_event,
                                dedupe_key=streaming_event.get("event_id"),
                                session_id=session_id,
                                tenant=(metadata or {}).get("tenant"),
                            )
                        tc = delta.get("tool_calls")
                        if isinstance(tc, list) and tc:
                            for item in tc:
                                try:
                                    idx = int(item.get("index", 0))
                                except Exception:
                                    idx = 0
                                func = (item.get("function") or {})
                                name_part = func.get("name")
                                if name_part:
                                    tc_name_acc[idx] = name_part
                                args_part = func.get("arguments")
                                if isinstance(args_part, str) and args_part:
                                    prev = tc_args_acc.get(idx, {}).get("_raw", "")
                                    tc_args_acc.setdefault(idx, {})["_raw"] = prev + args_part
                        chunk_usage = chunk.get("usage")
                        if isinstance(chunk_usage, dict):
                            usage["input_tokens"] = int(chunk_usage.get("prompt_tokens", usage["input_tokens"]))
                            usage["output_tokens"] = int(chunk_usage.get("completion_tokens", usage["output_tokens"]))
                        if ch0.get("finish_reason") == "tool_calls":
                            break
        except Exception:
            _record_llm_failure(model_label)
            raise

        # If we received tool call data, execute tools; otherwise return text
        if tc_args_acc or tc_name_acc:
            usage_norm = _normalize_usage(usage)
            _record_llm_success(
                model_label,
                usage_norm["input_tokens"],
                usage_norm["output_tokens"],
                time.perf_counter() - start_time,
            )
            # Compose final tool_calls list
            max_index = max(list(tc_name_acc.keys()) + list(tc_args_acc.keys())) if (tc_name_acc or tc_args_acc) else -1
            for i in range(max_index + 1):
                name = tc_name_acc.get(i) or ""
                raw_args = (tc_args_acc.get(i) or {}).get("_raw", "")
                tool_calls.append({"name": name, "arguments": raw_args})

            # Execute each tool sequentially and append results to the message list
            for call in tool_calls:
                tool_name = call.get("name") or ""
                raw = call.get("arguments") or "{}"
                try:
                    args = json.loads(raw)
                except Exception:
                    args = {"_raw": raw}

                req_id = str(uuid.uuid4())
                metadata = {
                    **dict(base_metadata or {}),
                    "tenant": (base_metadata or {}).get("tenant", "default"),
                    "request_id": req_id,
                    "source": "tool_orchestrator",
                }
                event = {
                    "event_id": req_id,
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "tool_name": tool_name,
                    "args": args,
                    "metadata": metadata,
                }
                try:
                    await self.publisher.publish(
                        cfg.env("TOOL_REQUESTS_TOPIC", "tool.requests"),
                        event,
                        dedupe_key=req_id,
                        session_id=session_id,
                        tenant=metadata.get("tenant"),
                    )
                except Exception:
                    LOGGER.debug("Failed to publish tool request", exc_info=True)
                    continue

                result_event = await self._wait_for_tool_result(
                    session_id=session_id, request_id=req_id, timeout_seconds=float(cfg.env("TOOL_RESULT_TIMEOUT", "20"))
                )
                # Append a summarised tool result back into the message context
                if result_event:
                    payload = result_event.get("payload")
                    try:
                        tool_text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
                    except Exception:
                        tool_text = str(payload)
                    messages.append(
                        ChatMessage(
                            role="system",
                            content=f"Tool {tool_name} result: {tool_text[:4000]}",
                        )
                    )
                else:
                    messages.append(
                        ChatMessage(
                            role="system",
                            content=f"Tool {tool_name} did not return a result in time.",
                        )
                    )

            # After injecting tool results, ask the model for the final answer (non-stream)
            return await self._generate_response(
                session_id=session_id,
                persona_id=persona_id,
                messages=messages,
                slm_kwargs=slm_kwargs,
                analysis_metadata=analysis_metadata,
                base_metadata=base_metadata,
            )
        else:
            text = "".join(buffer)
            if not text:
                _record_llm_failure(model_label)
                raise RuntimeError("Empty response from streaming Gateway/SLM")
            usage_norm = _normalize_usage(usage)
            _record_llm_success(
                model_label,
                usage_norm["input_tokens"],
                usage_norm["output_tokens"],
                time.perf_counter() - start_time,
            )
            return text, usage_norm

    async def _invoke_escalation_response(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
    ) -> tuple[str, dict[str, int], float, str, str | None]:
        # Prepare overrides from profile + provided kwargs
        profile = await self.profile_store.get("escalation", self.deployment_mode)
        overrides: Dict[str, Any] = {}
        if profile:
            # Only include base_url when non-empty to avoid sending an empty string
            overrides.update({
                "model": profile.model,
                "temperature": profile.temperature,
            })
            if isinstance(profile.base_url, str) and profile.base_url.strip():
                overrides["base_url"] = profile.base_url
            if isinstance(profile.kwargs, dict):
                overrides["kwargs"] = profile.kwargs
        # Allow explicit slm_kwargs to override profile
        for k in ("model", "base_url", "temperature", "kwargs", "metadata"):
            if k in slm_kwargs and slm_kwargs[k] is not None:
                if k == "metadata" and overrides.get("kwargs") is None:
                    overrides["kwargs"] = slm_kwargs[k]
                elif k != "metadata":
                    overrides[k] = slm_kwargs[k]

        url = f"{self._gateway_base}/v1/llm/invoke"
        body = {
            "role": "escalation",
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": None,
            "messages": [m.__dict__ for m in messages],
            "overrides": overrides,
        }
        headers = {"X-Internal-Token": self._internal_token or ""}
        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.is_error:
                raise RuntimeError(f"Gateway escalation invoke error {resp.status_code}: {resp.text[:512]}")
            data = resp.json()
        latency = time.time() - start_time
        text = data.get("content", "")
        usage = data.get("usage", {"input_tokens": 0, "output_tokens": 0})
        model_used = data.get("model") or overrides.get("model") or cfg.env("SLM_MODEL", "unknown")
        base_url_used = data.get("base_url") or overrides.get("base_url")
        if not text:
            raise RuntimeError("Empty response from escalation LLM via Gateway")
        return text, usage, latency, model_used, base_url_used

    async def start(self) -> None:
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
        await self.store.append_event(
            "system",
            {
                "type": "worker_start",
                "event_id": str(uuid.uuid4()),
                "message": "Conversation worker online",
            },
        )
        
        LOGGER.info(
            "Starting consumer",
            extra={
                "topic": self.settings["inbound"],
                "group": self.settings["group"],
                "bootstrap": self.kafka_settings.bootstrap_servers,
            },
        )
        await self.bus.consume(
            self.settings["inbound"],
            self.settings["group"],
            self._handle_event,
        )

    async def _handle_event(self, event: dict[str, Any]) -> None:
        start_time = time.perf_counter()
        path = "unknown"
        result_label = "success"

        def record_metrics(result: str, path_label: str | None = None) -> None:
            label = path_label or path
            duration = time.perf_counter() - start_time
            MESSAGE_PROCESSING_COUNTER.labels(result).inc()
            MESSAGE_LATENCY.labels(label).observe(duration)

        session_id = event.get("session_id")
        try:
            validate_schema(event, "conversation_event")
        except Exception as exc:
            LOGGER.error("conversation_event schema invalid", extra={"error": str(exc)})
            return
        
        # Extract tenant at the top level to ensure it's available throughout _handle_event
        try:
            tenant = (event.get("metadata") or {}).get("tenant", "default")
        except Exception:
            tenant = "default"

        async def _process() -> None:
            nonlocal path, result_label, tenant

            if not session_id:
                LOGGER.warning("Received event without session_id", extra={"event": event})
                record_metrics("missing_session")
                return

            try:
                validate_event(event, "conversation_event")
            except ValidationError as exc:
                LOGGER.error(
                    "Invalid conversation event",
                    extra={"error": exc.message, "event": event},
                )
                record_metrics("validation_error")
                return

            # Emit a short, single-line log entry as early as possible when an inbound
            # conversation event is processed. This helps correlate gateway POSTs
            # with worker activity during debugging and Playwright runs.
            try:
                event_id = event.get("event_id") or str(uuid.uuid4())
                preview = (event.get("message") or "")[:200]
            except Exception:
                # Defensive fallback - never fail message processing due to logging
                event_id = event.get("event_id") if isinstance(event, dict) else ""
                preview = ""

            LOGGER.info(
                "Received inbound event",
                extra={
                    "event_id": event_id,
                    "session_id": session_id,
                    "tenant": tenant,
                    "preview": preview,
                },
            )

            LOGGER.info("Processing message", extra={"session_id": session_id})

            raw_message = event.get("message", "")
            if isinstance(raw_message, str) and raw_message:
                try:
                    tokens_received_total.inc(count_tokens(raw_message))
                except Exception:
                    LOGGER.debug("Token counting failed for inbound message", exc_info=True)
            analysis = self.preprocessor.analyze(raw_message if isinstance(raw_message, str) else str(raw_message))
            analysis_dict = analysis.to_dict()
            enriched_metadata = dict(event.get("metadata", {}))
            enriched_metadata["analysis"] = analysis_dict
            event["metadata"] = enriched_metadata
            session_metadata = dict(enriched_metadata)

            tenant = enriched_metadata.get("tenant", "default")
            persona_id = event.get("persona_id")

            # Always enforce conversation policy (fail-closed)
            with thinking_policy_seconds.labels(policy="conversation").time():
                allowed = await self.policy_enforcer.check_message_policy(
                    tenant=tenant,
                    persona_id=persona_id,
                    message=event.get("message", ""),
                    metadata=enriched_metadata,
                )
            if not allowed:
                policy_record = {
                    "type": "policy_denied",
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "message": event.get("message", ""),
                    "metadata": {
                        "source": "policy",
                        "analysis": analysis_dict,
                        "policy": {
                            "action": "conversation.send",
                            "status": "denied",
                        },
                    },
                }
                await self.store.append_event(session_id, policy_record)

                denial_response = {
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "role": "assistant",
                    "message": "Message blocked by policy. Please contact your administrator if you believe this is an error.",
                    "metadata": {
                        "source": "policy",
                        "analysis": analysis_dict,
                        "policy": {
                            "action": "conversation.send",
                            "status": "denied",
                        },
                    },
                }
                validate_event(denial_response, "conversation_event")
                await self.publisher.publish(
                    self.settings["outbound"],
                    denial_response,
                    dedupe_key=denial_response.get("event_id"),
                    session_id=session_id,
                    tenant=(denial_response.get("metadata") or {}).get("tenant"),
                )
                record_metrics("policy_denied", "policy")
                return

            try:
                await self.store.append_event(session_id, {"type": "user", **event})
            except asyncpg.exceptions.UniqueViolationError:
                LOGGER.debug(
                    "Session event already persisted; skipping duplicate append",
                    extra={"session_id": session_id, "event_id": event.get("event_id")},
                )
            # Save user message to SomaBrain as a memory (non-blocking semantics with error shielding)
            try:
                payload = {
                    "id": event.get("event_id"),
                    "type": "conversation_event",
                    "role": "user",
                    "content": event.get("message", ""),
                    "attachments": event.get("attachments", []) or [],
                    "session_id": session_id,
                    "persona_id": event.get("persona_id"),
                    "metadata": {
                        **dict(enriched_metadata),
                        "agent_profile_id": enriched_metadata.get("agent_profile_id"),
                        "universe_id": enriched_metadata.get("universe_id") or cfg.env("SOMA_NAMESPACE"),
                    },
                }
                payload["idempotency_key"] = generate_for_memory_payload(payload)
                allow_memory = False
                try:
                    with thinking_policy_seconds.labels(policy="memory.write").time():
                        allow_memory = await self.policy_client.evaluate(
                            PolicyRequest(
                                tenant=tenant,
                                persona_id=event.get("persona_id"),
                                action="memory.write",
                                resource="somabrain",
                                context={
                                    "payload_type": payload.get("type"),
                                    "role": payload.get("role"),
                                    "session_id": session_id,
                                    "metadata": payload.get("metadata", {}),
                                },
                            )
                        )
                except Exception:
                    LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy", exc_info=True)

                if allow_memory:
                    wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
                    try:
                        result = await self.soma.remember(payload)
                    except Exception:
                        self._enter_somabrain_degraded("remember_failure")
                        try:
                            await self.mem_outbox.enqueue(
                                payload=payload,
                                tenant=tenant,
                                session_id=session_id,
                                persona_id=event.get("persona_id"),
                                idempotency_key=payload.get("idempotency_key"),
                                dedupe_key=str(payload.get("id")),
                            )
                        except Exception:
                            LOGGER.debug("Failed to enqueue memory write for retry (user)", exc_info=True)
                        result = None
                        allow_memory = False
                    if allow_memory:
                        try:
                            wal_event = {
                                "type": "memory.write",
                                "role": "user",
                                "session_id": session_id,
                                "persona_id": event.get("persona_id"),
                                "tenant": tenant,
                                "payload": payload,
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
                                dedupe_key=str(payload.get("id")),
                                session_id=session_id,
                                tenant=tenant,
                            )
                        except Exception:
                            LOGGER.debug("Failed to publish memory WAL (user)", exc_info=True)

                    try:
                        attach_list = event.get("attachments") or []
                        for a in attach_list:
                            if not isinstance(a, str) or not a.strip():
                                continue
                            raw = a.strip()
                            att_id = self._attachment_id_from_str(raw)
                            if att_id:
                                size_info = await self._attachment_head(att_id, tenant)
                                offload = self._should_offload_ingest_id(
                                    size_info.get("size") if isinstance(size_info, dict) else None
                                )
                                if offload:
                                    try:
                                        tool_event = {
                                            "event_id": str(uuid.uuid4()),
                                            "session_id": session_id,
                                            "persona_id": event.get("persona_id"),
                                            "tool_name": "document_ingest",
                                            "args": {
                                                "attachment_id": att_id,
                                                "session_id": session_id,
                                                "persona_id": event.get("persona_id"),
                                                "metadata": {**dict(enriched_metadata or {}), "source": "ingest"},
                                            },
                                            "metadata": {"tenant": tenant, **dict(enriched_metadata or {})},
                                        }
                                        topic = cfg.env("TOOL_REQUESTS_TOPIC", "tool.requests")
                                        await self.publisher.publish(
                                            topic,
                                            tool_event,
                                            dedupe_key=tool_event.get("event_id"),
                                            session_id=session_id,
                                            tenant=tenant,
                                        )
                                    except Exception:
                                        LOGGER.debug("Failed to enqueue document_ingest tool", exc_info=True)
                                else:
                                    asyncio.create_task(
                                        self._ingest_attachment_by_id(
                                            att_id=att_id,
                                            session_id=session_id,
                                            persona_id=event.get("persona_id"),
                                            tenant=tenant,
                                            metadata=enriched_metadata,
                                        )
                                    )
                            else:
                                if self.deployment_mode != "DEV":
                                    LOGGER.warning(
                                        "Path-based attachment ingest blocked in non-DEV mode",
                                        extra={"session_id": session_id},
                                    )
                                    continue
                                fullpath = raw
                                if self._should_offload_ingest(fullpath):
                                    try:
                                        tool_event = {
                                            "event_id": str(uuid.uuid4()),
                                            "session_id": session_id,
                                            "persona_id": event.get("persona_id"),
                                            "tool_name": "document_ingest",
                                            "args": {
                                                "path": fullpath,
                                                "session_id": session_id,
                                                "persona_id": event.get("persona_id"),
                                                "metadata": {**dict(enriched_metadata or {}), "source": "ingest"},
                                            },
                                            "metadata": {"tenant": tenant, **dict(enriched_metadata or {})},
                                        }
                                        topic = cfg.env("TOOL_REQUESTS_TOPIC", "tool.requests")
                                        await self.publisher.publish(
                                            topic,
                                            tool_event,
                                            dedupe_key=tool_event.get("event_id"),
                                            session_id=session_id,
                                            tenant=tenant,
                                        )
                                    except Exception:
                                        LOGGER.debug("Failed to enqueue document_ingest tool", exc_info=True)
                                else:
                                    asyncio.create_task(
                                        self._ingest_attachment(
                                            path=fullpath,
                                            session_id=session_id,
                                            persona_id=event.get("persona_id"),
                                            tenant=tenant,
                                            metadata=enriched_metadata,
                                        )
                                    )
                    except Exception:
                        LOGGER.debug("Scheduling attachment ingest failed", exc_info=True)
                else:
                    LOGGER.info(
                        "memory.write denied by policy",
                        extra={"session_id": session_id, "event_id": payload.get("id")},
                    )
            except SomaClientError as exc:
                LOGGER.warning(
                    "SomaBrain remember failed for user message",
                    extra={"session_id": session_id, "error": str(exc)},
                )
                try:
                    await self.mem_outbox.enqueue(
                        payload=payload,
                        tenant=tenant,
                        session_id=session_id,
                        persona_id=event.get("persona_id"),
                        idempotency_key=payload.get("idempotency_key"),
                        dedupe_key=str(payload.get("id")) if payload.get("id") else None,
                    )
                except Exception:
                    LOGGER.debug("Failed to enqueue memory write for retry (user)", exc_info=True)
            except Exception:
                LOGGER.debug("SomaBrain remember (user) unexpected error", exc_info=True)

            cache_metadata = dict(event.get("metadata", {}))
            try:
                await self.cache.write_context(session_id, event.get("persona_id"), cache_metadata)
            except Exception:
                SESSION_CACHE_SYNC.labels("error").inc()
                LOGGER.warning(
                    "Failed to synchronise session cache",
                    extra={"session_id": session_id},
                    exc_info=True,
                )
            else:
                SESSION_CACHE_SYNC.labels("success").inc()

        history = await self.store.list_events(session_id, limit=20)
        history_messages = self._history_events_to_messages(history)
        
        # Get analysis data from metadata or provide defaults to prevent NameError
        analysis_dict = event.get("metadata", {}).get("analysis", {
            "intent": "general",
            "sentiment": "neutral", 
            "tags": []
        })
        
        priors = await self._fetch_planner_priors(
            tenant_id=event.get("tenant") or session_metadata.get("tenant"),
            persona_id=persona_id,
            session_id=session_id,
            analysis=analysis_dict,
        )
        if priors:
            event.setdefault("metadata", {})["planner_priors"] = priors
        
        summary_tags = ", ".join(analysis_dict["tags"]) if analysis_dict.get("tags") else "none"
        analysis_prompt = ChatMessage(
            role="system",
            content=(
                "The following classification is for internal guidance only. Do not repeat or mention it in your reply. "
                "Use it silently to tailor your response. Classification: intent={intent}; sentiment={sentiment}; tags={tags}."
            ).format(
                intent=analysis_dict.get("intent", "general"),
                sentiment=analysis_dict.get("sentiment", "neutral"),
                tags=summary_tags,
            ),
        )
        priors_prompt: list[ChatMessage] = []
        if priors:
            formatted = "; ".join(
                f"{p.get('name','?')}: {p.get('description','')}" for p in priors[:3]
            )
            priors_prompt.append(
                ChatMessage(
                    role="system",
                    name="planner_priors",
                    content=f"Recent successful tasks/tools for similar intent: {formatted}. Prefer these when deciding actions.",
                )
            )

        try:
            # Initialize session_metadata for context builder path
            session_metadata = {}
            turn_envelope = {
                "tenant_id": tenant,
                "session_id": session_id,
                "system_prompt": analysis_prompt.content,
                "user_message": event.get("message", ""),
                "history": history_messages,
            }
            max_tokens = self._context_builder_max_tokens()
            built_context = await self.context_builder.build_for_turn(turn_envelope, max_prompt_tokens=max_tokens)
            messages = [ChatMessage(role=msg.get("role", "user"), content=str(msg.get("content", ""))) for msg in built_context.messages]
            if priors_prompt:
                messages = priors_prompt + messages
            session_metadata["somabrain_state"] = (
                built_context.debug.get("somabrain_state")
                or self._somabrain_health_state().value
            )
            session_metadata["somabrain_reason"] = (
                built_context.debug.get("somabrain_reason")
                or self._last_degraded_reason
                or session_metadata["somabrain_state"]
            )
        except Exception:
            LOGGER.exception("Context builder failed; falling back to legacy prompt assembly")
            self._enter_somabrain_degraded("context_builder_failure")
            messages = self._legacy_prompt_messages(history, event, analysis_prompt)
            if priors_prompt:
                messages = priors_prompt + messages
            # Initialize session_metadata if not already defined
            if 'session_metadata' not in locals():
                session_metadata = {}
            session_metadata.setdefault("somabrain_state", self._somabrain_health_state().value)
            session_metadata.setdefault(
                "somabrain_reason",
                self._last_degraded_reason or session_metadata["somabrain_state"],
            )

            model_profile = await self.profile_store.get("dialogue", self.deployment_mode)
            slm_kwargs: dict[str, Any] = {}
            if model_profile:
                slm_kwargs.update(
                    {
                        "model": model_profile.model,
                        "base_url": model_profile.base_url,
                        "temperature": model_profile.temperature,
                    }
                )
                # Be defensive: only merge kwargs when it's a dict
                if isinstance(model_profile.kwargs, dict) and model_profile.kwargs:
                    slm_kwargs.update(model_profile.kwargs)
                elif model_profile.kwargs is not None and not isinstance(model_profile.kwargs, dict):
                    try:
                        LOGGER.warning(
                            "Ignoring non-dict model_profile.kwargs",
                            extra={"type": str(type(model_profile.kwargs))},
                        )
                    except Exception:
                        pass
            routing_allow, routing_deny = self.tenant_config.get_routing_policy(tenant)

            if model_profile and cfg.env("ROUTER_URL"):
                candidates = (
                    [slm_kwargs.get("model", model_profile.model)]
                    if slm_kwargs
                    else [model_profile.model]
                )
                if routing_allow:
                    candidates = [
                        candidate for candidate in candidates if candidate in routing_allow
                    ]
                if routing_deny:
                    candidates = [
                        candidate for candidate in candidates if candidate not in routing_deny
                    ]
                if candidates:
                    routed = await self.router.route(
                        role="dialogue",
                        deployment_mode=self.deployment_mode,
                        candidates=candidates,
                    )
                    if routed:
                        slm_kwargs["model"] = routed.model
                        slm_kwargs.setdefault("metadata", {})
                        slm_kwargs["metadata"]["router_score"] = routed.score

            metadata_for_decision = dict(enriched_metadata)
            metadata_for_decision.pop("analysis", None)

            decision = EscalationDecision(False, "disabled", {"enabled": False})
            if self.escalation_enabled:
                decision = should_escalate(
                    message=event.get("message", ""),
                    analysis=analysis_dict,
                    event_metadata=metadata_for_decision,
                )

            budget_check = await self.budgets.consume(tenant, persona_id, 0)
            limit = budget_check.limit_tokens
            if limit and budget_check.total_tokens >= limit:
                budget_response = {
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "role": "assistant",
                    "message": "Token budget exceeded for this persona/tenant.",
                    "metadata": {"source": "budget"},
                    "version": "sa01-v1",
                    "type": "assistant.final",
                }
                await self.telemetry.emit_budget(
                    tenant=tenant,
                    persona_id=persona_id,
                    delta_tokens=0,
                    total_tokens=budget_check.total_tokens,
                    limit_tokens=limit,
                    status="limit_reached",
                )
                validate_event(budget_response, "conversation_event")
                await self.store.append_event(
                    session_id,
                    {"type": "assistant", **budget_response},
                )
                await self.publisher.publish(
                    self.settings["outbound"],
                    budget_response,
                    dedupe_key=budget_response.get("event_id"),
                    session_id=session_id,
                    tenant=(budget_response.get("metadata") or {}).get("tenant"),
                )
                record_metrics("budget_limit", "budget")
                return

            # Emit a versioned thinking event before generation so the UI can render planning state
            try:
                thinking_meta = _compose_outbound_metadata(
                    session_metadata,
                    source="worker",
                    status="thinking",
                    analysis=analysis_dict,
                )
                thinking_event = {
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "role": "assistant",
                    "message": "",
                    "metadata": thinking_meta,
                    "version": "sa01-v1",
                    "type": "assistant.thinking",
                }
                validate_event(thinking_event, "conversation_event")
                await self.publisher.publish(
                    self.settings["outbound"],
                    thinking_event,
                    dedupe_key=thinking_event.get("event_id"),
                    session_id=session_id,
                    tenant=(thinking_event.get("metadata") or {}).get("tenant"),
                )
            except Exception:
                LOGGER.debug("Failed to publish assistant.thinking event", exc_info=True)

            # Continue normal processing when budget not exceeded
            response_text = ""
            usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
            latency = 0.0
            model_used = slm_kwargs.get("model") or cfg.env("SLM_MODEL", "unknown")
            path = "slm"
            escalation_metadata: dict[str, Any] | None = None

            if self.escalation_enabled and decision.should_escalate:
                ESCALATION_ATTEMPTS.labels("attempt").inc()
                try:
                    (
                        response_text,
                        usage,
                        latency,
                        model_used,
                        escalation_base_url,
                    ) = await self._invoke_escalation_response(
                        session_id=session_id,
                        persona_id=persona_id,
                        messages=messages,
                        slm_kwargs=slm_kwargs,
                    )
                    path = "escalation"
                    escalation_metadata = {
                        "deployment_mode": self.deployment_mode,
                        "analysis": analysis_dict,
                        "decision": decision.metadata,
                        "base_url": escalation_base_url,
                    }
                    cost_estimate = estimate_escalation_cost(
                        model_used,
                        input_tokens=usage.get("input_tokens", 0),
                        output_tokens=usage.get("output_tokens", 0),
                    )
                    if cost_estimate is not None:
                        escalation_metadata["cost_estimate_usd"] = cost_estimate
                    _record_llm_success(
                        model_used,
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                        latency,
                    )
                    ESCALATION_ATTEMPTS.labels("success").inc()
                except Exception as exc:
                    path = "slm"
                    result_label = "escalation_error"
                    _record_llm_failure(model_used)
                    LOGGER.exception("Escalation LLM invocation failed")
                    error_metadata = {
                        "error": str(exc),
                        "deployment_mode": self.deployment_mode,
                        "analysis": analysis_dict,
                        "decision": decision.metadata,
                    }
                    await self.telemetry.emit_escalation_llm(
                        session_id=session_id,
                        persona_id=persona_id,
                        tenant=tenant,
                        model=model_used,
                        latency_seconds=0.0,
                        input_tokens=0,
                        output_tokens=0,
                        decision_reason=decision.reason,
                        status="error",
                        metadata=error_metadata,
                    )
                    decision = EscalationDecision(
                        False,
                        "fallback_after_error",
                        {**decision.metadata, "error": str(exc)},
                    )
                    ESCALATION_ATTEMPTS.labels("error").inc()

            if path == "slm":
                response_start = time.perf_counter()
                try:
                    response_text, usage = await self._generate_with_tools(
                        session_id=session_id,
                        persona_id=persona_id,
                        messages=messages,
                        slm_kwargs=slm_kwargs,
                        analysis_metadata=analysis_dict,
                        base_metadata=session_metadata,
                    )
                    _record_llm_success(
                        model_used,
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                        time.perf_counter() - response_start,
                    )
                except Exception as exc:
                    _record_llm_failure(model_used)
                    LOGGER.exception("SLM request failed")
                    # Attempt a non-streaming fallback via Gateway once more before giving up
                    result_label = "generation_error"
                    await self.store.append_event(
                        session_id,
                        {
                            "type": "error",
                            "event_id": str(uuid.uuid4()),
                            "details": str(exc),
                        },
                    )
                    try:
                        url_ns = f"{self._gateway_base}/v1/llm/invoke"
                        ov2: dict[str, Any] = {}
                        for k, v in {
                            "model": slm_kwargs.get("model"),
                            "base_url": slm_kwargs.get("base_url"),
                            "temperature": slm_kwargs.get("temperature"),
                            "kwargs": slm_kwargs.get("metadata") or slm_kwargs.get("kwargs"),
                        }.items():
                            if v is None:
                                continue
                            if isinstance(v, str) and v.strip() == "":
                                continue
                            ov2[k] = v
                        body_ns = {
                            "role": "dialogue",
                            "session_id": session_id,
                            "persona_id": persona_id,
                            "tenant": (session_metadata or {}).get("tenant"),
                            "messages": [m.__dict__ for m in messages],
                            "overrides": ov2,
                        }
                        headers_ns = {"X-Internal-Token": self._internal_token or ""}
                        async with httpx.AsyncClient(timeout=20.0) as client:
                            resp_ns = await client.post(url_ns, json=body_ns, headers=headers_ns)
                            if not resp_ns.is_error:
                                data_ns = resp_ns.json()
                                fallback_text = data_ns.get("content", "")
                                usage = data_ns.get("usage", {"input_tokens": 0, "output_tokens": 0})
                                if fallback_text:
                                    response_text = fallback_text
                                else:
                                    response_text = "I encountered an error while generating a reply."
                                _record_llm_success(
                                    data_ns.get("model") or model_used,
                                    usage.get("input_tokens", 0),
                                    usage.get("output_tokens", 0),
                                    time.perf_counter() - response_start,
                                )
                            else:
                                response_text = "I encountered an error while generating a reply."
                    except Exception:
                        response_text = "I encountered an error while generating a reply."
                latency = time.time() - response_start
                model_used = slm_kwargs.get("model") or cfg.env("SLM_MODEL", "unknown")
                # Note: model_used may be overridden by Gateway's router; usage remains accurate

            total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            budget_result = await self.budgets.consume(tenant, persona_id, total_tokens)
            if not budget_result.allowed:
                response_text = "Token budget exceeded for this persona/tenant."
                result_label = "budget_limit"
                # Progress publishing via SKM removed; emit telemetry and continue
                LOGGER.info(
                    "Budget limit reached",
                    extra={
                        "session_id": session_id,
                        "persona_id": event.get("persona_id"),
                        "tenant": tenant,
                    },
                )

            if path == "escalation":
                await self.telemetry.emit_escalation_llm(
                    session_id=session_id,
                    persona_id=persona_id,
                    tenant=tenant,
                    model=model_used,
                    latency_seconds=latency,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    decision_reason=decision.reason,
                    status="success",
                    metadata=escalation_metadata,
                )
            else:
                slm_metadata = {
                    "deployment_mode": self.deployment_mode,
                    "intent": analysis_dict["intent"],
                    "sentiment": analysis_dict["sentiment"],
                    "tags": analysis_dict["tags"],
                    "escalation_decision": {
                        "should_escalate": decision.should_escalate,
                        "reason": decision.reason,
                        "metadata": decision.metadata,
                    },
                }
                await self.telemetry.emit_slm(
                    session_id=session_id,
                    persona_id=persona_id,
                    tenant=tenant,
                    model=model_used,
                    latency_seconds=latency,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    metadata=slm_metadata,
                )
            await self.telemetry.emit_budget(
                tenant=tenant,
                persona_id=event.get("persona_id"),
                delta_tokens=total_tokens,
                total_tokens=budget_result.total_tokens,
                limit_tokens=budget_result.limit_tokens,
                status="allowed" if budget_result.allowed else "limit_reached",
            )

            response_source = "escalation_llm" if path == "escalation" else "slm"
            escalation_payload = None
            if path == "escalation":
                escalation_payload = {
                    "reason": decision.reason,
                    "metadata": decision.metadata,
                }

            if not response_text.strip():
                response_text = self._degraded_response_text()

            # Refresh somabrain markers right before publishing
            if self._somabrain_health_state() != SomabrainHealthState.NORMAL:
                session_metadata["somabrain_state"] = self._somabrain_health_state().value
                session_metadata["somabrain_reason"] = self._last_degraded_reason or session_metadata["somabrain_state"]

            response_metadata = _compose_outbound_metadata(
                session_metadata,
                source=response_source,
                status="completed",
                analysis=analysis_dict,
                extra={"escalation": escalation_payload} if escalation_payload else None,
            )
            response_event = {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "persona_id": event.get("persona_id"),
                "role": "assistant",
                "message": response_text,
                "metadata": response_metadata,
                "version": "sa01-v1",
                "type": "assistant.final",
            }
            validate_schema(response_event, "assistant_event")
            validate_event(response_event, "conversation_event")

            await self.store.append_event(session_id, {"type": "assistant", **response_event})
            _pub_res = await self.publisher.publish(
                self.settings["outbound"],
                response_event,
                dedupe_key=response_event.get("event_id"),
                session_id=session_id,
                tenant=(response_event.get("metadata") or {}).get("tenant"),
                headers=build_headers(
                    tenant=(response_event.get("metadata") or {}).get("tenant"),
                    session_id=session_id,
                    persona_id=response_event.get("persona_id"),
                    event_type=response_event.get("type"),
                    event_id=response_event.get("event_id"),
                ),
            )
            try:
                LOGGER.info(
                    "Published assistant event",
                    extra={
                        "topic": self.settings["outbound"],
                        "session_id": session_id,
                        "event_id": response_event.get("event_id"),
                        "result": _pub_res,
                    },
                )
            except Exception:
                LOGGER.debug("Failed to log assistant publish", exc_info=True)
            # Save assistant response to SomaBrain as a memory
            try:
                payload = {
                    "id": response_event.get("event_id"),
                    "type": "conversation_event",
                    "role": "assistant",
                    "content": response_text,
                    "attachments": [],
                    "session_id": session_id,
                    "persona_id": event.get("persona_id"),
                    "metadata": {
                        **dict(response_metadata),
                        "agent_profile_id": response_metadata.get("agent_profile_id"),
                        "universe_id": response_metadata.get("universe_id") or cfg.env("SOMA_NAMESPACE"),
                    },
                }
                payload["idempotency_key"] = generate_for_memory_payload(payload)
                allow_memory = False
                try:
                    with thinking_policy_seconds.labels(policy="memory.write").time():
                        allow_memory = await self.policy_client.evaluate(
                            PolicyRequest(
                                tenant=tenant,
                                persona_id=event.get("persona_id"),
                                action="memory.write",
                                resource="somabrain",
                                context={
                                    "payload_type": payload.get("type"),
                                    "role": payload.get("role"),
                                    "session_id": session_id,
                                    "metadata": payload.get("metadata", {}),
                                },
                            )
                        )
                except Exception:
                    LOGGER.warning("OPA memory.write check failed; denying by fail-closed policy", exc_info=True)
                if allow_memory:
                    wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
                    try:
                        result = await self.soma.remember(payload)
                    except Exception:
                        self._enter_somabrain_degraded("remember_failure")
                        try:
                            await self.mem_outbox.enqueue(
                                payload=payload,
                                tenant=tenant,
                                session_id=session_id,
                                persona_id=event.get("persona_id"),
                                idempotency_key=payload.get("idempotency_key"),
                                dedupe_key=str(payload.get("id")),
                            )
                        except Exception:
                            LOGGER.debug("Failed to enqueue memory write for retry (assistant)", exc_info=True)
                        allow_memory = False
                        result = None
                    try:
                        wal_event = {
                            "type": "memory.write",
                            "role": "assistant",
                            "session_id": session_id,
                            "persona_id": event.get("persona_id"),
                            "tenant": tenant,
                            "payload": payload,
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
                            dedupe_key=str(payload.get("id")),
                            session_id=session_id,
                            tenant=tenant,
                        )
                    except Exception:
                        LOGGER.debug("Failed to publish memory WAL (assistant)", exc_info=True)
                else:
                    LOGGER.info(
                        "memory.write denied by policy",
                        extra={"session_id": session_id, "event_id": payload.get("id")},
                    )
            except SomaClientError as exc:
                LOGGER.warning(
                    "SomaBrain remember failed for assistant message",
                    extra={"session_id": session_id, "error": str(exc)},
                )
                try:
                    await self.mem_outbox.enqueue(
                        payload=payload,
                        tenant=tenant,
                        session_id=session_id,
                        persona_id=event.get("persona_id"),
                        idempotency_key=payload.get("idempotency_key"),
                        dedupe_key=str(payload.get("id")) if payload.get("id") else None,
                    )
                except Exception:
                    LOGGER.debug("Failed to enqueue memory write for retry (assistant)", exc_info=True)
            except Exception:
                LOGGER.debug("SomaBrain remember (assistant) unexpected error", exc_info=True)
            record_metrics(result_label, path)
        # Execute the processing pipeline and ensure metrics are recorded on unexpected errors
        try:
            await _process()
        except Exception:
            try:
                # Best-effort metrics in case of an unhandled exception
                MESSAGE_PROCESSING_COUNTER.labels("error").inc()
                MESSAGE_LATENCY.labels(path).observe(time.perf_counter() - start_time)
            except Exception:
                pass
            LOGGER.exception("Unhandled error while processing conversation event")

    # REAL IMPLEMENTATION - Enhanced Learning & Adaptation Features
    async def submit_enhanced_feedback(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        query: str,
        response: str,
        utility_score: float,
        metadata: Dict[str, Any],
        reward: float | None = None,
    ) -> bool:
        """Submit enhanced feedback to SomaBrain with learning context."""
        try:
            # Get current adaptation state to inform feedback
            adaptation_state = await self.soma.adaptation_state(metadata.get("tenant", "default"))
            
            feedback_payload = {
                "session_id": session_id,
                "query": query,
                "prompt": metadata.get("system_prompt", ""),
                "response_text": response,
                "utility": utility_score,
                "reward": reward,
                "tenant_id": metadata.get("tenant", "default"),
                "metadata": {
                    "persona_id": persona_id,
                    "analysis": metadata.get("analysis", {}),
                    "cognitive_params": metadata.get("cognitive_params", {}),
                    "neuromodulators": metadata.get("neuromodulators", {}),
                    "interaction_patterns": metadata.get("interaction_patterns", []),
                    "timestamp": time.time(),
                    "adaptation_state": adaptation_state
                }
            }
            
            result = await self.soma.context_feedback(feedback_payload)
            if result.get("accepted"):
                LOGGER.info(
                    "Enhanced feedback submitted to SomaBrain",
                    extra={
                        "session_id": session_id,
                        "utility": utility_score,
                        "adaptation_weights": len(adaptation_state.get("weights", {})) if adaptation_state else 0
                    }
                )
                return True
            else:
                LOGGER.warning("Enhanced feedback rejected by SomaBrain")
                return False
        except SomaClientError as e:
            LOGGER.error(f"Failed to submit enhanced feedback: {e}")
            return False

    async def get_adaptive_persona_config(self, persona_id: str, tenant: str = "default") -> Dict[str, Any]:
        """Get adaptive persona configuration based on learning state."""
        try:
            # Get base persona
            persona = await self.soma.get_persona(persona_id)
            if not persona:
                return {}
            
            # Get adaptation state
            adaptation_state = await self.soma.adaptation_state(tenant)
            
            # Apply learned adaptations to persona
            adaptive_config = dict(persona)
            
            if adaptation_state:
                weights = adaptation_state.get("weights", {})
                
                # Adjust behavior based on learning weights
                if weights.get("creativity_boost", 0) > 0.7:
                    adaptive_config["properties"]["creativity_level"] = "high"
                elif weights.get("creativity_boost", 0) < 0.3:
                    adaptive_config["properties"]["creativity_level"] = "low"
                
                if weights.get("empathy_boost", 0) > 0.7:
                    adaptive_config["properties"]["empathy_level"] = "high"
                elif weights.get("empathy_boost", 0) < 0.3:
                    adaptive_config["properties"]["empathy_level"] = "low"
                
                if weights.get("focus_factor", 0.5) > 0.7:
                    adaptive_config["properties"]["focus_level"] = "high"
                elif weights.get("focus_factor", 0.5) < 0.3:
                    adaptive_config["properties"]["focus_level"] = "low"
            
            return adaptive_config
            
        except SomaClientError as e:
            LOGGER.error(f"Failed to get adaptive persona config: {e}")
            return {}

    async def track_semantic_tool_usage(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
        success: bool,
        tenant: str = "default",
    ) -> bool:
        """Track tool usage in semantic graph with learning context."""
        try:
            # Create tool execution memory
            tool_memory = {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": str(result)[:500],  # Truncate for storage
                "success": success,
                "session_id": session_id,
                "persona_id": persona_id,
                "tenant": tenant,
                "timestamp": time.time()
            }
            
            # Store in SomaBrain
            try:
                memory_result = await self.soma.remember(tool_memory)
            except Exception:
                self._enter_somabrain_degraded("remember_failure")
                return False
            coordinate = memory_result.get("coordinate")
            
            if coordinate:
                # Create semantic links for tool usage patterns
                tool_entity = f"tool_{tool_name}_{session_id}"
                session_entity = f"session_{session_id}"
                
                # Link tool to session
                link_payload = {
                    "from_key": session_entity,
                    "to_key": coordinate,
                    "type": "used_tool",
                    "weight": 1.0 if success else 0.1,
                    "universe": tenant,
                    "metadata": {
                        "tool_name": tool_name,
                        "success": success,
                        "timestamp": time.time()
                    }
                }
                await self.soma.link(link_payload)
                
                # Link similar tools based on success patterns
                if success:
                    await self._link_similar_successful_tools(tool_name, coordinate, tenant)
                
                LOGGER.info(
                    "Tracked semantic tool usage",
                    extra={
                        "session_id": session_id,
                        "tool_name": tool_name,
                        "success": success,
                        "coordinate": coordinate[:3] + "..."
                    }
                )
                return True
            return False
            
        except SomaClientError as e:
            LOGGER.error(f"Failed to track semantic tool usage: {e}")
            return False

    async def _link_similar_successful_tools(
        self,
        tool_name: str,
        current_coordinate: str,
        tenant: str,
    ) -> None:
        """Link current tool to similar successful tools for learning transfer."""
        try:
            # Find similar tools based on name patterns or categories
            similar_tools = await self._find_similar_tools(tool_name)
            
            for similar_tool in similar_tools:
                # Create link for learning transfer
                link_payload = {
                    "from_key": current_coordinate,
                    "to_key": f"tool_pattern_{similar_tool}",
                    "type": "similar_success_pattern",
                    "weight": 0.8,
                    "universe": tenant,
                    "metadata": {
                        "original_tool": tool_name,
                        "similar_tool": similar_tool,
                        "transfer_type": "success_pattern"
                    }
                }
                await self.soma.link(link_payload)
                
        except Exception as e:
            LOGGER.debug(f"Failed to link similar tools: {e}")

    async def _find_similar_tools(self, tool_name: str) -> List[str]:
        """Find tools similar to the given tool name."""
        similar_tools = []
        
        # Simple pattern matching for tool similarity
        tool_categories = {
            "search": ["find", "search", "lookup", "query"],
            "create": ["make", "create", "build", "generate"],
            "modify": ["update", "change", "edit", "modify"],
            "analyze": ["examine", "analyze", "inspect", "review"],
            "communicate": ["send", "notify", "message", "communicate"]
        }
        
        tool_lower = tool_name.lower()
        for category, patterns in tool_categories.items():
            if any(pattern in tool_lower for pattern in patterns):
                similar_tools.extend(patterns)
                break
                
        return similar_tools

    async def get_learning_insights(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        tenant: str = "default",
    ) -> Dict[str, Any]:
        """Get learning insights and adaptation recommendations."""
        try:
            # Get adaptation state
            adaptation_state = await self.soma.adaptation_state(tenant)
            
            # Get semantic graph insights
            insights = {
                "adaptation_state": adaptation_state,
                "learning_recommendations": [],
                "performance_metrics": {},
                "behavioral_patterns": {}
            }
            
            if adaptation_state:
                weights = adaptation_state.get("weights", {})
                
                # Generate learning recommendations
                if weights.get("creativity_boost", 0) < 0.3:
                    insights["learning_recommendations"].append({
                        "type": "creativity_enhancement",
                        "priority": "medium",
                        "suggestion": "Introduce more diverse problem-solving approaches"
                    })
                
                if weights.get("empathy_boost", 0) < 0.3:
                    insights["learning_recommendations"].append({
                        "type": "empathy_development",
                        "priority": "medium",
                        "suggestion": "Focus on understanding user perspectives more deeply"
                    })
                
                if weights.get("focus_factor", 0.5) < 0.3:
                    insights["learning_recommendations"].append({
                        "type": "focus_improvement",
                        "priority": "high",
                        "suggestion": "Reduce distractions and improve task concentration"
                    })
                
                # Calculate performance metrics
                insights["performance_metrics"] = {
                    "adaptation_rate": len([w for w in weights.values() if w > 0.7]) / max(1, len(weights)),
                    "learning_velocity": weights.get("learning_velocity", 0.5),
                    "stability_score": weights.get("stability", 0.5)
                }
            
            return insights
            
        except SomaClientError as e:
            LOGGER.error(f"Failed to get learning insights: {e}")
            return {}




async def main() -> None:
    worker = ConversationWorker()
    try:
        await worker.start()
    finally:
        await worker.soma.close()
        await worker.router.close()
        await worker.policy_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
