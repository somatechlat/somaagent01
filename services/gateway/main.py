"""FastAPI gateway for SomaAgent 01.

This service exposes the public HTTP/WebSocket surface. It validates
requests, enqueues events to Kafka, and streams outbound responses back
to clients. Real deployments should run this behind Kong/Envoy with mTLS.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Annotated, AsyncIterator

import httpx
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.common.event_bus import KafkaEventBus, KafkaSettings, iterate_topic
from services.common.session_repository import PostgresSessionStore, RedisSessionCache

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_event_bus() -> KafkaEventBus:
    return KafkaEventBus()


def get_session_cache() -> RedisSessionCache:
    return RedisSessionCache()


def get_session_store() -> PostgresSessionStore:
    return PostgresSessionStore()


class MessagePayload(BaseModel):
    session_id: str | None = Field(default=None, description="Conversation context identifier")
    persona_id: str | None = Field(default=None, description="Persona guiding this session")
    message: str = Field(..., description="User message")
    attachments: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class QuickActionPayload(BaseModel):
    session_id: str | None = None
    persona_id: str | None = None
    action: str
    metadata: dict[str, str] = Field(default_factory=dict)


QUICK_ACTIONS: dict[str, str] = {
    "summarize": "Summarize the recent conversation for the operator.",
    "next_steps": "Suggest the next three actionable steps.",
    "status_report": "Provide a short status report of current progress.",
}

@app.post("/v1/session/message")
async def enqueue_message(
    payload: MessagePayload,
    bus: Annotated[KafkaEventBus, Depends(get_event_bus)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    """Accept a user message and enqueue it for processing."""
    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id,
        "message": payload.message,
        "attachments": payload.attachments,
        "metadata": payload.metadata,
    }

    try:
        await bus.publish("conversation.inbound", event)
    except Exception as exc:  # pragma: no cover - needs live Kafka
        LOGGER.exception("Failed to publish inbound event")
        raise HTTPException(status_code=502, detail="Unable to enqueue message") from exc

    # Cache most recent metadata for quick lookup.
    await cache.set(f"session:{session_id}:meta", {"persona_id": payload.persona_id or ""})
    await store.append_event(session_id, {"type": "user", **event})

    return JSONResponse({"session_id": session_id, "event_id": event_id})


@app.post("/v1/session/action")
async def enqueue_quick_action(
    payload: QuickActionPayload,
    bus: Annotated[KafkaEventBus, Depends(get_event_bus)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    template = QUICK_ACTIONS.get(payload.action)
    if not template:
        raise HTTPException(status_code=400, detail="Unknown action")

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id,
        "message": template,
        "attachments": [],
        "metadata": {**payload.metadata, "source": "quick_action", "action": payload.action},
    }

    await bus.publish("conversation.inbound", event)
    await cache.set(f"session:{session_id}:meta", {"persona_id": payload.persona_id or ""})
    await store.append_event(session_id, {"type": "user", **event})

    return JSONResponse({"session_id": session_id, "event_id": event_id})


async def stream_events(session_id: str) -> AsyncIterator[dict[str, str]]:
    group_id = f"gateway-{session_id}"
    async for payload in iterate_topic("conversation.outbound", group_id):
        if payload.get("session_id") == session_id:
            yield payload


@app.websocket("/v1/session/{session_id}/stream")
async def websocket_stream(
    websocket: WebSocket,
    session_id: str,
) -> None:
    await websocket.accept()
    try:
        async for event in stream_events(session_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        LOGGER.info("WebSocket disconnected", extra={"session_id": session_id})
    except Exception:  # pragma: no cover - live streaming only
        LOGGER.exception("WebSocket streaming error")
    finally:
        if not websocket.client_state.closed:
            await websocket.close()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    # Ensure background producers are closed on shutdown
    bus = KafkaEventBus()
    await bus.close()


@app.get("/health")
async def health_check(
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
) -> JSONResponse:
    components: dict[str, dict[str, str]] = {}
    overall_status = "ok"

    def record_status(name: str, status: str, detail: str | None = None) -> None:
        nonlocal overall_status
        components[name] = {"status": status}
        if detail:
            components[name]["detail"] = detail
        if status == "down":
            overall_status = "down"
        elif status == "degraded" and overall_status == "ok":
            overall_status = "degraded"

    try:
        await store.ping()
        record_status("postgres", "ok")
    except Exception as exc:  # pragma: no cover - external dependency
        record_status("postgres", "down", str(exc))

    try:
        await cache.ping()
        record_status("redis", "ok")
    except Exception as exc:  # pragma: no cover - external dependency
        record_status("redis", "down", str(exc))

    kafka_bus = KafkaEventBus()
    try:
        await kafka_bus.healthcheck()
        record_status("kafka", "ok")
    except Exception as exc:  # pragma: no cover - external dependency
        record_status("kafka", "down", str(exc))
    finally:
        await kafka_bus.close()

    async def check_http_target(name: str, url: str | None) -> None:
        if not url:
            return
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            record_status(name, "ok")
        except Exception as exc:  # pragma: no cover - external dependency
            record_status(name, "degraded", str(exc))

    await check_http_target("telemetry_worker", os.getenv("TELEMETRY_HEALTH_URL"))
    await check_http_target("delegation_gateway", os.getenv("DELEGATION_HEALTH_URL"))

    return JSONResponse({"status": overall_status, "components": components})
