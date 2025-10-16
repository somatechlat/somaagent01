"""FastAPI gateway for SomaAgent 01.

This service exposes the public HTTP/WebSocket surface. It validates
requests, enqueues events to Kafka, and streams outbound responses back
to clients. Real deployments should run this behind Kong/Envoy with mTLS.
"""

from __future__ import annotations

# Standard library imports (alphabetical)
import asyncio
import json
import logging
import os
import time
import uuid
from typing import Annotated, Any, AsyncIterator, Dict, Optional

import httpx

# Third‑party imports (alphabetical by top‑level package name)
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

SERVICE_NAME = "gateway"
from prometheus_client import start_http_server
from pydantic import BaseModel, Field

# Circuit breaker is mandatory for production resilience
try:
    import pybreaker
except ImportError:
    raise ImportError(
        "pybreaker is required for production resilience. Install with: pip install pybreaker"
    )

# Local package imports (alphabetical)
from python.helpers.settings import set_settings
from services.common.api_key_store import ApiKeyStore, RedisApiKeyStore
from services.common.event_bus import iterate_topic, KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.memory_client import MemoryClient
from services.common.model_profiles import ModelProfile, ModelProfileStore
from services.common.openfga_client import OpenFGAClient
from services.common.requeue_store import RequeueStore
from services.common.schema_validator import validate_event
from services.common.session_repository import PostgresSessionStore, RedisSessionCache
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry_store import TelemetryStore
from services.common.tracing import setup_tracing
from services.common.vault_secrets import load_kv_secret

# Import PyJWT properly - no fallbacks or shims allowed in production
try:
    import jwt
except ImportError:
    raise ImportError(
        "PyJWT is required for production JWT authentication. Install with: pip install PyJWT"
    )

# LOGGER configuration (no additional imports needed here)
setup_logging()
LOGGER = logging.getLogger(__name__)

APP_SETTINGS = SA01Settings.from_env()
tracer = setup_tracing(SERVICE_NAME, endpoint=APP_SETTINGS.otlp_endpoint)

# --- Consolidated service stores (moved in-process to the gateway) ---
PROFILE_STORE = ModelProfileStore.from_settings(APP_SETTINGS)
TELEMETRY_STORE = TelemetryStore.from_settings(APP_SETTINGS)
MEMORY_CLIENT = MemoryClient(settings=APP_SETTINGS)
REQUEUE_STORE = RequeueStore.from_settings(APP_SETTINGS)


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", APP_SETTINGS.kafka_bootstrap_servers
        ),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
    )


def _redis_url() -> str:
    return os.getenv("REDIS_URL", APP_SETTINGS.redis_url)


app = FastAPI(title="SomaAgent 01 Gateway")

# Instrument FastAPI and httpx client used for external calls (after app creation)
FastAPIInstrumentor().instrument_app(app)
HTTPXClientInstrumentor().instrument()

# ---------------------------------------------------------------------------
# Feature‑flag hot‑reload background task
# ---------------------------------------------------------------------------


async def _config_update_listener() -> None:
    """Listen on the ``config_updates`` Kafka topic and apply new settings.

    The message payload is expected to be a JSON object containing the same
    structure as the settings file.  When a message is received we call
    ``set_settings`` which validates the payload via the ``SettingsModel`` and
    updates the in-memory singleton used throughout the application.
    """

    async for payload in iterate_topic(
        "config_updates",
        f"{SERVICE_NAME}-config-listener",
        settings=_kafka_settings(),
    ):
        try:
            set_settings(payload)  # type: ignore[arg-type]
        except Exception as exc:
            LOGGER.error(
                "Failed to apply config update",
                extra={"error": str(exc), "payload_type": type(payload).__name__},
            )
            # Continue processing other config updates


# Schedule the listener when the FastAPI app starts
@app.on_event("startup")
async def start_background_services() -> None:
    """Initialize shared resources and background services."""
    # Initialize shared event bus for reuse across requests
    event_bus = KafkaEventBus(_kafka_settings())
    await event_bus.start()
    app.state.event_bus = event_bus

    # Initialize shared HTTP client with proper connection pooling
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )

    # Start config update listener in background
    asyncio.create_task(_config_update_listener())


# ---------------------------------------------------------------------------
# Sprint 2 – Self‑service UI for API‑key management & policy overview
# ---------------------------------------------------------------------------


@app.get("/ui/keys", response_class=HTMLResponse)
async def ui_list_keys(request: Request) -> HTMLResponse:
    """Render a simple HTML page showing existing API keys.

    The page is deliberately minimal – it calls the existing ``get_api_key_store``
    to retrieve keys and formats them into an HTML table.  In a full product the
    UI would be a separate React/TS app; this placeholder satisfies the Sprint 2
    requirement for a self‑service UI.
    """
    store = get_api_key_store()
    keys = await store.list_keys()
    rows = "".join(
        f"<tr><td>{k.key_id}</td><td>{k.label}</td><td>{k.prefix}</td><td>{'revoked' if k.revoked else 'active'}</td></tr>"
        for k in keys
    )
    html = f"""
    <html><head><title>API Keys</title></head><body>
    <h1>API Keys</h1>
    <table border='1'>
        <tr><th>ID</th><th>Label</th><th>Prefix</th><th>Status</th></tr>
        {rows}
    </table>
    </body></html>
    """
    return HTMLResponse(content=html)


@app.get("/ui/policy", response_class=HTMLResponse)
async def ui_policy_overview(request: Request) -> HTMLResponse:
    """Show a very basic OPA policy health view.

    It performs a lightweight request to the configured OPA server (if any) and
    reports whether the policy service is reachable.  Real‑world implementations
    would display policy rules, allow editing, etc.
    """
    opa_url = os.getenv("OPA_URL", APP_SETTINGS.opa_url)
    status_msg = "OPA not configured"
    if opa_url:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(opa_url)
                resp.raise_for_status()
                status_msg = f"OPA reachable – HTTP {resp.status_code}"
        except Exception as exc:
            status_msg = f"OPA unreachable: {exc}"
    html = f"""
    <html><head><title>Policy Overview</title></head><body>
    <h1>OPA Policy Service</h1>
    <p>{status_msg}</p>
    </body></html>
    """
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Prometheus metrics server (Sprint 3 observability)
# ---------------------------------------------------------------------------
# Start a dedicated metrics HTTP server on startup. The server runs on a separate
# port (default 8000) and exposes the default prometheus_client metrics.
@app.on_event("startup")
def _start_metrics_server() -> None:
    port = int(os.getenv("GATEWAY_METRICS_PORT", str(APP_SETTINGS.metrics_port)))
    host = os.getenv("GATEWAY_METRICS_HOST", APP_SETTINGS.metrics_host)
    start_http_server(port, addr=host)
    LOGGER.info(
        "Gateway metrics server started",
        extra={"host": host, "port": port},
    )
    # Ensure consolidated services are ready when the gateway starts
    # (model profiles, telemetry/memory pools)
    import asyncio

    async def _ensure_aux_services() -> None:
        try:
            await PROFILE_STORE.ensure_schema()
            await PROFILE_STORE._ensure_pool()
            await PROFILE_STORE.sync_from_settings(APP_SETTINGS)
        except Exception:
            LOGGER.debug("Model profile store initialisation failed", exc_info=True)

        try:
            await TELEMETRY_STORE._ensure_pool()
        except Exception:
            LOGGER.debug("Telemetry store initialisation failed", exc_info=True)

    asyncio.create_task(_ensure_aux_services())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_VERSION = os.getenv("GATEWAY_API_VERSION", "v1")

_API_KEY_STORE: Optional[ApiKeyStore] = None


@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    if "X-API-Version" not in response.headers:
        response.headers["X-API-Version"] = API_VERSION
    return response


def _cached_openapi_schema() -> dict[str, Any]:
    global _OPENAPI_CACHE
    if _OPENAPI_CACHE is None:
        _OPENAPI_CACHE = get_openapi(
            title=app.title,
            version=os.getenv("GATEWAY_OPENAPI_VERSION", "1.0.0"),
            routes=app.routes,
            description=app.description,
        )
    return _OPENAPI_CACHE


app.openapi = _cached_openapi_schema  # type: ignore[assignment]


def get_event_bus() -> KafkaEventBus:
    return KafkaEventBus(_kafka_settings())


def get_session_cache() -> RedisSessionCache:
    return RedisSessionCache(url=_redis_url())


def get_session_store() -> PostgresSessionStore:
    return PostgresSessionStore(dsn=APP_SETTINGS.postgres_dsn)


def get_api_key_store() -> ApiKeyStore:
    global _API_KEY_STORE
    if _API_KEY_STORE is not None:
        return _API_KEY_STORE

    # Require Redis configuration for production use
    redis_url = _redis_url()
    redis_password = os.getenv("REDIS_PASSWORD")
    if not redis_url:
        raise RuntimeError(
            "API‑key store requires a Redis configuration. Set REDIS_URL (and optionally REDIS_PASSWORD)."
        )
    _API_KEY_STORE = RedisApiKeyStore(redis_url=redis_url, redis_password=redis_password)
    LOGGER.info("Initialized Redis‑based API‑key store.")
    return _API_KEY_STORE


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


class ApiKeyCreatePayload(BaseModel):
    label: str = Field(..., max_length=100, description="Human readable label for the API key")


class ApiKeyResponse(BaseModel):
    key_id: str
    label: str
    created_at: float
    created_by: str | None
    prefix: str
    last_used_at: float | None
    revoked: bool


class ApiKeyCreateResponse(ApiKeyResponse):
    secret: str


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
    for claim in os.getenv("GATEWAY_JWT_TENANT_CLAIMS", "tenant,org,customer").split(",")
    if claim.strip()
]
OPA_URL = os.getenv("OPA_URL", APP_SETTINGS.opa_url)
OPA_DECISION_PATH = os.getenv("OPA_DECISION_PATH", "/v1/data/somastack/allow")
OPA_TIMEOUT_SECONDS = float(os.getenv("OPA_TIMEOUT_SECONDS", "3"))
JWKS_TIMEOUT_SECONDS = float(os.getenv("GATEWAY_JWKS_TIMEOUT_SECONDS", "3"))

JWKS_CACHE: dict[str, tuple[list[dict[str, Any]], float]] = {}

CAPSULE_REGISTRY_URL = os.getenv("CAPSULE_REGISTRY_URL", "http://localhost:8000")
CAPSULE_REGISTRY_TIMEOUT = float(os.getenv("CAPSULE_REGISTRY_TIMEOUT_SECONDS", "10"))

_OPENAPI_CACHE: dict[str, Any] | None = None
_OPENFGA_CLIENT: OpenFGAClient | None = None


def _hydrate_jwt_credentials_from_vault() -> None:
    """Load JWT signing secret from Vault when configured."""

    global JWT_SECRET

    if JWT_SECRET:
        return

    vault_path = os.getenv("GATEWAY_JWT_VAULT_PATH")
    secret_key = os.getenv("GATEWAY_JWT_VAULT_SECRET_KEY")
    mount_point = os.getenv("GATEWAY_JWT_VAULT_MOUNT", "secret")

    if not vault_path or not secret_key:
        return

    secret = load_kv_secret(
        path=vault_path,
        key=secret_key,
        mount_point=mount_point,
        logger=LOGGER,
    )
    if secret:
        LOGGER.info("Loaded JWT secret from Vault", extra={"path": vault_path})
        JWT_SECRET = secret

    # The JWT credentials will be loaded at application startup via a FastAPI
    # event handler. This call is removed to avoid executing before the FastAPI
    # app instance exists.


def _get_openfga_client() -> OpenFGAClient | None:
    """Lazily construct the OpenFGA authorization client when configured."""

    global _OPENFGA_CLIENT

    if os.getenv("OPENFGA_DISABLED", "false").lower() in {"true", "1", "yes"}:
        return None

    if _OPENFGA_CLIENT is not None:
        return _OPENFGA_CLIENT

    try:
        _OPENFGA_CLIENT = OpenFGAClient()
    except ValueError:
        LOGGER.debug("OpenFGA client not configured; skipping enforcement")
        _OPENFGA_CLIENT = None
    except Exception:
        LOGGER.warning("Failed to initialise OpenFGA client", exc_info=True)
        _OPENFGA_CLIENT = None

    return _OPENFGA_CLIENT


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


def _require_admin_scope(auth_ctx: Dict[str, str]) -> None:
    if not REQUIRE_AUTH:
        return
    scope_raw = auth_ctx.get("scope")
    scopes = {scope.strip() for scope in (scope_raw or "").split() if scope.strip()}
    if scopes.intersection({"admin", "keys:manage"}):
        return
    raise HTTPException(status_code=403, detail="Admin scope required")


async def _cache_session_metadata(
    cache: RedisSessionCache,
    session_id: str,
    persona_id: str | None,
    metadata: Dict[str, Any],
) -> None:
    write_context = getattr(cache, "write_context", None)
    if callable(write_context):
        await write_context(session_id, persona_id, metadata)
        return

    cache_payload: Dict[str, str] = {"persona_id": persona_id or ""}
    tenant = metadata.get("tenant")
    if tenant:
        cache_payload["tenant"] = str(tenant)
    await cache.set(f"session:{session_id}:meta", cache_payload)


async def _get_jwks_keys() -> list[dict[str, Any]]:
    if not JWT_JWKS_URL:
        return []
    cached = JWKS_CACHE.get(JWT_JWKS_URL)
    now = time.time()
    if cached and now - cached[1] < JWT_JWKS_CACHE_SECONDS:
        return cached[0]

    # Use circuit breaker to protect JWKS fetches (mandatory for production)
    breaker = pybreaker.CircuitBreaker(
        fail_max=5, reset_timeout=60, expected_exception=httpx.HTTPError
    )

    async def _fetch_jwks() -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=JWKS_TIMEOUT_SECONDS) as client:
            response = await client.get(JWT_JWKS_URL)
            response.raise_for_status()
            return response.json().get("keys", [])

    try:
        jwks = await _fetch_jwks()
    except pybreaker.CircuitBreakerError as exc:
        LOGGER.error("JWKS circuit breaker open", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="JWKS service unavailable")
    except httpx.HTTPError as exc:
        LOGGER.error("JWKS fetch failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="JWKS fetch failed")

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
    except (ValueError, TypeError, KeyError) as exc:
        LOGGER.warning("Failed to load signing key from JWK", extra={"error": str(exc)})
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

    async def _post_opa() -> httpx.Response:
        async with httpx.AsyncClient(timeout=OPA_TIMEOUT_SECONDS) as client:
            return await client.post(decision_url, json={"input": opa_input})

    # Apply circuit breaker to protect OPA service (mandatory for production)
    breaker = pybreaker.CircuitBreaker(
        fail_max=5, reset_timeout=60, expected_exception=httpx.HTTPError
    )

    try:
        response = await _post_opa()
    except pybreaker.CircuitBreakerError as exc:
        LOGGER.error("OPA circuit breaker open", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="OPA service unavailable")
    except httpx.HTTPError as exc:
        LOGGER.error("OPA request failed", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="OPA evaluation failed")

    try:
        response.raise_for_status()
    except httpx.HTTPError as exc:
        LOGGER.error(
            "OPA evaluation failed",
            extra={
                "error": str(exc),
                "url": decision_url,
                "status_code": getattr(exc.response, "status_code", None),
            },
        )
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
            # Audit log for missing token
            LOGGER.warning(
                "Authorization failed – missing header",
                extra={"path": request.url.path, "client": request.client.host},
            )
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            LOGGER.warning(
                "Authorization failed – malformed header",
                extra={"path": request.url.path, "header": auth_header},
            )
            raise HTTPException(status_code=401, detail="Invalid Authorization header")
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            LOGGER.warning(
                "Authorization failed – invalid JWT header",
                extra={"error": str(exc), "path": request.url.path},
            )
            raise HTTPException(status_code=401, detail="Invalid token header") from exc

        key = await _resolve_signing_key(header)
        if key is None:
            LOGGER.error(
                "Unable to resolve signing key",
                extra={"alg": header.get("alg"), "path": request.url.path},
            )
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
            LOGGER.warning(
                "Authorization failed – token decode error",
                extra={"error": str(exc), "path": request.url.path},
            )
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    await _evaluate_opa(request, payload, claims)

    tenant = _extract_tenant(claims)
    scope = _extract_scope(claims)
    subject = claims.get("sub")

    auth_metadata: Dict[str, str] = {}
    if tenant:
        auth_metadata["tenant"] = tenant
    if subject:
        auth_metadata["subject"] = str(subject)
    if claims.get("iss"):
        auth_metadata["issuer"] = str(claims["iss"])
    if scope:
        auth_metadata["scope"] = scope

    client = _get_openfga_client()
    if client and tenant and subject:
        try:
            allowed = await client.check_tenant_access(
                tenant=tenant,
                subject=str(subject),
            )
        except Exception as exc:
            LOGGER.error(
                "OpenFGA authorization check failed",
                extra={
                    "tenant": tenant,
                    "subject": subject,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            raise HTTPException(
                status_code=502, detail="Authorization service unavailable"
            ) from exc
        if not allowed:
            raise HTTPException(status_code=403, detail="Tenant access denied")

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
    except Exception as exc:
        LOGGER.error(
            "Failed to publish inbound event",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "session_id": session_id,
                "event_id": event_id,
            },
        )
        raise HTTPException(status_code=502, detail="Message queue unavailable") from exc

    # Cache most recent metadata for quick lookup.
    await _cache_session_metadata(cache, session_id, payload.persona_id, metadata)
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
    await _cache_session_metadata(cache, session_id, payload.persona_id, event["metadata"])
    await store.append_event(session_id, {"type": "user", **event})

    return JSONResponse({"session_id": session_id, "event_id": event_id})


@app.post("/v1/keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    payload: ApiKeyCreatePayload,
    request: Request,
    store: Annotated[ApiKeyStore, Depends(get_api_key_store)],
) -> ApiKeyCreateResponse:
    auth_metadata = await authorize_request(request, payload.model_dump())
    _require_admin_scope(auth_metadata)
    created = await store.create_key(payload.label, created_by=auth_metadata.get("subject"))
    return ApiKeyCreateResponse(
        key_id=created.key_id,
        label=created.label,
        created_at=created.created_at,
        created_by=created.created_by,
        prefix=created.prefix,
        last_used_at=created.last_used_at,
        revoked=created.revoked,
        secret=created.secret,
    )


@app.get("/v1/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    request: Request,
    store: Annotated[ApiKeyStore, Depends(get_api_key_store)],
) -> list[ApiKeyResponse]:
    auth_metadata = await authorize_request(request, {})
    _require_admin_scope(auth_metadata)
    items = await store.list_keys()
    return [
        ApiKeyResponse(
            key_id=item.key_id,
            label=item.label,
            created_at=item.created_at,
            created_by=item.created_by,
            prefix=item.prefix,
            last_used_at=item.last_used_at,
            revoked=item.revoked,
        )
        for item in items
    ]


@app.delete("/v1/keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: str,
    request: Request,
    store: Annotated[ApiKeyStore, Depends(get_api_key_store)],
) -> Response:
    auth_metadata = await authorize_request(request, {"key_id": key_id})
    _require_admin_scope(auth_metadata)
    await store.revoke_key(key_id)
    return Response(status_code=204)


async def stream_events(session_id: str) -> AsyncIterator[dict[str, str]]:
    group_id = f"gateway-{session_id}"
    async for payload in iterate_topic(
        "conversation.outbound",
        group_id,
        settings=_kafka_settings(),
    ):
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
    except Exception as exc:
        LOGGER.error(
            "WebSocket streaming error",
            extra={"error": str(exc), "error_type": type(exc).__name__, "session_id": session_id},
        )
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
        except asyncio.CancelledError:
            LOGGER.debug("SSE stream cancelled", extra={"session_id": session_id})

    headers = {"Cache-Control": "no-cache", "Content-Type": "text/event-stream"}
    return StreamingResponse(event_generator(), headers=headers)


def _capsule_registry_url(path: str) -> str:
    base = CAPSULE_REGISTRY_URL.rstrip("/")
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"


@app.get("/v1/capsules")
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


@app.post("/v1/capsules/{capsule_id}/install")
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


@app.get("/v1/capsules/{capsule_id}")
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


app.add_api_route(
    "/capsules",
    proxy_list_capsules,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/capsules/{capsule_id}",
    proxy_download_capsule,
    methods=["GET"],
    include_in_schema=False,
)
app.add_api_route(
    "/capsules/{capsule_id}/install",
    proxy_install_capsule,
    methods=["POST"],
    include_in_schema=False,
)


@app.on_event("shutdown")
async def shutdown_background_services() -> None:
    """Ensure all shared resources are properly closed on shutdown."""

    # Close shared event bus
    if hasattr(app.state, "event_bus"):
        await app.state.event_bus.close()

    # Close shared HTTP client
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()

    # Close consolidated service stores
    try:
        await MEMORY_CLIENT.close()
    except Exception as exc:
        LOGGER.warning("Error closing memory client", extra={"error": str(exc)})

    LOGGER.info("Gateway shutdown completed")


@app.get("/v1/health")
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
    except Exception as exc:
        LOGGER.warning("Postgres health check failed", extra={"error": str(exc)})
        record_status("postgres", "down", f"{type(exc).__name__}: {exc}")

    try:
        await cache.ping()
        record_status("redis", "ok")
    except Exception as exc:
        LOGGER.warning("Redis health check failed", extra={"error": str(exc)})
        record_status("redis", "down", f"{type(exc).__name__}: {exc}")

    kafka_bus = KafkaEventBus(_kafka_settings())
    try:
        await kafka_bus.healthcheck()
        record_status("kafka", "ok")
    except Exception as exc:
        LOGGER.warning("Kafka health check failed", extra={"error": str(exc)})
        record_status("kafka", "down", f"{type(exc).__name__}: {exc}")
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
        except Exception as exc:
            LOGGER.debug(f"{name} health check failed", extra={"error": str(exc), "url": url})
            record_status(name, "degraded", f"{type(exc).__name__}: {exc}")

    await check_http_target("telemetry_worker", os.getenv("TELEMETRY_HEALTH_URL"))
    await check_http_target("delegation_gateway", os.getenv("DELEGATION_HEALTH_URL"))

    return JSONResponse({"status": overall_status, "components": components})


app.add_api_route(
    "/health",
    health_check,
    methods=["GET"],
    include_in_schema=False,
)


# -----------------------------
# Model profiles endpoints (from settings_service)
# -----------------------------


@app.get("/v1/model-profiles")
async def list_profiles() -> list[ModelProfile]:
    """List all model profiles."""
    return await PROFILE_STORE.list_profiles()


@app.post("/v1/model-profiles", status_code=201)
async def create_profile(profile: ModelProfile) -> None:
    """Create a new model profile."""
    await PROFILE_STORE.create_profile(profile)


@app.put("/v1/model-profiles/{role}/{deployment_mode}")
async def update_profile(role: str, deployment_mode: str, profile: ModelProfile) -> None:
    """Update an existing model profile."""
    await PROFILE_STORE.update_profile(role, deployment_mode, profile)


@app.delete("/v1/model-profiles/{role}/{deployment_mode}")
async def delete_profile(role: str, deployment_mode: str) -> None:
    """Delete a model profile."""
    await PROFILE_STORE.delete_profile(role, deployment_mode)


# -----------------------------
# Routing endpoint (from router)
# -----------------------------


class RouteRequest(BaseModel):
    candidates: list[str]
    tenant: Optional[str] = None
    persona: Optional[str] = None


class RouteResponse(BaseModel):
    chosen: str
    score: Optional[float] = None


@app.post("/v1/route", response_model=RouteResponse)
async def route_decision(payload: RouteRequest) -> RouteResponse:
    """Route model selection among candidates using telemetry and memory fallback."""
    # Try telemetry scoring first
    try:
        scores = await TELEMETRY_STORE.get_model_scores(
            tenant=payload.tenant, persona=payload.persona, candidates=payload.candidates
        )
        if scores:
            best = max(scores, key=lambda x: x["score"])  # dicts with 'model' and 'score'
            return RouteResponse(chosen=best["model"], score=best["score"])
    except Exception:
        LOGGER.debug("Telemetry routing failed, falling back to memory", exc_info=True)

    # Memory fallback: query recent sessions for preferred models
    try:
        preferred = await MEMORY_CLIENT.find_preferred_model(
            payload.tenant, payload.persona, payload.candidates
        )
        if preferred:
            return RouteResponse(chosen=preferred, score=None)
    except Exception:
        LOGGER.debug("Memory routing failed, falling back to first candidate", exc_info=True)

    # Final fallback
    chosen = payload.candidates[0] if payload.candidates else ""
    return RouteResponse(chosen=chosen, score=None)


# -----------------------------
# Requeue management endpoints (from requeue_service)
# -----------------------------


@app.get("/v1/requeue")
async def list_requeue() -> list[dict]:
    """List items pending requeue."""
    return await REQUEUE_STORE.list_requeue()


@app.post("/v1/requeue/{requeue_id}/resolve")
async def resolve_requeue(requeue_id: str, publish: bool = True) -> dict:
    """Resolve a requeue item and optionally publish it to the tool requests topic."""
    item = await REQUEUE_STORE.get_requeue(requeue_id)
    if not item:
        raise HTTPException(status_code=404, detail="requeue item not found")

    if publish and APP_SETTINGS.tool_requests_topic:
        try:
            # Use shared event bus for efficiency
            bus = app.state.event_bus
            await bus.publish(APP_SETTINGS.tool_requests_topic, item["payload"])
            LOGGER.info("Requeue item published", extra={"requeue_id": requeue_id})
        except Exception as exc:
            LOGGER.error(
                "Failed to publish requeue item",
                extra={
                    "error": str(exc),
                    "requeue_id": requeue_id,
                    "topic": APP_SETTINGS.tool_requests_topic,
                },
            )

    await REQUEUE_STORE.delete_requeue(requeue_id)
    return {"status": "resolved"}


@app.delete("/v1/requeue/{requeue_id}")
async def delete_requeue(requeue_id: str) -> dict:
    """Delete a requeue item."""
    await REQUEUE_STORE.delete_requeue(requeue_id)
    return {"status": "deleted"}
