"""FastAPI gateway for SomaAgent 01.

This service exposes the public HTTP/WebSocket surface. It validates
requests, enqueues events to Kafka, and streams outbound responses back
to clients. Real deployments should run this behind Kong/Envoy with mTLS.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Annotated, AsyncIterator, Any, Dict

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from services.common.event_bus import KafkaEventBus, KafkaSettings, iterate_topic
from services.common.schema_validator import validate_event
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

REQUIRE_AUTH = os.getenv("GATEWAY_REQUIRE_AUTH", "false").lower() in {"true", "1", "yes"}
JWT_SECRET = os.getenv("GATEWAY_JWT_SECRET")
JWT_PUBLIC_KEY = os.getenv("GATEWAY_JWT_PUBLIC_KEY")
JWT_AUDIENCE = os.getenv("GATEWAY_JWT_AUDIENCE")
JWT_ISSUER = os.getenv("GATEWAY_JWT_ISSUER")
JWT_ALGORITHMS = [alg.strip() for alg in os.getenv("GATEWAY_JWT_ALGORITHMS", "HS256,RS256").split(",") if alg.strip()]
JWT_JWKS_URL = os.getenv("GATEWAY_JWKS_URL")
JWT_JWKS_CACHE_SECONDS = float(os.getenv("GATEWAY_JWKS_CACHE_SECONDS", "300"))
JWT_LEEWAY = float(os.getenv("GATEWAY_JWT_LEEWAY", "10"))
JWT_TENANT_CLAIMS = [claim.strip() for claim in os.getenv("GATEWAY_JWT_TENANT_CLAIMS", "tenant,org,customer").split(",") if claim.strip()]
OPA_URL = os.getenv("OPA_URL")
OPA_DECISION_PATH = os.getenv("OPA_DECISION_PATH", "/v1/data/somastack/allow")
OPA_TIMEOUT_SECONDS = float(os.getenv("OPA_TIMEOUT_SECONDS", "3"))
JWKS_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_JWKS_TIMEOUT_SECONDS", "3"))

JWKS_CACHE: dict[str, tuple[list[dict[str, Any]], float]] = {}


def _extract_tenant(claims: Dict[str, Any]) -> str | None:
    for key in JWT_TENANT_CLAIMS:
        value = claims.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)) and value:
            return str(value[0])
        return str(value)
    return None


def _extract_scope(claims: Dict[str, Any]) -> str | None:
    scope = claims.get("scope") or claims.get("scp")
    if scope is None:
        return None
    if isinstance(scope, (list, tuple, set)):
        return " ".join(str(item) for item in scope)
    return str(scope)


def _apply_auth_metadata(metadata: Dict[str, str], auth_ctx: Dict[str, str]) -> Dict[str, str]:
    merged = dict(metadata)
    for key, value in auth_ctx.items():
        if key not in merged and value is not None:
            merged[key] = value
    return merged


async def _get_jwks_keys() -> list[dict[str, Any]]:
    if not JWT_JWKS_URL:
        return []
    cached = JWKS_CACHE.get(JWT_JWKS_URL)
    now = time.time()
    if cached and now - cached[1] < JWT_JWKS_CACHE_SECONDS:
        return cached[0]
    try:
        async with httpx.AsyncClient(timeout=JWKS_TIMEOUT_SECONDS) as client:
            response = await client.get(JWT_JWKS_URL)
            response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - external dependency
        LOGGER.error("Failed to fetch JWKS", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Failed to fetch JWKS") from exc
    jwks = response.json().get("keys", [])
    JWKS_CACHE[JWT_JWKS_URL] = (jwks, now)
    return jwks


def _load_key_from_jwk(jwk: dict[str, Any], alg: str | None) -> Any:
    jwk_json = json.dumps(jwk)
    try:
        if alg and alg.startswith("RS"):
            return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
        if alg and alg.startswith("ES"):
            return jwt.algorithms.ECAlgorithm.from_jwk(jwk_json)
        if alg and alg.startswith("HS") and jwk.get("k"):
            return jwk["k"]
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
    except Exception:  # pragma: no cover - defensive
        return None


async def _resolve_signing_key(header: Dict[str, Any]) -> Any:
    alg = header.get("alg")
    if alg and alg.startswith("HS") and JWT_SECRET:
        return JWT_SECRET
    if JWT_PUBLIC_KEY and alg and (alg.startswith("RS") or alg.startswith("ES")):
        return JWT_PUBLIC_KEY
    if JWT_JWKS_URL:
        keys = await _get_jwks_keys()
        kid = header.get("kid")
        for jwk in keys:
            if kid and jwk.get("kid") != kid:
                continue
            key = _load_key_from_jwk(jwk, alg)
            if key:
                return key
    if JWT_SECRET:
        return JWT_SECRET
    if JWT_PUBLIC_KEY:
        return JWT_PUBLIC_KEY
    return None


async def _evaluate_opa(request: Request, payload: Dict[str, Any], claims: Dict[str, Any]) -> None:
    if not OPA_URL:
        return

    decision_url = f"{OPA_URL.rstrip('/')}{OPA_DECISION_PATH}"
    opa_input = {
        "request": {
            "method": request.method,
            "path": request.url.path,
            "headers": {key: value for key, value in request.headers.items()},
        },
        "payload": payload,
        "claims": claims,
    }

    try:
        async with httpx.AsyncClient(timeout=OPA_TIMEOUT_SECONDS) as client:
            response = await client.post(decision_url, json={"input": opa_input})
            response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - external dependency
        LOGGER.error("OPA evaluation failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="OPA evaluation failed") from exc

    decision = response.json()
    result = decision.get("result")
    allow = result.get("allow") if isinstance(result, dict) else result
    if not allow:
        raise HTTPException(status_code=403, detail="Request blocked by policy")


async def authorize_request(request: Request, payload: Dict[str, Any]) -> Dict[str, str]:
    token_required = REQUIRE_AUTH or any([JWT_SECRET, JWT_PUBLIC_KEY, JWT_JWKS_URL])
    auth_header = request.headers.get("authorization")

    claims: Dict[str, Any] = {}

    if token_required or auth_header:
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid token header") from exc

        key = await _resolve_signing_key(header)
        if key is None:
            LOGGER.error("Unable to resolve signing key", extra={"alg": header.get("alg")})
            if token_required:
                raise HTTPException(status_code=500, detail="Unable to resolve signing key")
            else:
                raise HTTPException(status_code=401, detail="Signing key unavailable")

        decode_kwargs: Dict[str, Any] = {
            "algorithms": JWT_ALGORITHMS or [header.get("alg")],
            "options": {"verify_aud": bool(JWT_AUDIENCE)},
            "leeway": JWT_LEEWAY,
        }
        if JWT_AUDIENCE:
            decode_kwargs["audience"] = JWT_AUDIENCE
        if JWT_ISSUER:
            decode_kwargs["issuer"] = JWT_ISSUER

        try:
            claims = jwt.decode(token, key=key, **decode_kwargs)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    await _evaluate_opa(request, payload, claims)

    tenant = _extract_tenant(claims)
    scope = _extract_scope(claims)
    auth_metadata: Dict[str, str] = {}
    if tenant:
        auth_metadata["tenant"] = tenant
    if claims.get("sub"):
        auth_metadata["subject"] = str(claims["sub"])
    if claims.get("iss"):
        auth_metadata["issuer"] = str(claims["iss"])
    if scope:
        auth_metadata["scope"] = scope

    return auth_metadata

@app.post("/v1/session/message")
async def enqueue_message(
    payload: MessagePayload,
    request: Request,
    bus: Annotated[KafkaEventBus, Depends(get_event_bus)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    """Accept a user message and enqueue it for processing."""
    auth_metadata = await authorize_request(request, payload.model_dump())
    metadata = _apply_auth_metadata(payload.metadata, auth_metadata)

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id,
        "message": payload.message,
        "attachments": payload.attachments,
        "metadata": metadata,
        "role": "user",
    }

    validate_event(event, "conversation_event")

    try:
        await bus.publish("conversation.inbound", event)
    except Exception as exc:  # pragma: no cover - needs live Kafka
        LOGGER.exception("Failed to publish inbound event")
        raise HTTPException(status_code=502, detail="Unable to enqueue message") from exc

    # Cache most recent metadata for quick lookup.
    cache_payload = {"persona_id": payload.persona_id or ""}
    if metadata.get("tenant"):
        cache_payload["tenant"] = metadata["tenant"]
    await cache.set(f"session:{session_id}:meta", cache_payload)
    await store.append_event(session_id, {"type": "user", **event})

    return JSONResponse({"session_id": session_id, "event_id": event_id})


@app.post("/v1/session/action")
async def enqueue_quick_action(
    payload: QuickActionPayload,
    request: Request,
    bus: Annotated[KafkaEventBus, Depends(get_event_bus)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    template = QUICK_ACTIONS.get(payload.action)
    if not template:
        raise HTTPException(status_code=400, detail="Unknown action")

    auth_metadata = await authorize_request(request, payload.model_dump())
    metadata = _apply_auth_metadata(payload.metadata, auth_metadata)

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id,
        "message": template,
        "attachments": [],
        "metadata": {**metadata, "source": "quick_action", "action": payload.action},
        "role": "user",
    }

    validate_event(event, "conversation_event")

    await bus.publish("conversation.inbound", event)
    cache_payload = {"persona_id": payload.persona_id or ""}
    if event["metadata"].get("tenant"):
        cache_payload["tenant"] = event["metadata"]["tenant"]
    await cache.set(f"session:{session_id}:meta", cache_payload)
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


async def sse_stream(session_id: str) -> AsyncIterator[str]:
    async for event in stream_events(session_id):
        data = json.dumps(event)
        yield f"data: {data}\n\n"


@app.get("/v1/session/{session_id}/events")
async def sse_endpoint(session_id: str, request: Request) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        try:
            async for chunk in sse_stream(session_id):
                yield chunk
                if await request.is_disconnected():
                    break
        except asyncio.CancelledError:  # pragma: no cover - cancellation path
            pass

    headers = {"Cache-Control": "no-cache", "Content-Type": "text/event-stream"}
    return StreamingResponse(event_generator(), headers=headers)


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
