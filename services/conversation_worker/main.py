"""Conversation worker for SomaAgent 01."""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from jsonschema import ValidationError
from prometheus_client import Counter, Histogram, start_http_server

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
from services.common.idempotency import generate_for_memory_payload
from services.common.router_client import RouterClient
from services.common.schema_validator import validate_event
from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
    RedisSessionCache,
)
from services.common.settings_sa01 import SA01Settings
from services.common.slm_client import ChatMessage, SLMClient
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
import httpx
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer
import mimetypes
from pathlib import Path

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
    metrics_port = int(os.getenv("CONVERSATION_METRICS_PORT", str(APP_SETTINGS.metrics_port)))
    if metrics_port <= 0:
        LOGGER.warning("Metrics server disabled", extra={"port": metrics_port})
        _METRICS_SERVER_STARTED = True
        return
    metrics_host = os.getenv("CONVERSATION_METRICS_HOST", APP_SETTINGS.metrics_host)
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
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", APP_SETTINGS.kafka_bootstrap_servers
        )
        self.kafka_settings = KafkaSettings(
            bootstrap_servers=bootstrap_servers,
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
        )
        self.settings = {
            "inbound": os.getenv("CONVERSATION_INBOUND", "conversation.inbound"),
            "outbound": os.getenv("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": os.getenv("CONVERSATION_GROUP", "conversation-worker"),
        }
        self.bus = KafkaEventBus(self.kafka_settings)
        self.outbox = OutboxStore(dsn=APP_SETTINGS.postgres_dsn)
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        redis_url = os.getenv("REDIS_URL", APP_SETTINGS.redis_url)
        self.dlq = DeadLetterQueue(self.settings["inbound"], bus=self.bus)
        self.cache = RedisSessionCache(url=redis_url)
        self.store = PostgresSessionStore(dsn=APP_SETTINGS.postgres_dsn)
        self.slm = SLMClient()
        # Attempt to fetch provider key from Gateway if not supplied via env
        self._gateway_base = os.getenv("WORKER_GATEWAY_BASE", "http://gateway:8010").rstrip("/")
        self._internal_token = os.getenv("GATEWAY_INTERNAL_TOKEN")
        self.profile_store = ModelProfileStore.from_settings(APP_SETTINGS)
        tenant_config_path = os.getenv(
            "TENANT_CONFIG_PATH",
            APP_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"),
        )
        self.tenant_config = TenantConfig(path=tenant_config_path)
        self.budgets = BudgetManager(url=redis_url, tenant_config=self.tenant_config)
        policy_base = os.getenv("POLICY_BASE_URL", APP_SETTINGS.opa_url)
        self.policy_client = PolicyClient(base_url=policy_base, tenant_config=self.tenant_config)
        self.policy_enforcer = ConversationPolicyEnforcer(self.policy_client)
        telemetry_store = TelemetryStore.from_settings(APP_SETTINGS)
        self.telemetry = TelemetryPublisher(publisher=self.publisher, store=telemetry_store)
        # SomaBrain HTTP client (centralized memory backend)
        self.soma = SomaBrainClient.get()
        self.mem_outbox = MemoryWriteOutbox(dsn=APP_SETTINGS.postgres_dsn)
        router_url = os.getenv("ROUTER_URL") or APP_SETTINGS.extra.get("router_url")
        self.router = RouterClient(base_url=router_url)
        self.deployment_mode = os.getenv("SOMA_AGENT_MODE", APP_SETTINGS.deployment_mode).upper()
        # Enforce secure credential flow: outside DEV do not honor env SLM_API_KEY
        try:
            if self.deployment_mode != "DEV" and getattr(self.slm, "api_key", None):
                self.slm.api_key = None
        except Exception:
            pass
        self.preprocessor = ConversationPreprocessor()
        self.escalation_enabled = os.getenv("ESCALATION_ENABLED", "true").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.escalation_fallback_enabled = os.getenv(
            "ESCALATION_FALLBACK_ENABLED", "false"
        ).lower() in {"1", "true", "yes", "on"}

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
                    "universe_id": (metadata or {}).get("universe_id") or os.getenv("SOMA_NAMESPACE"),
                },
            }
            payload["idempotency_key"] = generate_for_memory_payload(payload)
            allow_memory = True
            try:
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
                LOGGER.debug("OPA memory.write check failed; honoring fail-open defaults", exc_info=True)
            if not allow_memory:
                return
            wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
            try:
                result = await self.soma.remember(payload)
            except Exception:
                # best-effort: enqueue to mem outbox for retry
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
            threshold_mb = float(os.getenv("INGEST_OFFLOAD_THRESHOLD_MB", "5"))
        except ValueError:
            threshold_mb = 5.0
        try:
            size = Path(path).stat().st_size
        except Exception:
            size = 0
        return size > int(threshold_mb * 1024 * 1024)

    async def _stream_response(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
        base_metadata: Dict[str, Any],
    ) -> tuple[str, dict[str, int]]:
        buffer: list[str] = []
        usage = {"input_tokens": 0, "output_tokens": 0}
        async for chunk in self.slm.chat_stream(messages, **slm_kwargs):
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
                }
                await self.publisher.publish(
                    self.settings["outbound"],
                    streaming_event,
                    dedupe_key=streaming_event.get("event_id"),
                    session_id=session_id,
                    tenant=(metadata or {}).get("tenant"),
                )
            finish_reason = choice.get("finish_reason")
            chunk_usage = chunk.get("usage")
            if isinstance(chunk_usage, dict):
                usage["input_tokens"] = int(chunk_usage.get("prompt_tokens", usage["input_tokens"]))
                usage["output_tokens"] = int(
                    chunk_usage.get("completion_tokens", usage["output_tokens"])
                )
            if finish_reason:
                break

        text = "".join(buffer)
        if not text:
            raise RuntimeError("Empty response from streaming SLM")
        return text, usage

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
        # Hydrate API key on-demand if missing (pull from Gateway using internal token)
        if not getattr(self.slm, "api_key", None):
            try:
                await self._ensure_llm_key()
            except Exception:
                LOGGER.debug("On-demand LLM credential fetch failed", exc_info=True)
        try:
            return await self._stream_response(
                session_id=session_id,
                persona_id=persona_id,
                messages=messages,
                slm_kwargs=slm_kwargs,
                analysis_metadata=analysis_metadata,
                base_metadata=base_metadata,
            )
        except Exception as exc:
            LOGGER.warning(
                "Streaming unavailable, falling back to single response",
                extra={"error": str(exc)},
            )
            return await self.slm.chat(messages, **slm_kwargs)

    async def _invoke_escalation_response(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
    ) -> tuple[str, dict[str, int], float, str, str | None]:
        profile = await self.profile_store.get("escalation", self.deployment_mode)
        escalation_kwargs = dict(slm_kwargs)
        base_url = escalation_kwargs.pop("base_url", None)
        model = escalation_kwargs.pop("model", None)
        temperature = escalation_kwargs.pop("temperature", None)

        if profile:
            base_url = profile.base_url
            model = profile.model
            temperature = profile.temperature
            if profile.kwargs:
                escalation_kwargs.update(profile.kwargs)

        start_time = time.time()
        text, usage = await self.slm.chat(
            messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            **escalation_kwargs,
        )
        latency = time.time() - start_time
        if not text:
            raise RuntimeError("Empty response from escalation LLM")
        return text, usage, latency, model or self.slm.default_model, base_url

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
        # Ensure LLM credentials are available before consumption starts (DEV-friendly)
        try:
            await self._ensure_llm_key()
        except Exception:
            LOGGER.debug("LLM credential fetch failed/skipped at startup", exc_info=True)
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

        async def _process() -> None:
            nonlocal path, result_label

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
                tenant = (event.get("metadata") or {}).get("tenant", "default")
                preview = (event.get("message") or "")[:200]
            except Exception:
                # Defensive fallback - never fail message processing due to logging
                event_id = event.get("event_id") if isinstance(event, dict) else ""
                tenant = "default"
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

            analysis = self.preprocessor.analyze(event.get("message", ""))
            analysis_dict = analysis.to_dict()
            enriched_metadata = dict(event.get("metadata", {}))
            enriched_metadata["analysis"] = analysis_dict
            event["metadata"] = enriched_metadata
            session_metadata = dict(enriched_metadata)

            tenant = enriched_metadata.get("tenant", "default")
            persona_id = event.get("persona_id")

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

            await self.store.append_event(session_id, {"type": "user", **event})
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
                        "universe_id": enriched_metadata.get("universe_id") or os.getenv("SOMA_NAMESPACE"),
                    },
                }
                # Idempotency key per contract
                payload["idempotency_key"] = generate_for_memory_payload(payload)
                # Pre-write OPA policy check: memory.write
                allow_memory = True
                try:
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
                    LOGGER.debug("OPA memory.write check failed; honoring fail-open defaults", exc_info=True)
                if allow_memory:
                    wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
                    result = await self.soma.remember(payload)
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
                # Best-effort: ingest attachments in background (parse → remember)
                try:
                    attach_list = event.get("attachments") or []
                    for apath in attach_list:
                        if not isinstance(apath, str) or not apath.strip():
                            continue
                        fullpath = apath.strip()
                        # Offload large/expensive files to tool-executor, otherwise ingest inline
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
                                topic = os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests")
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
            # Ensure SLM API key present (fetch from Gateway when missing)
            await self._ensure_llm_key()
            messages: list[ChatMessage] = []
            for item in reversed(history):
                if item.get("type") == "user":
                    messages.append(ChatMessage(role="user", content=item.get("message", "")))
                elif item.get("type") == "assistant":
                    messages.append(ChatMessage(role="assistant", content=item.get("message", "")))

            if not messages or messages[-1].role != "user":
                messages.append(ChatMessage(role="user", content=event.get("message", "")))

            summary_tags = ", ".join(analysis_dict["tags"]) if analysis_dict["tags"] else "none"
            analysis_prompt = ChatMessage(
                role="system",
                content=(
                    "Conversation analysis: intent={intent}; sentiment={sentiment}; tags={tags}. "
                    "Use this context to tailor the response."
                ).format(
                    intent=analysis_dict["intent"],
                    sentiment=analysis_dict["sentiment"],
                    tags=summary_tags,
                ),
            )
            messages.insert(0, analysis_prompt)

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

            if model_profile and os.getenv("ROUTER_URL"):
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

            # Continue normal processing when budget not exceeded
            response_text = ""
            usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
            latency = 0.0
            model_used = slm_kwargs.get("model", self.slm.default_model)
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
                    ESCALATION_ATTEMPTS.labels("success").inc()
                except Exception as exc:
                    path = "slm"
                    result_label = "escalation_error"
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
                response_start = time.time()
                try:
                    response_text, usage = await self._generate_response(
                        session_id=session_id,
                        persona_id=persona_id,
                        messages=messages,
                        slm_kwargs=slm_kwargs,
                        analysis_metadata=analysis_dict,
                        base_metadata=session_metadata,
                    )
                except Exception as exc:
                    LOGGER.exception("SLM request failed")
                    response_text = "I encountered an error while generating a reply."
                    result_label = "generation_error"
                    await self.store.append_event(
                        session_id,
                        {
                            "type": "error",
                            "event_id": str(uuid.uuid4()),
                            "details": str(exc),
                        },
                    )
                    usage = {"input_tokens": 0, "output_tokens": 0}
                latency = time.time() - response_start
                model_used = slm_kwargs.get("model", self.slm.default_model)

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
            }

            validate_event(response_event, "conversation_event")

            await self.store.append_event(session_id, {"type": "assistant", **response_event})
            _pub_res = await self.publisher.publish(
                self.settings["outbound"],
                response_event,
                dedupe_key=response_event.get("event_id"),
                session_id=session_id,
                tenant=(response_event.get("metadata") or {}).get("tenant"),
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
                        "universe_id": response_metadata.get("universe_id") or os.getenv("SOMA_NAMESPACE"),
                    },
                }
                payload["idempotency_key"] = generate_for_memory_payload(payload)
                allow_memory = True
                try:
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
                    LOGGER.debug("OPA memory.write check failed; honoring fail-open defaults", exc_info=True)
                if allow_memory:
                    wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
                    result = await self.soma.remember(payload)
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

    async def _ensure_llm_key(self) -> None:
        if getattr(self.slm, 'api_key', None):
            return
        # Infer provider from base_url
        host = ''
        try:
            host = (self.slm.base_url or '').split('//',1)[-1].split('/',1)[0]
        except Exception:
            host = ''
        provider = 'openai'
        if 'groq' in host:
            provider = 'groq'
        elif 'openrouter' in host:
            provider = 'openrouter'
        if not self._internal_token:
            LOGGER.warning("No GATEWAY_INTERNAL_TOKEN; cannot fetch LLM credentials from Gateway")
            return
        url = f"{self._gateway_base}/v1/llm/credentials/{provider}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers={"X-Internal-Token": self._internal_token})
                if resp.status_code == 200:
                    body = resp.json()
                    key = body.get('secret')
                    if key:
                        self.slm.api_key = key
                        LOGGER.info("Fetched LLM credentials from Gateway", extra={"provider": provider})
                else:
                    LOGGER.debug("Failed to fetch LLM credentials", extra={"status": resp.status_code})
        except Exception:
            LOGGER.debug("Error fetching LLM credentials", exc_info=True)



async def main() -> None:
    worker = ConversationWorker()
    try:
        await worker.start()
    finally:
        await worker.slm.close()
        await worker.soma.close()
        await worker.router.close()
        await worker.policy_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
