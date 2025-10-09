"""FastAPI gateway for SomaAgent 01.

This service exposes the public HTTP/WebSocket surface. It validates
requests, enqueues events to Kafka, and streams outbound responses back
to clients. Real deployments should run this behind Kong/Envoy with mTLS.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
import uuid
from typing import Annotated, AsyncIterator, Any, Dict

import httpx
from contextlib import asynccontextmanager
try:
    import jwt  # type: ignore
except Exception:  # pragma: no cover
    class _MissingJWT:
        class PyJWTError(Exception):
            pass

        class algorithms:  # type: ignore
            class RSAAlgorithm:
                @staticmethod
                def from_jwk(*_, **__):
                    raise ImportError("PyJWT required for RSA verification")

            class ECAlgorithm:
                @staticmethod
                def from_jwk(*_, **__):
                    raise ImportError("PyJWT required for EC verification")

        @staticmethod
        def get_unverified_header(*_, **__):
            raise ImportError("PyJWT required for JWT header inspection")

        @staticmethod
        def decode(*_, **__):
            raise ImportError("PyJWT required for JWT validation")

    jwt = _MissingJWT()  # type: ignore

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from services.common.event_bus import KafkaEventBus, iterate_topic
from services.common.logging_config import setup_logging
from services.common.schema_validator import validate_event
from services.common.session_repository import (
    PostgresSessionStore,
    RedisSessionCache,
)
from services.common.trace_context import inject_trace_context
from services.common.tracing import setup_tracing
from services.common.vault_secrets import load_kv_secret
from services.common.openfga_client import OpenFGAClient
from python.helpers.circuit_breaker import ensure_metrics_exporter

setup_logging()
LOGGER = logging.getLogger(__name__)
tracer = setup_tracing("gateway")

# Start the standalone circuit-breaker metrics exporter if configured. This
# exposes the counters defined in ``python.helpers.circuit_breaker`` for
# Prometheus scraping alongside the FastAPI metrics surface.
ensure_metrics_exporter()


def _hydrate_jwt_credentials_from_vault() -> None:
    global JWT_SECRET, JWT_PUBLIC_KEY

    path = os.getenv("GATEWAY_JWT_VAULT_PATH")
    if not path:
        return

    mount_point = os.getenv("GATEWAY_JWT_VAULT_MOUNT", "secret")
    secret_key = os.getenv(
        "GATEWAY_JWT_VAULT_SECRET_KEY",
        os.getenv("GATEWAY_JWT_VAULT_KEY", "secret"),
    )
    if not JWT_SECRET and secret_key:
        secret = load_kv_secret(path=path, key=secret_key, mount_point=mount_point, logger=LOGGER)
        if secret:
            JWT_SECRET = secret
            LOGGER.info(
                "JWT secret hydrated from Vault",
                extra={"vault_path": path, "mount_point": mount_point},
            )

    public_key_key = os.getenv("GATEWAY_JWT_VAULT_PUBLIC_KEY_KEY")
    if not JWT_PUBLIC_KEY and public_key_key:
        public_key = load_kv_secret(
            path=path,
            key=public_key_key,
            mount_point=mount_point,
            logger=LOGGER,
        )
        if public_key:
            JWT_PUBLIC_KEY = public_key
            LOGGER.info(
                "JWT public key hydrated from Vault",
                extra={"vault_path": path, "mount_point": mount_point},
            )


_hydrate_jwt_credentials_from_vault()

@asynccontextmanager
async def gateway_lifespan(app: FastAPI):
    hub_monitor_task: asyncio.Task | None = None
    if SOMA_AGENT_HUB_MONITOR_ENABLED:
        hub_monitor_task = asyncio.create_task(_monitor_soma_agent_hub())
        app.state.hub_monitor_task = hub_monitor_task

    try:
        yield
    finally:
        if hub_monitor_task:
            hub_monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await hub_monitor_task
            if hasattr(app.state, "hub_monitor_task"):
                delattr(app.state, "hub_monitor_task")

        bus = KafkaEventBus()
        await bus.close()

app = FastAPI(
    title="SomaAgent 01 Gateway",
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    lifespan=gateway_lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_OPENAPI_CACHE: dict[str, Any] | None = None


@app.get("/openapi.json", include_in_schema=False)
async def openapi_document() -> JSONResponse:
    """Expose the service OpenAPI document at the canonical root path."""

    global _OPENAPI_CACHE
    if _OPENAPI_CACHE is None:
        _OPENAPI_CACHE = app.openapi()
    return JSONResponse(_OPENAPI_CACHE)


REQUEST_COUNTER = Counter(
    "gateway_requests_total",
    "Total HTTP requests processed by the gateway",
    labelnames=("method", "route", "status"),
)
REQUEST_LATENCY = Histogram(
    "gateway_request_latency_seconds",
    "Latency of HTTP requests handled by the gateway",
    labelnames=("route",),
)
KAFKA_PUBLISH_COUNTER = Counter(
    "gateway_kafka_publish_total",
    "Count of Kafka publish attempts from the gateway",
    labelnames=("topic", "status"),
)
STREAMED_EVENTS_COUNTER = Counter(
    "gateway_streamed_events_total",
    "Outbound events streamed to clients",
    labelnames=("transport",),
)
ACTIVE_WEBSOCKETS = Gauge(
    "gateway_active_websockets",
    "Current number of active WebSocket connections",
)
SOMA_AGENT_HUB_STATUS = Gauge(
    "soma_agent_hub_up",
    "Availability of the SomaAgentHub OpenAPI endpoint as probed by the gateway",
    labelnames=("endpoint",),
)
SOMA_AGENT_HUB_LATENCY = Histogram(
    "soma_agent_hub_openapi_latency_seconds",
    "Latency fetching the SomaAgentHub OpenAPI document",
    labelnames=("endpoint",),
)


def _resolve_route_label(request: Request) -> str:
    route = request.scope.get("route")  # FastAPI injects the APIRoute here
    if route and getattr(route, "path", None):
        return route.path
    return request.url.path


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    route_label = _resolve_route_label(request)
    start_time = time.perf_counter()
    status_code = "500"
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start_time
        REQUEST_COUNTER.labels(request.method, route_label, status_code).inc()
        REQUEST_LATENCY.labels(route_label).observe(duration)


def get_event_bus() -> KafkaEventBus:
    return KafkaEventBus()


def get_session_cache() -> RedisSessionCache:
    return RedisSessionCache()


def get_session_store() -> PostgresSessionStore:
    return PostgresSessionStore()


_OPENFGA_CLIENT: OpenFGAClient | None = None


def _get_openfga_client() -> OpenFGAClient | None:
    global _OPENFGA_CLIENT
    if _OPENFGA_CLIENT is None:
        store_id = os.getenv("OPENFGA_STORE_ID")
        if not store_id:
            LOGGER.warning("OPENFGA_STORE_ID not configured; skipping OpenFGA enforcement")
            return None
        fail_open = os.getenv("OPENFGA_FAIL_OPEN", "true").lower() in {"1", "true", "yes", "on"}
        try:
            _OPENFGA_CLIENT = OpenFGAClient(store_id=store_id, fail_open=fail_open)
        except ValueError as exc:
            LOGGER.error("Failed to initialise OpenFGA client", extra={"error": str(exc)})
            _OPENFGA_CLIENT = None
    return _OPENFGA_CLIENT


class MessagePayload(BaseModel):
    session_id: str | None = Field(
        default=None, description="Conversation context identifier"
    )
    persona_id: str | None = Field(
        default=None, description="Persona guiding this session"
    )
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

REQUIRE_AUTH = os.getenv("GATEWAY_REQUIRE_AUTH", "false").lower() in {
    "true",
    "1",
    "yes",
}
JWT_SECRET = os.getenv("GATEWAY_JWT_SECRET")
JWT_PUBLIC_KEY = os.getenv("GATEWAY_JWT_PUBLIC_KEY")
JWT_AUDIENCE = os.getenv("GATEWAY_JWT_AUDIENCE")
JWT_ISSUER = os.getenv("GATEWAY_JWT_ISSUER")
JWT_ALGORITHMS = [
    alg.strip()
    for alg in os.getenv("GATEWAY_JWT_ALGORITHMS", "HS256,RS256").split(",")
    if alg.strip()
]
JWT_JWKS_URL = os.getenv("GATEWAY_JWKS_URL")
JWT_JWKS_CACHE_SECONDS = float(os.getenv("GATEWAY_JWKS_CACHE_SECONDS", "300"))
JWT_LEEWAY = float(os.getenv("GATEWAY_JWT_LEEWAY", "10"))
JWT_TENANT_CLAIMS = [
    claim.strip()
    for claim in os.getenv("GATEWAY_JWT_TENANT_CLAIMS", "tenant,org,customer").split(
        ","
    )
    if claim.strip()
]
OPA_URL = os.getenv("OPA_URL")
OPA_DECISION_PATH = os.getenv("OPA_DECISION_PATH", "/v1/data/somastack/allow")
OPA_TIMEOUT_SECONDS = float(os.getenv("OPA_TIMEOUT_SECONDS", "3"))
JWKS_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_JWKS_TIMEOUT_SECONDS", "3"))

JWKS_CACHE: dict[str, tuple[list[dict[str, Any]], float]] = {}

SOMA_AGENT_HUB_URL = os.getenv(
    "SOMA_AGENT_HUB_URL", "http://host.docker.internal:60000"
)
SOMA_AGENT_HUB_OPENAPI_PATH = os.getenv(
    "SOMA_AGENT_HUB_OPENAPI_PATH", "/openapi.json"
)
SOMA_AGENT_HUB_CHECK_INTERVAL = float(
    os.getenv("SOMA_AGENT_HUB_CHECK_INTERVAL_SECONDS", "60")
)
SOMA_AGENT_HUB_TIMEOUT = float(os.getenv("SOMA_AGENT_HUB_TIMEOUT_SECONDS", "3"))
SOMA_AGENT_HUB_MONITOR_ENABLED = os.getenv(
    "SOMA_AGENT_HUB_MONITOR_ENABLED", "true"
).lower() in {"1", "true", "yes", "on"}

CAPSULE_REGISTRY_URL = os.getenv("CAPSULE_REGISTRY_URL", "http://localhost:8000")
CAPSULE_REGISTRY_TIMEOUT = float(os.getenv("CAPSULE_REGISTRY_TIMEOUT_SECONDS", "10"))


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


def _extract_subject(claims: Dict[str, Any]) -> str | None:
    subject = claims.get("sub")
    if subject is None:
        return None
    return str(subject)


def _apply_auth_metadata(
    metadata: Dict[str, str], auth_ctx: Dict[str, str]
) -> Dict[str, str]:
    merged = dict(metadata)
    for key, value in auth_ctx.items():
        if key not in merged and value is not None:
            merged[key] = value
    return merged


async def _load_session_context(
    session_id: str, cache: RedisSessionCache, store: PostgresSessionStore
) -> dict[str, Any]:
    cache_key = cache.format_key(session_id)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    envelope = await store.get_envelope(session_id)
    if not envelope:
        return {}

    context = {
        "persona_id": envelope.persona_id or "",
        "metadata": envelope.metadata,
    }
    try:
        await cache.write_context(session_id, envelope.persona_id, envelope.metadata)
    except Exception:
        LOGGER.warning("Failed to persist session cache", exc_info=True)
    return context


async def _hydrate_session_envelope(
    *,
    session_id: str,
    requested_persona: str | None,
    metadata: Dict[str, Any],
    cache: RedisSessionCache,
    store: PostgresSessionStore,
) -> tuple[str | None, Dict[str, Any]]:
    if not session_id:
        return requested_persona, metadata

    context = await _load_session_context(session_id, cache, store)
    merged_metadata = {**context.get("metadata", {}), **metadata}
    persona = requested_persona or context.get("persona_id") or None
    return persona, merged_metadata


async def _persist_session_context(
    session_id: str,
    persona_id: str | None,
    metadata: Dict[str, Any],
    cache: RedisSessionCache,
) -> None:
    try:
        await cache.write_context(session_id, persona_id, metadata)
    except Exception:
        LOGGER.warning("Failed to persist session cache", exc_info=True)
        raise


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


async def _evaluate_opa(
    request: Request, payload: Dict[str, Any], claims: Dict[str, Any]
) -> None:
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


async def authorize_request(
    request: Request, payload: Dict[str, Any]
) -> Dict[str, str]:
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
            LOGGER.error(
                "Unable to resolve signing key", extra={"alg": header.get("alg")}
            )
            if token_required:
                raise HTTPException(
                    status_code=500, detail="Unable to resolve signing key"
                )
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
    subject = _extract_subject(claims)
    if subject:
        auth_metadata["subject"] = subject
    if claims.get("iss"):
        auth_metadata["issuer"] = str(claims["iss"])
    if scope:
        auth_metadata["scope"] = scope

    # ---------- OpenFGA tenant enforcement ----------
    # If the OpenFGA client is configured, verify that the authenticated subject
    # is allowed to act within the resolved tenant. The check runs after any OPA
    # evaluation and will raise a 403 if the tenant access is denied.
    client = _get_openfga_client()
    if client and tenant and subject:
        try:
            allowed = await client.check_tenant_access(tenant=tenant, subject=subject)
        except Exception as exc:  # pragma: no cover – defensive guard
            LOGGER.error(
                "OpenFGA authorization failed",
                extra={"tenant": tenant, "subject": subject, "error": str(exc)},
            )
            allowed = False
        if not allowed:
            raise HTTPException(status_code=403, detail="Tenant access denied")

    return auth_metadata


@app.on_event("startup")
async def _start_background_tasks() -> None:
    if not SOMA_AGENT_HUB_MONITOR_ENABLED:
        return
    if getattr(app.state, "hub_monitor_task", None):
        return
    app.state.hub_monitor_task = asyncio.create_task(_monitor_soma_agent_hub())


@app.on_event("shutdown")
async def _stop_background_tasks() -> None:
    task = getattr(app.state, "hub_monitor_task", None)
    if not task:
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


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
    persona_id, hydrated_metadata = await _hydrate_session_envelope(
        session_id=session_id,
        requested_persona=payload.persona_id,
        metadata=metadata,
        cache=cache,
        store=store,
    )

    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": persona_id,
        "message": payload.message,
        "attachments": payload.attachments,
        "metadata": hydrated_metadata,
        "role": "user",
    }

    validate_event(event, "conversation_event")
    inject_trace_context(event)

    try:
        with tracer.start_as_current_span(
            "gateway.publish_inbound",
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": "conversation.inbound",
                "soma.session_id": session_id,
                "soma.persona_id": str(event.get("persona_id") or ""),
            },
        ):
            await bus.publish("conversation.inbound", event)
        KAFKA_PUBLISH_COUNTER.labels("conversation.inbound", "success").inc()
    except Exception as exc:  # pragma: no cover - needs live Kafka
        LOGGER.exception("Failed to publish inbound event")
        KAFKA_PUBLISH_COUNTER.labels("conversation.inbound", "error").inc()
        raise HTTPException(
            status_code=502, detail="Unable to enqueue message"
        ) from exc

    await _persist_session_context(session_id, event["persona_id"], event["metadata"], cache)
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
    persona_id, hydrated_metadata = await _hydrate_session_envelope(
        session_id=session_id,
        requested_persona=payload.persona_id,
        metadata={**metadata, "source": "quick_action", "action": payload.action},
        cache=cache,
        store=store,
    )

    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": persona_id,
        "message": template,
        "attachments": [],
        "metadata": hydrated_metadata,
        "role": "user",
    }

    validate_event(event, "conversation_event")
    inject_trace_context(event)

    try:
        with tracer.start_as_current_span(
            "gateway.publish_inbound",
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": "conversation.inbound",
                "soma.session_id": session_id,
                "soma.persona_id": str(event.get("persona_id") or ""),
            },
        ):
            await bus.publish("conversation.inbound", event)
        KAFKA_PUBLISH_COUNTER.labels("conversation.inbound", "success").inc()
    except Exception as exc:  # pragma: no cover - needs live Kafka
        KAFKA_PUBLISH_COUNTER.labels("conversation.inbound", "error").inc()
        raise HTTPException(status_code=502, detail="Unable to enqueue message") from exc
    await _persist_session_context(session_id, event["persona_id"], event["metadata"], cache)
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
    ACTIVE_WEBSOCKETS.inc()
    try:
        async for event in stream_events(session_id):
            STREAMED_EVENTS_COUNTER.labels("websocket").inc()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        LOGGER.info("WebSocket disconnected", extra={"session_id": session_id})
    except Exception:  # pragma: no cover - live streaming only
        LOGGER.exception("WebSocket streaming error")
    finally:
        ACTIVE_WEBSOCKETS.dec()
        if not websocket.client_state.closed:
            await websocket.close()


async def sse_stream(session_id: str) -> AsyncIterator[str]:
    async for event in stream_events(session_id):
        data = json.dumps(event)
        STREAMED_EVENTS_COUNTER.labels("sse").inc()
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


def _capsule_registry_url(path: str) -> str:
    base = CAPSULE_REGISTRY_URL.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


@app.get("/capsules")
async def proxy_list_capsules() -> JSONResponse:
    url = _capsule_registry_url("/capsules")
    try:
        async with httpx.AsyncClient(timeout=CAPSULE_REGISTRY_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Capsule registry unavailable") from exc
    return JSONResponse(response.json())


@app.post("/capsules/{capsule_id}/install")
async def proxy_install_capsule(capsule_id: str) -> JSONResponse:
    url = _capsule_registry_url(f"/capsules/{capsule_id}/install")
    try:
        async with httpx.AsyncClient(timeout=CAPSULE_REGISTRY_TIMEOUT) as client:
            response = await client.post(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Capsule registry unavailable") from exc
    return JSONResponse(response.json())


@app.get("/capsules/{capsule_id}")
async def proxy_download_capsule(capsule_id: str) -> Response:
    url = _capsule_registry_url(f"/capsules/{capsule_id}")
    try:
        async with httpx.AsyncClient(timeout=CAPSULE_REGISTRY_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Capsule registry unavailable") from exc

    headers: dict[str, str] = {}
    disposition = response.headers.get("content-disposition")
    if disposition:
        headers["Content-Disposition"] = disposition

    media_type = response.headers.get("content-type", "application/octet-stream")
    return Response(content=response.content, media_type=media_type, headers=headers)


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


@app.get("/metrics")
def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def _monitor_soma_agent_hub() -> None:
    """Periodically probe the SomaAgent Hub OpenAPI endpoint.
    Updates Prometheus gauges ``SOMA_AGENT_HUB_STATUS`` and ``SOMA_AGENT_HUB_LATENCY``.
    The probe runs only when ``SOMA_AGENT_HUB_MONITOR_ENABLED`` is true.
    """
    if not SOMA_AGENT_HUB_MONITOR_ENABLED:
        return
    endpoint = f"{SOMA_AGENT_HUB_URL.rstrip('/')}{SOMA_AGENT_HUB_OPENAPI_PATH}"
    interval = SOMA_AGENT_HUB_CHECK_INTERVAL
    timeout = SOMA_AGENT_HUB_TIMEOUT
    previous_up = 0.0
    while True:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
            up = 1.0
        except Exception as exc:  # pragma: no cover – network failures are expected in prod
            up = 0.0
            LOGGER.warning(
                "SomaAgent Hub health check failed",
                extra={"error": str(exc), "endpoint": endpoint},
            )
        latency = time.time() - start
        # Record metrics
        SOMA_AGENT_HUB_STATUS.labels(endpoint).set(up)
        SOMA_AGENT_HUB_LATENCY.labels(endpoint).observe(latency)
        # Log transitions for observability
        if up != previous_up:
            if up:
                LOGGER.info(
                    "SomaAgent Hub probe recovered",
                    extra={"endpoint": endpoint, "latency_seconds": latency},
                )
            else:
                LOGGER.warning(
                    "SomaAgent Hub probe down",
                    extra={"endpoint": endpoint, "latency_seconds": latency},
                )
            previous_up = up
        await asyncio.sleep(interval)
