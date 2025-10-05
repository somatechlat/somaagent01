"""Conversation worker for SomaAgent 01."""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any

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
from services.common.skm_client import SKMClient, ProgressPayload
from services.common.router_client import RouterClient
from services.common.tenant_config import TenantConfig

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


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

        LOGGER.info("Processing message", extra={"session_id": session_id})
        await self.store.append_event(session_id, {"type": "user", **event})

        # Build conversation history (last 20 events).
        history = await self.store.list_events(session_id, limit=20)
        messages: list[ChatMessage] = []
        for item in reversed(history):  # stored newest first
            if item.get("type") == "user":
                messages.append(ChatMessage(role="user", content=item.get("message", "")))
            elif item.get("type") == "assistant":
                messages.append(ChatMessage(role="assistant", content=item.get("message", "")))

        if not messages or messages[-1].role != "user":
            messages.append(ChatMessage(role="user", content=event.get("message", "")))

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
            candidates = [slm_kwargs.get("model", model_profile.model)] if slm_kwargs else [model_profile.model]
            if routing_allow:
                candidates = [candidate for candidate in candidates if candidate in routing_allow]
            if routing_deny:
                candidates = [candidate for candidate in candidates if candidate not in routing_deny]
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
            await self.store.append_event(
                session_id,
                {"type": "assistant", **budget_response},
            )
            await self.bus.publish(self.settings["outbound"], budget_response)
            return

        start_time = time.time()
        try:
            response_text, usage = await self.slm.chat(messages, **slm_kwargs)
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
            metadata={"deployment_mode": self.deployment_mode},
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
            "metadata": {"source": "slm"},
        }

        await self.store.append_event(session_id, {"type": "assistant", **response_event})
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
