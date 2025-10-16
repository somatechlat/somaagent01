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

from services.common.event_bus import KafkaEventBus
from services.common.session_repository import (
    PostgresSessionStore,
    RedisSessionCache,
    ensure_schema,
)
from services.common.slm_client import ChatMessage, SLMClient
from services.common.model_profiles import ModelProfileStore
from services.common.budget_manager import BudgetManager
from services.common.telemetry import TelemetryPublisher
from services.common.schema_validator import validate_event
from services.common.skm_client import SKMClient, ProgressPayload
from services.common.router_client import RouterClient
from services.common.tenant_config import TenantConfig

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


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
        elif lower.startswith(
            ("how", "what", "why", "when", "where", "who")
        ) or text.endswith("?"):
            intent = "question"
        elif any(
            keyword in lower for keyword in ["create", "build", "implement", "write"]
        ):
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
        self.settings = {
            "inbound": os.getenv("CONVERSATION_INBOUND", "conversation.inbound"),
            "outbound": os.getenv("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": os.getenv("CONVERSATION_GROUP", "conversation-worker"),
        }
        self.bus = KafkaEventBus()
        self.cache = RedisSessionCache()
        self.store = PostgresSessionStore()
        self.slm = SLMClient()
        self.profile_store = ModelProfileStore()
        self.tenant_config = TenantConfig()
        self.budgets = BudgetManager(tenant_config=self.tenant_config)
        self.telemetry = TelemetryPublisher(self.bus)
        self.skm = SKMClient()
        self.router = RouterClient()
        self.deployment_mode = os.getenv("SOMA_AGENT_MODE", "LOCAL").upper()
        self.preprocessor = ConversationPreprocessor()

    async def _stream_response(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        messages: List[ChatMessage],
        slm_kwargs: Dict[str, Any],
        analysis_metadata: Dict[str, Any],
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
                streaming_event = {
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "persona_id": persona_id,
                    "role": "assistant",
                    "message": "".join(buffer),
                    "metadata": {
                        "source": "slm",
                        "status": "streaming",
                        "analysis": analysis_metadata,
                    },
                }
                await self.bus.publish(self.settings["outbound"], streaming_event)
            finish_reason = choice.get("finish_reason")
            chunk_usage = chunk.get("usage")
            if isinstance(chunk_usage, dict):
                usage["input_tokens"] = int(
                    chunk_usage.get("prompt_tokens", usage["input_tokens"])
                )
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
    ) -> tuple[str, dict[str, int]]:
        try:
            return await self._stream_response(
                session_id=session_id,
                persona_id=persona_id,
                messages=messages,
                slm_kwargs=slm_kwargs,
                analysis_metadata=analysis_metadata,
            )
        except Exception as exc:
            LOGGER.warning(
                "Streaming unavailable, falling back to single response",
                extra={"error": str(exc)},
            )
            return await self.slm.chat(messages, **slm_kwargs)

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
        session_id = event.get("session_id")
        if not session_id:
            LOGGER.warning("Received event without session_id", extra={"event": event})
            return

        try:
            validate_event(event, "conversation_event")
        except ValidationError as exc:
            LOGGER.error(
                "Invalid conversation event",
                extra={"error": exc.message, "event": event},
            )
            return

        LOGGER.info("Processing message", extra={"session_id": session_id})

        analysis = self.preprocessor.analyze(event.get("message", ""))
        analysis_dict = analysis.to_dict()
        enriched_metadata = dict(event.get("metadata", {}))
        enriched_metadata["analysis"] = analysis_dict
        event["metadata"] = enriched_metadata

        await self.store.append_event(session_id, {"type": "user", **event})

        # Build conversation history (last 20 events).
        history = await self.store.list_events(session_id, limit=20)
        messages: list[ChatMessage] = []
        for item in reversed(history):  # stored newest first
            if item.get("type") == "user":
                messages.append(
                    ChatMessage(role="user", content=item.get("message", ""))
                )
            elif item.get("type") == "assistant":
                messages.append(
                    ChatMessage(role="assistant", content=item.get("message", ""))
                )

        if not messages or messages[-1].role != "user":
            messages.append(ChatMessage(role="user", content=event.get("message", "")))

        summary_tags = (
            ", ".join(analysis_dict["tags"]) if analysis_dict["tags"] else "none"
        )
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

        tenant = event.get("metadata", {}).get("tenant", "default")

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
                    candidate
                    for candidate in candidates
                    if candidate not in routing_deny
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

        persona_id = event.get("persona_id")
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
            return

        start_time = time.time()
        try:
            response_text, usage = await self._generate_response(
                session_id=session_id,
                persona_id=persona_id,
                messages=messages,
                slm_kwargs=slm_kwargs,
                analysis_metadata=analysis_dict,
            )
        except Exception as exc:
            LOGGER.exception("SLM request failed")
            response_text = "I encountered an error while generating a reply."
            await self.store.append_event(
                session_id,
                {
                    "type": "error",
                    "event_id": str(uuid.uuid4()),
                    "details": str(exc),
                },
            )
            usage = {"input_tokens": 0, "output_tokens": 0}

        latency = time.time() - start_time
        total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        budget_result = await self.budgets.consume(tenant, persona_id, total_tokens)
        if not budget_result.allowed:
            response_text = "Token budget exceeded for this persona/tenant."
            await self.skm.publish_progress(
                ProgressPayload(
                    session_id=session_id,
                    persona_id=event.get("persona_id"),
                    status="budget_limit",
                    detail="Token budget exceeded",
                    metadata={"tenant": tenant},
                )
            )

        await self.telemetry.emit_slm(
            session_id=session_id,
            persona_id=persona_id,
            tenant=tenant,
            model=slm_kwargs.get("model", self.slm.default_model),
            latency_seconds=latency,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            metadata={
                "deployment_mode": self.deployment_mode,
                "intent": analysis_dict["intent"],
                "sentiment": analysis_dict["sentiment"],
                "tags": analysis_dict["tags"],
            },
        )
        await self.telemetry.emit_budget(
            tenant=tenant,
            persona_id=event.get("persona_id"),
            delta_tokens=total_tokens,
            total_tokens=budget_result.total_tokens,
            limit_tokens=budget_result.limit_tokens,
            status="allowed" if budget_result.allowed else "limit_reached",
        )

        response_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": event.get("persona_id"),
            "role": "assistant",
            "message": response_text,
            "metadata": {"source": "slm", "analysis": analysis_dict},
        }

        validate_event(response_event, "conversation_event")

        await self.store.append_event(
            session_id, {"type": "assistant", **response_event}
        )
        await self.bus.publish(self.settings["outbound"], response_event)


async def main() -> None:
    worker = ConversationWorker()
    try:
        await worker.start()
    finally:
        await worker.slm.close()
        await worker.skm.close()
        await worker.router.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
