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
from datetime import datetime
from typing import Annotated, Any, AsyncIterator, Dict, Optional

import httpx

# Third‑party imports (alphabetical by top‑level package name)
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_client import Counter, Gauge, Histogram, start_http_server, REGISTRY
from pydantic import BaseModel, Field

SERVICE_NAME = "gateway"

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
from services.common.dlq_store import DLQStore
from services.common.event_bus import iterate_topic, KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.memory_replica_store import MemoryReplicaStore
from services.common.memory_write_outbox import MemoryWriteOutbox
from services.common.export_job_store import ExportJobStore, ensure_schema as ensure_export_jobs_schema
from services.common.model_profiles import ModelProfile, ModelProfileStore
from services.common.ui_settings_store import UiSettingsStore
from services.common.openfga_client import OpenFGAClient
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.memory_write_outbox import MemoryWriteOutbox, ensure_schema as ensure_mw_outbox_schema
from services.common.llm_credentials_store import LlmCredentialsStore
from services.common.publisher import DurablePublisher
from services.common.requeue_store import RequeueStore
from services.common.schema_validator import validate_event
from services.common.session_repository import PostgresSessionStore, RedisSessionCache
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry_store import TelemetryStore
from services.common.tracing import setup_tracing
from services.common.vault_secrets import load_kv_secret
from services.common.idempotency import generate_for_memory_payload
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from services.common.memory_write_outbox import MemoryWriteOutbox

# Import PyJWT properly - no fallbacks or shims allowed in production
try:
    import jwt
except ImportError:
    # PyJWT is mandatory. Fail fast so missing dependencies are fixed in CI / build.
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


# -----------------------------
# CORS configuration (env-driven)
# -----------------------------

def _csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _setup_cors() -> None:
    origins = _csv_list(os.getenv("GATEWAY_CORS_ORIGINS"))
    methods = _csv_list(os.getenv("GATEWAY_CORS_METHODS"))
    headers = _csv_list(os.getenv("GATEWAY_CORS_HEADERS"))
    expose = _csv_list(os.getenv("GATEWAY_CORS_EXPOSE_HEADERS"))
    allow_credentials = os.getenv("GATEWAY_CORS_CREDENTIALS", "false").lower() in {"true", "1", "yes", "on"}

    # Defaults: permissive in dev, explicit in prod via env
    if not origins:
        origins = ["*"]
    if not methods:
        methods = ["*"]
    if not headers:
        headers = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=methods,
        allow_headers=headers,
        expose_headers=expose or None,
        allow_credentials=allow_credentials,
    )


_setup_cors()

def _get_or_create_counter(name: str, documentation: str, *, labelnames: tuple[str, ...] = ()) -> Counter:
    try:
        return Counter(name, documentation, labelnames=labelnames)
    except ValueError:
        # Attempt to reuse existing collector when tests import module multiple times
        existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)  # type: ignore[attr-defined]
        if isinstance(existing, Counter):
            return existing
        raise


def _get_or_create_gauge(name: str, documentation: str, *, labelnames: tuple[str, ...] = ()) -> Gauge:
    try:
        return Gauge(name, documentation, labelnames=labelnames)
    except ValueError:
        existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)  # type: ignore[attr-defined]
        if isinstance(existing, Gauge):
            return existing
        raise


def _get_or_create_histogram(name: str, documentation: str, *, labelnames: tuple[str, ...] = ()) -> Histogram:
    try:
        return Histogram(name, documentation, labelnames=labelnames)
    except ValueError:
        existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)  # type: ignore[attr-defined]
        if isinstance(existing, Histogram):
            return existing
        raise


# Gateway write-through metrics (emitted when GATEWAY_WRITE_THROUGH is enabled)
GATEWAY_WT_ATTEMPTS = _get_or_create_counter(
    "gateway_write_through_attempts_total",
    "Total write-through attempts from gateway to SomaBrain",
    labelnames=("path",),
)
GATEWAY_WT_RESULTS = _get_or_create_counter(
    "gateway_write_through_results_total",
    "Write-through outcomes from gateway to SomaBrain",
    labelnames=("path", "result"),  # result: ok|client_error|server_error|exception
)
GATEWAY_WT_WAL_RESULTS = _get_or_create_counter(
    "gateway_write_through_wal_results_total",
    "Outcome of WAL publish following gateway write-through",
    labelnames=("path", "result"),  # result: ok|error
)

# DLQ depth gauge for observability/alerts
GATEWAY_DLQ_DEPTH = _get_or_create_gauge(
    "gateway_dlq_depth",
    "Current depth of DLQ messages recorded in Postgres",
    labelnames=("topic",),
)

# Export jobs metrics
EXPORT_JOBS = _get_or_create_counter(
    "gateway_export_jobs_total",
    "Export job outcomes",
    labelnames=("result",),
)
EXPORT_JOB_SECONDS = _get_or_create_histogram(
    "gateway_export_job_seconds",
    "Export job processing time (seconds)",
)

# -----------------------------
# DLQ depth refresher settings
# -----------------------------
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _dlq_topics_from_env() -> list[str]:
    raw = os.getenv("DLQ_TOPICS", "")
    topics = [t.strip() for t in raw.split(",") if t.strip()]
    if not topics:
        topics = [f"{os.getenv('MEMORY_WAL_TOPIC', 'memory.wal')}.dlq"]
    return topics


# Helper to construct a CircuitBreaker in a backward-compatible way.
def _make_circuit_breaker(*, fail_max: int = 5, reset_timeout: int = 60, expected_exception: type | None = None):
    """Create a pybreaker.CircuitBreaker while accepting older pybreaker
    versions that don't support the `expected_exception` keyword.

    We try the modern signature first and fall back gracefully on TypeError.
    """
    if expected_exception is None:
        # Simple fast path
        return pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout)
    try:
        return pybreaker.CircuitBreaker(
            fail_max=fail_max, reset_timeout=reset_timeout, expected_exception=expected_exception
        )
    except TypeError:
        # Older pybreaker versions don't accept `expected_exception`; fall back.
        return pybreaker.CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout)


def _classify_wt_error(exc: Exception) -> str:
    """Map exceptions to stable result labels for write-through metrics.

    Returns one of: client_error | server_error | exception.
    Attempts to parse a 3-digit HTTP status from the exception text.
    """
    text = str(exc)
    try:
        import re

        m = re.search(r"\b(\d{3})\b", text)
        if m:
            code = int(m.group(1))
            if 400 <= code < 500:
                return "client_error"
            if 500 <= code < 600:
                return "server_error"
    except Exception:
        pass
    if " 4" in text or " 40" in text:
        return "client_error"
    if " 5" in text or " 50" in text:
        return "server_error"
    return "exception"

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
    # No explicit start() on our KafkaEventBus; producer is initialized lazily.
    # Try a lightweight healthcheck, but don't block startup if Kafka isn't ready yet.
    try:
        await event_bus.healthcheck()
    except Exception:
        LOGGER.debug("Kafka event bus healthcheck failed at startup (will retry on demand)", exc_info=True)
    app.state.event_bus = event_bus

    # Initialize durable publisher with Outbox fallback
    outbox_store = OutboxStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    try:
        await ensure_outbox_schema(outbox_store)
    except Exception:
        LOGGER.debug("Outbox schema ensure failed", exc_info=True)
    app.state.outbox_store = outbox_store
    app.state.publisher = DurablePublisher(bus=event_bus, outbox=outbox_store)

    # Initialize memory write outbox for fail-safe remember() retry
    mem_outbox = MemoryWriteOutbox(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    try:
        await ensure_mw_outbox_schema(mem_outbox)
    except Exception:
        LOGGER.debug("MemoryWriteOutbox schema ensure failed", exc_info=True)
    app.state.mem_write_outbox = mem_outbox

    # Initialize shared HTTP client with proper connection pooling
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )

    # Start config update listener in background
    asyncio.create_task(_config_update_listener())

    # Start DLQ depth refresher in background
    try:
        app.state._dlq_refresher_stop = asyncio.Event()
        asyncio.create_task(_dlq_depth_refresher())
    except Exception:
        LOGGER.debug("Failed to start DLQ refresher task", exc_info=True)

    # Initialize export jobs store and schema, then start worker
    try:
        export_store = get_export_job_store()
        await ensure_export_jobs_schema(export_store)
    except Exception:
        LOGGER.debug("Export jobs schema ensure failed", exc_info=True)
    try:
        app.state._export_runner_stop = asyncio.Event()
        asyncio.create_task(_export_jobs_runner())
    except Exception:
        LOGGER.debug("Failed to start export jobs runner", exc_info=True)

    # Ensure UI settings schema exists (best-effort)
    try:
        await get_ui_settings_store().ensure_schema()
    except Exception:
        LOGGER.debug("UI settings schema ensure failed", exc_info=True)


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


# CORS is configured via _setup_cors above

API_VERSION = os.getenv("GATEWAY_API_VERSION", "v1")
def _flag_truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"true", "1", "yes", "on"}


def _write_through_enabled() -> bool:
    return _flag_truthy(os.getenv("GATEWAY_WRITE_THROUGH"), False)


def _write_through_async() -> bool:
    return _flag_truthy(os.getenv("GATEWAY_WRITE_THROUGH_ASYNC"), False)

_API_KEY_STORE: Optional[ApiKeyStore] = None
_DLQ_STORE: Optional[DLQStore] = None
_REPLICA_STORE: Optional[MemoryReplicaStore] = None
_LLM_CRED_STORE: Optional[LlmCredentialsStore] = None
_UI_SETTINGS_STORE: Optional[UiSettingsStore] = None


@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    if "X-API-Version" not in response.headers:
        response.headers["X-API-Version"] = API_VERSION
    return response


# -----------------------------
# Optional CSRF protection (for cookie-based sessions)
# -----------------------------

def _csrf_enabled() -> bool:
    return os.getenv("GATEWAY_CSRF_ENABLED", "false").lower() in {"true", "1", "yes", "on"}


def _csrf_enforce_for_bearer() -> bool:
    return os.getenv("GATEWAY_CSRF_ENFORCE_FOR_BEARER", "false").lower() in {"true", "1", "yes", "on"}


@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    if not _csrf_enabled():
        return await call_next(request)

    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return await call_next(request)

    # If using bearer tokens and not enforcing CSRF for Authorization flows, skip
    if (not _csrf_enforce_for_bearer()) and request.headers.get("authorization"):
        return await call_next(request)

    cookie_name = os.getenv("GATEWAY_CSRF_COOKIE_NAME", "csrf_token")
    expected = request.cookies.get(cookie_name)
    header = request.headers.get("x-csrf-token")
    if not expected or not header or header != expected:
        return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)
    return await call_next(request)


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


def get_publisher() -> DurablePublisher:
    # If tests override the event bus, respect that by creating a temporary publisher
    overrides = getattr(app, "dependency_overrides", {})
    get_bus_override = overrides.get(get_event_bus)
    if get_bus_override is not None:
        bus = get_bus_override()
        outbox = getattr(app.state, "outbox_store", None) or OutboxStore(
            dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn)
        )
        return DurablePublisher(bus=bus, outbox=outbox)

    # Use the shared instance initialised at startup
    publisher = getattr(app.state, "publisher", None)
    if publisher is None:
        # Fallback construction (should not happen in normal startup)
        event_bus = KafkaEventBus(_kafka_settings())
        outbox_store = OutboxStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
        publisher = DurablePublisher(bus=event_bus, outbox=outbox_store)
        app.state.publisher = publisher
    return publisher


def get_session_cache() -> RedisSessionCache:
    return RedisSessionCache(url=_redis_url())


def get_session_store() -> PostgresSessionStore:
    dsn = os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn)
    return PostgresSessionStore(dsn=dsn)


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


def get_dlq_store() -> DLQStore:
    global _DLQ_STORE
    if _DLQ_STORE is not None:
        return _DLQ_STORE
    _DLQ_STORE = DLQStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    return _DLQ_STORE


def get_replica_store() -> MemoryReplicaStore:
    global _REPLICA_STORE
    if _REPLICA_STORE is not None:
        return _REPLICA_STORE
    _REPLICA_STORE = MemoryReplicaStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    return _REPLICA_STORE


def get_export_job_store() -> ExportJobStore:
    global _EXPORT_STORE
    if _EXPORT_STORE is not None:
        return _EXPORT_STORE
    _EXPORT_STORE = ExportJobStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    return _EXPORT_STORE


def get_llm_credentials_store() -> LlmCredentialsStore:
    global _LLM_CRED_STORE
    if _LLM_CRED_STORE is not None:
        return _LLM_CRED_STORE
    # Enforce presence of encryption key; fail fast if missing
    try:
        _LLM_CRED_STORE = LlmCredentialsStore(redis_url=_redis_url())
    except Exception as exc:
        LOGGER.error("Failed to initialize LLM credentials store", extra={"error": str(exc)})
        raise
    return _LLM_CRED_STORE


def get_ui_settings_store() -> UiSettingsStore:
    global _UI_SETTINGS_STORE
    if _UI_SETTINGS_STORE is not None:
        return _UI_SETTINGS_STORE
    _UI_SETTINGS_STORE = UiSettingsStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    return _UI_SETTINGS_STORE


# -----------------------------
# Admin memory endpoints (models + list/detail)
# -----------------------------


class AdminMemoryItem(BaseModel):
    id: int
    event_id: str | None
    session_id: str | None
    persona_id: str | None
    tenant: str | None
    role: str | None
    coord: str | None
    request_id: str | None
    trace_id: str | None
    payload: dict[str, Any]
    wal_timestamp: float | None
    created_at: datetime


class AdminMemoryListResponse(BaseModel):
    items: list[AdminMemoryItem]
    next_cursor: int | None


@app.get("/v1/admin/memory", response_model=AdminMemoryListResponse)
async def list_admin_memory(
    request: Request,
    tenant: str | None = Query(None, description="Filter by tenant"),
    persona_id: str | None = Query(None, description="Filter by persona id"),
    role: str | None = Query(None, description="Filter by role (user|assistant|tool)"),
    session_id: str | None = Query(None, description="Filter by session id"),
    universe: str | None = Query(None, description="Filter by universe_id (logical scope)"),
    namespace: str | None = Query(None, description="Filter by memory namespace (e.g., wm, ltm)"),
    q: str | None = Query(None, description="Case-insensitive search in payload JSON text"),
    min_ts: float | None = Query(None, description="Minimum wal_timestamp (epoch seconds)"),
    max_ts: float | None = Query(None, description="Maximum wal_timestamp (epoch seconds)"),
    after: int | None = Query(None, ge=0, description="Return items with database id less than this cursor (paging)"),
    limit: int = Query(50, ge=1, le=200),
    store: Annotated[MemoryReplicaStore, Depends(get_replica_store)] = None,  # type: ignore[assignment]
) -> AdminMemoryListResponse:
    # Require admin scope when auth is enabled
    auth = await authorize_request(request, {
        "tenant": tenant,
        "persona_id": persona_id,
        "role": role,
        "session_id": session_id,
    })
    _require_admin_scope(auth)

    rows = await store.list_memories(
        limit=limit,
        after_id=after,
        tenant=tenant,
        persona_id=persona_id,
        role=role,
        session_id=session_id,
        universe=universe,
        namespace=namespace,
        min_ts=min_ts,
        max_ts=max_ts,
        q=q,
    )
    items = [
        AdminMemoryItem(
            id=r.id,
            event_id=r.event_id,
            session_id=r.session_id,
            persona_id=r.persona_id,
            tenant=r.tenant,
            role=r.role,
            coord=r.coord,
            request_id=r.request_id,
            trace_id=r.trace_id,
            payload=r.payload,
            wal_timestamp=r.wal_timestamp,
            created_at=r.created_at,
        )
        for r in rows
    ]
    next_cursor = items[-1].id if items else None
    return AdminMemoryListResponse(items=items, next_cursor=next_cursor)


@app.get("/v1/admin/memory/{event_id}", response_model=AdminMemoryItem)
async def get_admin_memory_item(
    event_id: str,
    request: Request,
    store: Annotated[MemoryReplicaStore, Depends(get_replica_store)] = None,  # type: ignore[assignment]
) -> AdminMemoryItem:
    auth = await authorize_request(request, {"event_id": event_id})
    _require_admin_scope(auth)
    row = await store.get_by_event_id(event_id)
    if not row:
        raise HTTPException(status_code=404, detail="memory event not found")
    return AdminMemoryItem(
        id=row.id,
        event_id=row.event_id,
        session_id=row.session_id,
        persona_id=row.persona_id,
        tenant=row.tenant,
        role=row.role,
        coord=row.coord,
        request_id=row.request_id,
        trace_id=row.trace_id,
        payload=row.payload,
        wal_timestamp=row.wal_timestamp,
        created_at=row.created_at,
    )


# -----------------------------
# Memory batch/write + delete + export
# -----------------------------


@app.post("/v1/memory/batch")
async def memory_batch_write(
    payload: MemoryBatchPayload,
    request: Request,
    publisher: Annotated[DurablePublisher, Depends(get_publisher)],
) -> dict:
    auth = await authorize_request(request, payload.model_dump())
    _require_admin_scope(auth)

    items = list(payload.items or [])
    max_items = int(os.getenv("MEMORY_BATCH_MAX_ITEMS", "500"))
    if len(items) > max_items:
        raise HTTPException(status_code=413, detail=f"Too many items (>{max_items})")

    soma = SomaBrainClient.get()
    results: list[dict[str, Any]] = []
    wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")

    for m in items:
        try:
            m = dict(m)
            # Ensure idempotency on server side if missing
            if not m.get("idempotency_key"):
                try:
                    m["idempotency_key"] = generate_for_memory_payload(m)
                except Exception:
                    pass
            res = await soma.remember(m)
            results.append({"id": m.get("id"), "ok": True, "result": res})
            try:
                wal_event = {
                    "type": "memory.write",
                    "role": m.get("role"),
                    "session_id": m.get("session_id"),
                    "persona_id": m.get("persona_id"),
                    "tenant": (m.get("metadata") or {}).get("tenant"),
                    "payload": m,
                    "result": {
                        "coord": (res or {}).get("coordinate") or (res or {}).get("coord"),
                        "trace_id": (res or {}).get("trace_id"),
                        "request_id": (res or {}).get("request_id"),
                    },
                    "timestamp": time.time(),
                }
                await publisher.publish(
                    wal_topic,
                    wal_event,
                    dedupe_key=str(m.get("id")) if m.get("id") else None,
                    session_id=str(m.get("session_id")) if m.get("session_id") else None,
                    tenant=(m.get("metadata") or {}).get("tenant"),
                )
            except Exception:
                LOGGER.debug("batch: WAL publish failed", exc_info=True)
        except SomaClientError as exc:
            results.append({"id": m.get("id"), "ok": False, "error": str(exc)})
            # Enqueue for later retry via memory_sync
            try:
                mem_outbox: MemoryWriteOutbox = getattr(app.state, "mem_write_outbox", None)
                if mem_outbox:
                    await mem_outbox.enqueue(
                        payload=m,
                        tenant=(m.get("metadata") or {}).get("tenant"),
                        session_id=m.get("session_id"),
                        persona_id=m.get("persona_id"),
                        idempotency_key=m.get("idempotency_key"),
                        dedupe_key=str(m.get("id")) if m.get("id") else None,
                    )
            except Exception:
                LOGGER.debug("batch: enqueue for retry failed", exc_info=True)
        except Exception as exc:
            results.append({"id": m.get("id"), "ok": False, "error": str(exc)})

    return {"items": results}


@app.delete("/v1/memory/{mem_id}")
async def memory_delete(
    mem_id: str,
    request: Request,
) -> dict:
    auth = await authorize_request(request, {"id": mem_id})
    _require_admin_scope(auth)
    soma = SomaBrainClient.get()
    # Prefer recall_delete that can accept identifiers; fall back to no-op if unsupported
    try:
        res = await soma.recall_delete({"id": mem_id})  # type: ignore[arg-type]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"delete failed: {exc}") from exc
    return {"deleted": True, "result": res}


def _export_semaphore() -> asyncio.Semaphore:
    sem = getattr(app.state, "_export_sem", None)
    if sem is None:
        limit = int(os.getenv("GATEWAY_EXPORT_CONCURRENCY", "2"))
        app.state._export_sem = asyncio.Semaphore(max(1, limit))
        sem = app.state._export_sem
    return sem


@app.get("/v1/memory/export")
async def memory_export(
    request: Request,
    tenant: str | None = Query(None),
    persona_id: str | None = Query(None),
    role: str | None = Query(None),
    session_id: str | None = Query(None),
    universe: str | None = Query(None),
    namespace: str | None = Query(None),
    q: str | None = Query(None),
    min_ts: float | None = Query(None),
    max_ts: float | None = Query(None),
    limit_total: int | None = Query(None, ge=1),
    store: Annotated[MemoryReplicaStore, Depends(get_replica_store)] = None,  # type: ignore[assignment]
):
    auth = await authorize_request(request, {
        "tenant": tenant,
        "persona_id": persona_id,
        "role": role,
        "session_id": session_id,
    })
    _require_admin_scope(auth)

    # Optionally enforce tenant scoping for exports
    if os.getenv("GATEWAY_EXPORT_REQUIRE_TENANT", "false").lower() in {"true", "1", "yes", "on"} and not tenant:
        raise HTTPException(status_code=400, detail="tenant parameter required for export")

    max_rows = int(os.getenv("MEMORY_EXPORT_MAX_ROWS", "100000"))
    hard_limit = min(limit_total or max_rows, max_rows)

    filename = f"memory_export_{int(time.time())}.ndjson"

    async def streamer():
        sent = 0
        after: int | None = None
        page = int(os.getenv("MEMORY_EXPORT_PAGE_SIZE", "1000"))
        while True:
            rows = await store.list_memories(
                limit=min(page, hard_limit - sent),
                after_id=after,
                tenant=tenant,
                persona_id=persona_id,
                role=role,
                session_id=session_id,
                universe=universe,
                namespace=namespace,
                min_ts=min_ts,
                max_ts=max_ts,
                q=q,
            )
            if not rows:
                break
            for r in rows:
                obj = {
                    "id": r.id,
                    "event_id": r.event_id,
                    "session_id": r.session_id,
                    "persona_id": r.persona_id,
                    "tenant": r.tenant,
                    "role": r.role,
                    "coord": r.coord,
                    "request_id": r.request_id,
                    "trace_id": r.trace_id,
                    "wal_timestamp": r.wal_timestamp,
                    "created_at": r.created_at.isoformat(),
                    "payload": r.payload,
                }
                line = json.dumps(obj, ensure_ascii=False) + "\n"
                yield line.encode("utf-8")
                sent += 1
                after = r.id
                if sent >= hard_limit:
                    return

    headers = {
        "Content-Type": "application/x-ndjson",
        "Content-Disposition": f"attachment; filename={filename}",
    }
    # Bound concurrency with a semaphore (simple rate-limiting)
    async def guarded_streamer():
        sem = _export_semaphore()
        async with sem:  # type: ignore
            async for chunk in streamer():
                yield chunk

    return StreamingResponse(guarded_streamer(), headers=headers)


# -----------------------------
# Asynchronous export jobs
# -----------------------------

class ExportJobCreate(BaseModel):
    tenant: str | None = None
    persona_id: str | None = None
    role: str | None = None
    session_id: str | None = None
    universe: str | None = None
    namespace: str | None = None
    q: str | None = None
    min_ts: float | None = None
    max_ts: float | None = None
    limit_total: int | None = Field(None, ge=1)


class ExportJobStatus(BaseModel):
    id: int
    status: str
    row_count: int | None = None
    byte_size: int | None = None
    error: str | None = None
    download_url: str | None = None


def _exports_dir() -> str:
    path = os.getenv("EXPORT_JOBS_DIR", "/tmp/soma_export_jobs")
    os.makedirs(path, exist_ok=True)
    return path


@app.post("/v1/memory/export/jobs", response_model=dict)
async def export_jobs_create(request: Request, payload: ExportJobCreate) -> dict:
    auth = await authorize_request(request, payload.model_dump())
    _require_admin_scope(auth)
    if os.getenv("GATEWAY_EXPORT_REQUIRE_TENANT", "false").lower() in {"true", "1", "yes", "on"} and not payload.tenant:
        raise HTTPException(status_code=400, detail="tenant parameter required for export jobs")

    job_id = await get_export_job_store().create(params=payload.model_dump(), tenant=payload.tenant)
    return {"job_id": job_id, "status": "queued"}


@app.get("/v1/memory/export/jobs/{job_id}", response_model=ExportJobStatus)
async def export_jobs_status(job_id: int, request: Request) -> ExportJobStatus:
    auth = await authorize_request(request, {"job_id": job_id})
    _require_admin_scope(auth)
    job = await get_export_job_store().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    download = None
    if job.status == "completed" and job.file_path:
        download = f"/v1/memory/export/jobs/{job_id}/download"
    return ExportJobStatus(
        id=job.id,
        status=job.status,
        row_count=job.row_count,
        byte_size=job.byte_size,
        error=job.error,
        download_url=download,
    )


@app.get("/v1/memory/export/jobs/{job_id}/download")
async def export_jobs_download(job_id: int, request: Request):
    auth = await authorize_request(request, {"job_id": job_id})
    _require_admin_scope(auth)
    job = await get_export_job_store().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status != "completed" or not job.file_path:
        raise HTTPException(status_code=409, detail="job not completed")

    try:
        fh = open(job.file_path, "rb")
    except FileNotFoundError:
        raise HTTPException(status_code=410, detail="export file no longer available")

    headers = {
        "Content-Type": "application/x-ndjson",
        "Content-Disposition": f"attachment; filename=export_{job_id}.ndjson",
    }

    async def file_streamer():
        try:
            while True:
                chunk = fh.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                fh.close()
            except Exception:
                pass

    return StreamingResponse(file_streamer(), headers=headers)


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


class SessionSummary(BaseModel):
    session_id: str
    persona_id: str | None
    tenant: str | None
    subject: str | None
    issuer: str | None
    scope: str | None
    metadata: dict[str, Any]
    analysis: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SessionEventEntry(BaseModel):
    id: int
    occurred_at: datetime
    payload: dict[str, Any]


class SessionEventsResponse(BaseModel):
    session_id: str
    events: list[SessionEventEntry]
    next_cursor: int | None


    # (AdminMemoryItem/AdminMemoryListResponse moved above their usage)


class MemoryBatchPayload(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list, description="Memory payloads to persist")


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
_EXPORT_STORE: ExportJobStore | None = None


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


def _apply_header_metadata(request: Request, metadata: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
    """Hydrate metadata/persona_id from ingress headers.

    - X-Agent-Profile -> metadata.agent_profile_id
    - X-Universe-Id -> metadata.universe_id
    - X-Persona-Id -> overrides persona_id if body omits it
    Returns (metadata, persona_id_override)
    """
    headers = request.headers
    merged = dict(metadata or {})
    agent_profile = headers.get("x-agent-profile")
    universe_id = headers.get("x-universe-id")
    persona_override = headers.get("x-persona-id")
    if agent_profile and not merged.get("agent_profile_id"):
        merged["agent_profile_id"] = agent_profile
    if universe_id and not merged.get("universe_id"):
        merged["universe_id"] = universe_id
    return merged, persona_override


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
    breaker = _make_circuit_breaker(fail_max=5, reset_timeout=60, expected_exception=httpx.HTTPError)

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
    breaker = _make_circuit_breaker(fail_max=5, reset_timeout=60, expected_exception=httpx.HTTPError)

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

    # Support JWT in cookie when configured (useful for browser sessions)
    if not auth_header:
        cookie_name = os.getenv("GATEWAY_JWT_COOKIE_NAME", "jwt")
        token_cookie = request.cookies.get(cookie_name)
        if token_cookie:
            auth_header = f"Bearer {token_cookie}"

    claims: Dict[str, Any] = {}

    # Enforce JWT only when required. If auth isn't required, ignore malformed/absent tokens.
    if token_required or (auth_header and REQUIRE_AUTH):
        if not auth_header:
            # Audit log for missing token
            LOGGER.warning(
                "Authorization failed – missing header",
                extra={"path": request.url.path, "client": request.client.host},
            )
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            # Do not log raw header/token content to avoid leaking secrets
            LOGGER.warning(
                "Authorization failed – malformed header",
                extra={"path": request.url.path},
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

    # Evaluate OPA policy only when auth is enforced and a policy URL is configured
    if REQUIRE_AUTH and OPA_URL:
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
    publisher: Annotated[DurablePublisher, Depends(get_publisher)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    """Accept a user message and enqueue it for processing."""
    auth_metadata = await authorize_request(request, payload.model_dump())
    base_meta = _apply_auth_metadata(payload.metadata, auth_metadata)
    metadata, persona_hdr = _apply_header_metadata(request, base_meta)

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id or persona_hdr,
        "message": payload.message,
        "attachments": payload.attachments,
        "metadata": metadata,
        "role": "user",
    }

    validate_event(event, "conversation_event")

    # Durable publish: try Kafka then fallback to Outbox
    result = await publisher.publish(
        "conversation.inbound",
        event,
        dedupe_key=event_id,
        session_id=session_id,
        tenant=metadata.get("tenant"),
    )
    if not result.get("published") and not result.get("enqueued"):
        raise HTTPException(status_code=502, detail="Unable to enqueue message")

    # Cache most recent metadata for quick lookup.
    await _cache_session_metadata(cache, session_id, payload.persona_id, metadata)
    await store.append_event(session_id, {"type": "user", **event})

    # Optional write-through to SomaBrain with WAL emission
    if _write_through_enabled():
        async def _write_through() -> None:
            try:
                soma = SomaBrainClient.get()
                GATEWAY_WT_ATTEMPTS.labels("/v1/session/message").inc()
                mem_payload = {
                    "id": event_id,
                    "type": "conversation_event",
                    "role": "user",
                    "content": payload.message,
                    "attachments": payload.attachments or [],
                    "session_id": session_id,
                    "persona_id": event.get("persona_id"),
                    "metadata": {
                        **dict(metadata or {}),
                        "agent_profile_id": (metadata or {}).get("agent_profile_id"),
                        "universe_id": (metadata or {}).get("universe_id") or os.getenv("SOMA_NAMESPACE"),
                    },
                }
                mem_payload["idempotency_key"] = generate_for_memory_payload(mem_payload)
                result = await soma.remember(mem_payload)
                GATEWAY_WT_RESULTS.labels("/v1/session/message", "ok").inc()
                try:
                    wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
                    wal_event = {
                        "type": "memory.write",
                        "role": "user",
                        "session_id": session_id,
                        "persona_id": event.get("persona_id"),
                        "tenant": (metadata or {}).get("tenant"),
                        "payload": mem_payload,
                        "result": {
                            "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                            "trace_id": (result or {}).get("trace_id"),
                            "request_id": (result or {}).get("request_id"),
                        },
                        "timestamp": time.time(),
                    }
                    await publisher.publish(
                        wal_topic,
                        wal_event,
                        dedupe_key=str(mem_payload.get("id")),
                        session_id=session_id,
                        tenant=(metadata or {}).get("tenant"),
                    )
                    GATEWAY_WT_WAL_RESULTS.labels("/v1/session/message", "ok").inc()
                except Exception:
                    LOGGER.debug("Gateway failed to publish memory WAL (user)", exc_info=True)
                    GATEWAY_WT_WAL_RESULTS.labels("/v1/session/message", "error").inc()
            except SomaClientError as exc:
                LOGGER.warning(
                    "Gateway write-through remember failed",
                    extra={"session_id": session_id, "error": str(exc)},
                )
                label = _classify_wt_error(exc)
                GATEWAY_WT_RESULTS.labels("/v1/session/message", label).inc()
                # Enqueue for memory_sync fail-safe
                try:
                    mem_outbox: MemoryWriteOutbox = getattr(app.state, "mem_write_outbox", None)
                    if mem_outbox:
                        await mem_outbox.enqueue(
                            payload=mem_payload,
                            tenant=(mem_payload.get("metadata") or {}).get("tenant"),
                            session_id=session_id,
                            persona_id=event.get("persona_id"),
                            idempotency_key=mem_payload.get("idempotency_key"),
                            dedupe_key=str(mem_payload.get("id")) if mem_payload.get("id") else None,
                        )
                except Exception:
                    LOGGER.debug("Failed to enqueue memory write for retry", exc_info=True)
            except Exception as exc:
                LOGGER.debug("Gateway write-through unexpected error", exc_info=True)
                GATEWAY_WT_RESULTS.labels("/v1/session/message", _classify_wt_error(exc)).inc()

        if _write_through_async():
            asyncio.create_task(_write_through())
        else:
            await _write_through()

    return JSONResponse({"session_id": session_id, "event_id": event_id})


@app.post("/v1/session/action")
async def enqueue_quick_action(
    payload: QuickActionPayload,
    request: Request,
    publisher: Annotated[DurablePublisher, Depends(get_publisher)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> JSONResponse:
    template = QUICK_ACTIONS.get(payload.action)
    if not template:
        raise HTTPException(status_code=400, detail="Unknown action")

    auth_metadata = await authorize_request(request, payload.model_dump())
    base_meta = _apply_auth_metadata(payload.metadata, auth_metadata)
    metadata, persona_hdr = _apply_header_metadata(request, base_meta)

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": payload.persona_id or persona_hdr,
        "message": template,
        "attachments": [],
        "metadata": {**metadata, "source": "quick_action", "action": payload.action},
        "role": "user",
    }

    validate_event(event, "conversation_event")

    await publisher.publish(
        "conversation.inbound",
        event,
        dedupe_key=event_id,
        session_id=session_id,
        tenant=metadata.get("tenant"),
    )
    await _cache_session_metadata(cache, session_id, payload.persona_id, event["metadata"])
    await store.append_event(session_id, {"type": "user", **event})

    # Optional write-through for quick actions as user messages
    if _write_through_enabled():
        async def _write_through() -> None:
            try:
                soma = SomaBrainClient.get()
                GATEWAY_WT_ATTEMPTS.labels("/v1/session/action").inc()
                mem_payload = {
                    "id": event_id,
                    "type": "conversation_event",
                    "role": "user",
                    "content": template,
                    "attachments": [],
                    "session_id": session_id,
                    "persona_id": event.get("persona_id"),
                    "metadata": {
                        **dict(event.get("metadata", {})),
                        "agent_profile_id": (event.get("metadata", {}) or {}).get("agent_profile_id"),
                        "universe_id": (event.get("metadata", {}) or {}).get("universe_id") or os.getenv("SOMA_NAMESPACE"),
                    },
                }
                mem_payload["idempotency_key"] = generate_for_memory_payload(mem_payload)
                result = await soma.remember(mem_payload)
                GATEWAY_WT_RESULTS.labels("/v1/session/action", "ok").inc()
                try:
                    wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
                    wal_event = {
                        "type": "memory.write",
                        "role": "user",
                        "session_id": session_id,
                        "persona_id": event.get("persona_id"),
                        "tenant": (event.get("metadata") or {}).get("tenant"),
                        "payload": mem_payload,
                        "result": {
                            "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                            "trace_id": (result or {}).get("trace_id"),
                            "request_id": (result or {}).get("request_id"),
                        },
                        "timestamp": time.time(),
                    }
                    await publisher.publish(
                        wal_topic,
                        wal_event,
                        dedupe_key=str(mem_payload.get("id")),
                        session_id=session_id,
                        tenant=(event.get("metadata") or {}).get("tenant"),
                    )
                    GATEWAY_WT_WAL_RESULTS.labels("/v1/session/action", "ok").inc()
                except Exception:
                    LOGGER.debug("Gateway failed to publish memory WAL (quick_action)", exc_info=True)
                    GATEWAY_WT_WAL_RESULTS.labels("/v1/session/action", "error").inc()
            except SomaClientError as exc:
                LOGGER.warning(
                    "Gateway write-through remember failed (quick_action)",
                    extra={"session_id": session_id, "error": str(exc)},
                )
                label = _classify_wt_error(exc)
                GATEWAY_WT_RESULTS.labels("/v1/session/action", label).inc()
                # Enqueue for memory_sync fail-safe
                try:
                    mem_outbox: MemoryWriteOutbox = getattr(app.state, "mem_write_outbox", None)
                    if mem_outbox:
                        await mem_outbox.enqueue(
                            payload=mem_payload,
                            tenant=(mem_payload.get("metadata") or {}).get("tenant"),
                            session_id=session_id,
                            persona_id=event.get("persona_id"),
                            idempotency_key=mem_payload.get("idempotency_key"),
                            dedupe_key=str(mem_payload.get("id")) if mem_payload.get("id") else None,
                        )
                except Exception:
                    LOGGER.debug("Failed to enqueue memory write for retry (quick_action)", exc_info=True)
            except Exception as exc:
                LOGGER.debug("Gateway write-through unexpected error (quick_action)", exc_info=True)
                GATEWAY_WT_RESULTS.labels("/v1/session/action", _classify_wt_error(exc)).inc()

        if _write_through_async():
            asyncio.create_task(_write_through())
        else:
            await _write_through()

    return JSONResponse({"session_id": session_id, "event_id": event_id})


@app.get("/v1/sessions", response_model=list[SessionSummary])
async def list_sessions_endpoint(
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
    limit: int = Query(50, ge=1, le=200),
    tenant: str | None = Query(None, description="Filter sessions by tenant identifier"),
) -> list[SessionSummary]:
    envelopes = await store.list_sessions(limit=limit, tenant=tenant)
    summaries: list[SessionSummary] = []
    for envelope in envelopes:
        summaries.append(
            SessionSummary(
                session_id=str(envelope.session_id),
                persona_id=envelope.persona_id,
                tenant=envelope.tenant,
                subject=envelope.subject,
                issuer=envelope.issuer,
                scope=envelope.scope,
                metadata=envelope.metadata,
                analysis=envelope.analysis,
                created_at=envelope.created_at,
                updated_at=envelope.updated_at,
            )
        )
    return summaries


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


@app.get("/v1/sessions/{session_id}/events", response_model=SessionEventsResponse)
async def list_session_events(
    session_id: str,
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
    after: int | None = Query(None, ge=0, description="Return events with database id greater than this cursor"),
    limit: int = Query(100, ge=1, le=500),
) -> SessionEventsResponse:
    events = await store.list_events_after(session_id, after_id=after, limit=limit)
    payload = [
        SessionEventEntry(id=item["id"], occurred_at=item["occurred_at"], payload=item["payload"])
        for item in events
    ]
    next_cursor = payload[-1].id if payload else after
    return SessionEventsResponse(session_id=session_id, events=payload, next_cursor=next_cursor)


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
    # No per-process memory client to close; SomaBrain is accessed directly by services that need it.

    LOGGER.info("Gateway shutdown completed")

    # Stop DLQ refresher
    if hasattr(app.state, "_dlq_refresher_stop"):
        app.state._dlq_refresher_stop.set()

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

    # Replication lag and DLQ depth (best-effort, do not hard-fail health)
    try:
        replica_store = get_replica_store()
        latest_ts = await replica_store.latest_wal_timestamp()
        if latest_ts is not None and latest_ts > 0:
            lag = max(0.0, time.time() - float(latest_ts))
            components["memory_replicator"] = {"status": "ok", "detail": f"lag_seconds={lag:.3f}"}
        else:
            components["memory_replicator"] = {"status": "degraded", "detail": "no WAL observed"}
    except Exception as exc:
        components["memory_replicator"] = {"status": "degraded", "detail": f"{type(exc).__name__}: {exc}"}

    try:
        dlq_topic = f"{os.getenv('MEMORY_WAL_TOPIC', 'memory.wal')}.dlq"
        dlq_store = get_dlq_store()
        depth = await dlq_store.count(topic=dlq_topic)
        # Emit depth to Prometheus for alerting
        try:
            GATEWAY_DLQ_DEPTH.labels(dlq_topic).set(int(depth))
        except Exception:
            pass
        components["memory_dlq"] = {"status": "ok", "detail": f"depth={int(depth)}"}
    except Exception as exc:
        components["memory_dlq"] = {"status": "degraded", "detail": f"{type(exc).__name__}: {exc}"}

    return JSONResponse({"status": overall_status, "components": components})


# -----------------------------
# UI runtime config endpoint
# -----------------------------

@app.get("/ui/config.json")
async def ui_runtime_config() -> JSONResponse:
    """Serve minimal runtime configuration for the Web UI.

    Contains safe, non-secret values the UI can use for wiring.
    """
    payload = {
        "api_base": f"/{API_VERSION}",
        "universe_default": os.getenv("SOMA_NAMESPACE"),
        "namespace_default": os.getenv("SOMA_MEMORY_NAMESPACE", "wm"),
        "features": {
            "write_through": _write_through_enabled(),
            "write_through_async": _write_through_async(),
            "require_auth": REQUIRE_AUTH,
        },
    }
    return JSONResponse(payload)


# -----------------------------
# DLQ depth refresher (background)
# -----------------------------

async def _refresh_dlq_depth_once(topics: list[str]) -> dict[str, int]:
    results: dict[str, int] = {}
    try:
        store = get_dlq_store()
        for topic in topics:
            try:
                depth = int(await store.count(topic=topic))
            except Exception as exc:
                LOGGER.debug("DLQ count failed", extra={"topic": topic, "error": str(exc)})
                continue
            results[topic] = depth
            try:
                GATEWAY_DLQ_DEPTH.labels(topic).set(depth)
            except Exception:
                pass
    except Exception:
        LOGGER.debug("DLQ refresh pass failed", exc_info=True)
    return results


async def _dlq_depth_refresher() -> None:
    poll = max(10.0, _env_float("GATEWAY_DLQ_POLL_SECONDS", 30.0))
    topics = _dlq_topics_from_env()
    # simple jitter to stagger across replicas
    try:
        await asyncio.sleep(min(5.0, poll * 0.1))
    except Exception:
        pass
    while True:
        try:
            if getattr(app.state, "_dlq_refresher_stop", None) and app.state._dlq_refresher_stop.is_set():
                break
            await _refresh_dlq_depth_once(topics)
        except Exception:
            LOGGER.debug("DLQ refresher iteration failed", exc_info=True)
        await asyncio.sleep(poll)


async def _process_export_job(job_id: int) -> None:
    store = get_export_job_store()
    replica = get_replica_store()
    job = await store.get(job_id)
    if not job:
        return
    params = job.params or {}
    # Enforce tenant requirement if configured
    if os.getenv("GATEWAY_EXPORT_REQUIRE_TENANT", "false").lower() in {"true", "1", "yes", "on"} and not (params.get("tenant")):
        await store.mark_failed(job_id, error="tenant required by policy")
        EXPORT_JOBS.labels("rejected").inc()
        return

    dir_path = _exports_dir()
    tmp_path = os.path.join(dir_path, f"job_{job_id}.ndjson.part")
    final_path = os.path.join(dir_path, f"job_{job_id}.ndjson")
    max_rows = int(os.getenv("EXPORT_JOBS_MAX_ROWS", os.getenv("MEMORY_EXPORT_MAX_ROWS", "100000")))
    page = int(os.getenv("EXPORT_JOBS_PAGE_SIZE", os.getenv("MEMORY_EXPORT_PAGE_SIZE", "1000")))
    sent = 0
    after: int | None = None
    rows_written = 0
    bytes_written = 0
    start = time.perf_counter()
    with EXPORT_JOB_SECONDS.time():
        try:
            with open(tmp_path, "wb") as fh:
                while True:
                    batch = await replica.list_memories(
                        limit=min(page, max_rows - sent),
                        after_id=after,
                        tenant=params.get("tenant"),
                        persona_id=params.get("persona_id"),
                        role=params.get("role"),
                        session_id=params.get("session_id"),
                        universe=params.get("universe"),
                        namespace=params.get("namespace"),
                        min_ts=params.get("min_ts"),
                        max_ts=params.get("max_ts"),
                        q=params.get("q"),
                    )
                    if not batch:
                        break
                    for r in batch:
                        obj = {
                            "id": r.id,
                            "event_id": r.event_id,
                            "session_id": r.session_id,
                            "persona_id": r.persona_id,
                            "tenant": r.tenant,
                            "role": r.role,
                            "coord": r.coord,
                            "request_id": r.request_id,
                            "trace_id": r.trace_id,
                            "wal_timestamp": r.wal_timestamp,
                            "created_at": r.created_at.isoformat(),
                            "payload": r.payload,
                        }
                        line = json.dumps(obj, ensure_ascii=False) + "\n"
                        data = line.encode("utf-8")
                        fh.write(data)
                        rows_written += 1
                        bytes_written += len(data)
                        sent += 1
                        after = r.id
                        if sent >= max_rows:
                            break
                    if sent >= max_rows:
                        break
            os.replace(tmp_path, final_path)
            await store.mark_complete(job_id, file_path=final_path, rows=rows_written, byte_size=bytes_written)
            EXPORT_JOBS.labels("ok").inc()
        except Exception as exc:
            try:
                await store.mark_failed(job_id, error=str(exc))
            except Exception:
                pass
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            EXPORT_JOBS.labels("error").inc()


async def _export_jobs_runner() -> None:
    poll = max(1.0, _env_float("EXPORT_JOBS_POLL_SECONDS", 2.0))
    concurrency = max(1, int(os.getenv("EXPORT_JOBS_CONCURRENCY", "1")))
    sem = asyncio.Semaphore(concurrency)
    try:
        await asyncio.sleep(min(1.0, poll * 0.25))
    except Exception:
        pass
    while True:
        try:
            if getattr(app.state, "_export_runner_stop", None) and app.state._export_runner_stop.is_set():
                break
            job_id = await get_export_job_store().claim_next()
            if not job_id:
                await asyncio.sleep(poll)
                continue

            async def _run(jid: int):
                async with sem:  # type: ignore
                    await _process_export_job(jid)

            asyncio.create_task(_run(job_id))
        except Exception:
            LOGGER.debug("Export jobs runner iteration failed", exc_info=True)
            await asyncio.sleep(poll)


async def _gather_health_components_with_memory(
    store: PostgresSessionStore, cache: RedisSessionCache
) -> dict[str, Any]:
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

    # Note: gRPC memory service removed. Health now relies on SomaBrain HTTP check below.

    return {"status": overall_status, "components": components}


app.add_api_route(
    "/health",
    health_check,
    methods=["GET"],
    include_in_schema=False,
)


@app.get("/healthz")
async def healthz(
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
) -> JSONResponse:
    """Consolidated healthz endpoint.

    This endpoint performs lightweight probes to core dependencies (Postgres,
    Redis, Kafka) and to SomaBrain via its HTTP /health endpoint (configurable via
    SOMA_BASE_URL). The overall status is computed from component
    statuses and returned along with per-component details.
    """

    # Start with existing gRPC-based components from helper
    payload = await _gather_health_components_with_memory(store, cache)
    components = payload.get("components", {})
    overall_status = payload.get("status", "ok")

    # Do an HTTP health check against the SomaBrain HTTP target
    http_target = os.getenv("SOMA_BASE_URL", "http://localhost:9696")
    mem_http_status = "degraded"
    mem_http_detail: str | None = None
    try:
        health_url = f"{http_target.rstrip('/')}/health"
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(health_url)
            resp.raise_for_status()
            body = resp.json() if resp.content else {}
            # Some services return {'ok': True} or {'status': 'ok'}
            if isinstance(body, dict) and (body.get("ok") is True or body.get("status") == "ok"):
                mem_http_status = "ok"
            else:
                mem_http_status = "ok" if resp.status_code == 200 else "degraded"
            mem_http_detail = json.dumps(body) if isinstance(body, dict) else None
    except Exception as exc:
        mem_http_status = "down"
        mem_http_detail = f"{type(exc).__name__}: {exc}"

    # Merge SomaBrain HTTP check into components map
    components["somabrain_http"] = {"status": mem_http_status}
    if mem_http_detail:
        components["somabrain_http"]["detail"] = mem_http_detail

    # Recompute overall status conservatively, but do not mark overall "down"
    # solely because SomaBrain HTTP is unavailable in dev; treat that scenario as
    # "degraded" when core deps (postgres, redis, kafka) are healthy.
    down_components = {name for name, c in components.items() if c.get("status") == "down"}
    non_memory_down = {n for n in down_components if n != "somabrain_http"}
    if non_memory_down:
        overall_status = "down"
    elif down_components == {"somabrain_http"}:
        # Only SomaBrain is down => degraded
        if overall_status != "down":
            overall_status = "degraded"
    elif any(c.get("status") == "degraded" for c in components.values()):
        if overall_status != "down":
            overall_status = "degraded"

    return JSONResponse({"status": overall_status, "components": components})


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


# Alias endpoint aligned with roadmap naming
@app.get("/v1/agents/profiles")
async def list_agent_profiles() -> list[ModelProfile]:
    """List agent model profiles (alias for /v1/model-profiles)."""
    return await PROFILE_STORE.list_profiles()


# -----------------------------
# Composite UI settings (single source of truth)
# -----------------------------


def _default_ui_agent() -> dict[str, str]:
    return {
        "agent_profile": "agent0",
        "agent_memory_subdir": "default",
        "agent_knowledge_subdir": "custom",
    }


@app.get("/v1/ui/settings")
async def get_ui_settings() -> dict[str, Any]:
    ui_store = get_ui_settings_store()
    agent_cfg = await ui_store.get()
    if not agent_cfg:
        agent_cfg = _default_ui_agent()

    deployment = APP_SETTINGS.deployment_mode
    profile = await PROFILE_STORE.get("dialogue", deployment)
    profile_payload: dict[str, Any] | None = None
    if profile:
        profile_payload = {
            "role": profile.role,
            "deployment_mode": profile.deployment_mode,
            "model": profile.model,
            "base_url": profile.base_url,
            "temperature": profile.temperature,
            "kwargs": profile.kwargs or {},
        }

    creds = get_llm_credentials_store()
    try:
        providers = await creds.list_providers()
    except Exception:
        providers = []
    llm_info = {p: True for p in providers}

    return {
        "agent": agent_cfg,
        "model_profile": profile_payload,
        "llm_credentials": {"has_secret": llm_info},
        "deployment_mode": deployment,
    }


class UiSettingsPayload(BaseModel):
    agent: Optional[Dict[str, Any]] = None
    model_profile: Optional[Dict[str, Any]] = None
    llm_credentials: Optional[Dict[str, Any]] = None


@app.put("/v1/ui/settings")
async def put_ui_settings(payload: UiSettingsPayload) -> dict[str, Any]:
    if payload.agent:
        agent_cfg = _default_ui_agent() | payload.agent
        await get_ui_settings_store().set(agent_cfg)

    if payload.model_profile:
        mp = payload.model_profile
        deployment = APP_SETTINGS.deployment_mode
        to_save = ModelProfile(
            role="dialogue",
            deployment_mode=deployment,
            model=str(mp.get("model", "")),
            base_url=str(mp.get("base_url", "")),
            temperature=float(mp.get("temperature", 0.2)),
            kwargs=mp.get("kwargs") if isinstance(mp.get("kwargs"), dict) else None,
        )
        await PROFILE_STORE.upsert(to_save)

    if payload.llm_credentials and isinstance(payload.llm_credentials.get("provider"), str):
        provider = payload.llm_credentials.get("provider", "").strip().lower()
        secret = payload.llm_credentials.get("secret", "")
        if provider and secret:
            store = get_llm_credentials_store()
            await store.set(provider, secret)

    return {"ok": True}


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
            publisher: DurablePublisher = app.state.publisher
            await publisher.publish(
                APP_SETTINGS.tool_requests_topic,
                item["payload"],
                dedupe_key=requeue_id,
                tenant=item.get("payload", {}).get("metadata", {}).get("tenant"),
            )
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


# -----------------------------
# DLQ admin endpoints
# -----------------------------


class DLQItem(BaseModel):
    id: int
    topic: str
    event: dict[str, Any]
    error: str | None
    created_at: datetime


@app.get("/v1/admin/dlq/{topic}", response_model=list[DLQItem])
async def list_dlq(
    topic: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    store: Annotated[DLQStore, Depends(get_dlq_store)] = None,  # type: ignore[assignment]
) -> list[DLQItem]:
    auth = await authorize_request(request, {"topic": topic})
    _require_admin_scope(auth)
    items = await store.list_recent(topic=topic, limit=limit)
    return [
        DLQItem(
            id=i.id,
            topic=i.topic,
            event=i.event,
            error=i.error,
            created_at=i.created_at,
        )
        for i in items
    ]


@app.delete("/v1/admin/dlq/{topic}")
async def purge_dlq(
    topic: str,
    request: Request,
    store: Annotated[DLQStore, Depends(get_dlq_store)] = None,  # type: ignore[assignment]
) -> dict:
    auth = await authorize_request(request, {"topic": topic})
    _require_admin_scope(auth)
    deleted = await store.purge(topic=topic)
    return {"status": "purged", "deleted": int(deleted)}


@app.post("/v1/admin/dlq/{topic}/{item_id}/reprocess")
async def reprocess_dlq_item(
    topic: str,
    item_id: int,
    request: Request,
    store: Annotated[DLQStore, Depends(get_dlq_store)] = None,  # type: ignore[assignment]
    publisher: Annotated[DurablePublisher, Depends(get_publisher)] = None,  # type: ignore[assignment]
) -> dict:
    """Replay a DLQ message back to its original topic (typically memory.wal).

    By convention, topics ending with ".dlq" are mapped back to their base
    topic for replay. On success, the DLQ row is deleted.
    """
    auth = await authorize_request(request, {"topic": topic, "id": item_id})
    _require_admin_scope(auth)

    item = await store.get_by_id(id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")

    target = topic[:-4] if topic.endswith(".dlq") else topic
    payload = dict(item.event)

    # Compute reasonable dedupe/session/tenant for durable publish
    dedupe_key = None
    try:
        dedupe_key = (
            payload.get("payload", {}).get("id")
            or payload.get("event_id")
            or payload.get("id")
        )
    except Exception:
        dedupe_key = None

    session_id = payload.get("session_id") or (payload.get("payload", {}) or {}).get("session_id")
    tenant = (
        payload.get("tenant")
        or (payload.get("metadata", {}) or {}).get("tenant")
        or (payload.get("payload", {}).get("metadata", {}) if isinstance(payload.get("payload"), dict) else {}).get("tenant")
    )

    result = await publisher.publish(
        target,
        payload,
        dedupe_key=str(dedupe_key) if dedupe_key else None,
        session_id=str(session_id) if session_id else None,
        tenant=str(tenant) if tenant else None,
    )
    # Delete DLQ entry upon successful publish or enqueue
    if result.get("published") or result.get("enqueued"):
        await store.delete_by_id(id=item_id)
    return {"status": "reprocessed", "target": target, "published": bool(result.get("published")), "enqueued": bool(result.get("enqueued"))}


# -----------------------------
# LLM credentials management
# -----------------------------

class LlmCredPayload(BaseModel):
    provider: str
    secret: str


@app.post("/v1/llm/credentials")
async def upsert_llm_credentials(
    payload: LlmCredPayload,
    request: Request,
    store: Annotated[LlmCredentialsStore, Depends(get_llm_credentials_store)] = None,  # type: ignore[assignment]
) -> dict:
    # Require admin scope when auth is enabled
    auth = await authorize_request(request, payload.model_dump())
    _require_admin_scope(auth)
    provider = payload.provider.strip().lower()
    if not provider or not payload.secret:
        raise HTTPException(status_code=400, detail="provider and secret required")
    await store.set(provider, payload.secret)
    # Broadcast config update so workers may refresh
    try:
        publisher: DurablePublisher = app.state.publisher
        await publisher.publish("config_updates", {"type": "llm.credentials.updated", "provider": provider})
    except Exception:
        LOGGER.debug("Failed to publish config update (llm credentials)", exc_info=True)
    return {"ok": True}


def _internal_token_ok(request: Request) -> bool:
    expected = os.getenv("GATEWAY_INTERNAL_TOKEN")
    if not expected:
        return False
    got = request.headers.get("x-internal-token") or request.headers.get("X-Internal-Token")
    return bool(got and got == expected)


@app.get("/v1/llm/credentials/{provider}")
async def get_llm_credentials(provider: str, request: Request, store: Annotated[LlmCredentialsStore, Depends(get_llm_credentials_store)] = None) -> dict:  # type: ignore[assignment]
    # Only allow internal calls with X-Internal-Token; do not expose via normal auth
    if not _internal_token_ok(request):
        raise HTTPException(status_code=403, detail="forbidden")
    provider = (provider or "").strip().lower()
    if not provider:
        raise HTTPException(status_code=400, detail="missing provider")
    secret = await store.get(provider)
    if not secret:
        raise HTTPException(status_code=404, detail="not found")
    return {"provider": provider, "secret": secret}
