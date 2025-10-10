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

from services.common.budget_manager import BudgetManager
from services.common.dlq import DeadLetterQueue
from services.common.escalation import decide_escalation, EscalationDecision
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.model_costs import estimate_escalation_cost
from services.common.model_profiles import ModelProfileStore
from services.common.policy_client import PolicyClient
from services.common.router_client import RouterClient
from services.common.schema_validator import validate_event
from services.common.session_repository import ensure_schema, PostgresSessionStore, RedisSessionCache
from services.common.skm_client import ProgressPayload, SKMClient
from services.common.slm_client import ChatMessage, SLMClient
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore
from services.common.tenant_config import TenantConfig
from services.common.tracing import setup_tracing
from services.conversation_worker.policy_integration import ConversationPolicyEnforcer

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
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", APP_SETTINGS.kafka_bootstrap_servers)
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
        redis_url = os.getenv("REDIS_URL", APP_SETTINGS.redis_url)
        self.dlq = DeadLetterQueue(self.settings["inbound"], bus=self.bus)
        self.cache = RedisSessionCache(url=redis_url)
        self.store = PostgresSessionStore(dsn=APP_SETTINGS.postgres_dsn)
        self.slm = SLMClient()
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
        self.telemetry = TelemetryPublisher(bus=self.bus, store=telemetry_store)
        self.skm = SKMClient()
        router_url = os.getenv("ROUTER_URL") or APP_SETTINGS.extra.get("router_url")
        self.router = RouterClient(base_url=router_url)
        self.deployment_mode = os.getenv("SOMA_AGENT_MODE", APP_SETTINGS.deployment_mode).upper()
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
                await self.bus.publish(self.settings["outbound"], streaming_event)
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
        await self.profile_store.ensure_schema()
        await self.store.append_event(
            "system",
            {
                "type": "worker_start",
                "event_id": str(uuid.uuid4()),
                "message": "Conversation worker online",
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
                await self.bus.publish(self.settings["outbound"], denial_response)
                record_metrics("policy_denied", "policy")
                return

            await self.store.append_event(session_id, {"type": "user", **event})

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
                if model_profile.kwargs:
                    slm_kwargs.update(model_profile.kwargs)
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
                decision = decide_escalation(
                    message=event.get("message", ""),
                    analysis=analysis_dict,
                    event_metadata=metadata_for_decision,
                    fallback_enabled=self.escalation_fallback_enabled,
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
                await self.bus.publish(self.settings["outbound"], budget_response)
                record_metrics("budget_limit", "budget")
                return

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
                await self.skm.publish_progress(
                    ProgressPayload(
                        session_id=session_id,
                        persona_id=event.get("persona_id"),
                        status="budget_limit",
                        detail="Token budget exceeded",
                        metadata={"tenant": tenant},
                    )
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
            await self.bus.publish(self.settings["outbound"], response_event)
            record_metrics(result_label, path)

        try:
            with tracer.start_as_current_span(
                "conversation_worker.process_event",
                attributes={
                    "soma.session_id": session_id or "",
                    "messaging.destination": self.settings["outbound"],
                },
            ):
                await _process()
        except Exception as exc:
            result_label = "error"
            LOGGER.exception(
                "Unhandled error while processing conversation event",
                extra={
                    "session_id": session_id,
                    "event_id": event.get("event_id"),
                },
            )
            try:
                await self.dlq.send_to_dlq(event, exc)
            except Exception:
                LOGGER.exception(
                    "Failed to forward event to DLQ",
                    extra={
                        "session_id": session_id,
                        "dlq_topic": self.dlq.dlq_topic,
                    },
                )
            record_metrics("error", "exception")


async def main() -> None:
    worker = ConversationWorker()
    try:
        await worker.start()
    finally:
        await worker.slm.close()
        await worker.skm.close()
        await worker.router.close()
        await worker.policy_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
