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
import secrets
from typing import Annotated, Any, AsyncIterator, Dict, Optional, List

import httpx

# Third‑party imports (alphabetical by top‑level package name)
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    File,
    UploadFile,
    Form,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_client import Counter, Gauge, Histogram, start_http_server, REGISTRY
from pydantic import BaseModel, Field, field_validator
from jsonschema import ValidationError
from werkzeug.utils import secure_filename
import hashlib
from pathlib import Path
import subprocess
import socket
import contextlib
from urllib.parse import urlencode
import copy

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
from python.helpers.settings import convert_out as ui_convert_out, get_default_settings as ui_get_defaults
from python.helpers.dotenv import get_dotenv_value
from services.common.api_key_store import ApiKeyStore, RedisApiKeyStore
from services.common.dlq_store import DLQStore
from services.common.event_bus import iterate_topic, KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.memory_replica_store import MemoryReplicaStore
from services.common.audit_store import AuditStore as _AuditStore, from_env as audit_store_from_env
from services.common.attachments_store import AttachmentsStore
from services.common.memory_replica_store import ensure_schema as ensure_replica_schema
from services.common.memory_write_outbox import MemoryWriteOutbox
from services.common.export_job_store import ExportJobStore, ensure_schema as ensure_export_jobs_schema
from services.common.model_profiles import ModelProfile, ModelProfileStore
from services.common.ui_settings_store import UiSettingsStore
from services.common.ui_settings_store import UiSettingsStore
from services.common.openfga_client import OpenFGAClient
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.memory_write_outbox import MemoryWriteOutbox, ensure_schema as ensure_mw_outbox_schema
from services.common.llm_credentials_store import LlmCredentialsStore
from services.common.publisher import DurablePublisher
from services.common.requeue_store import RequeueStore
from services.common.schema_validator import validate_event
from services.common.session_repository import PostgresSessionStore, RedisSessionCache, ensure_schema as ensure_session_schema
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry_store import TelemetryStore
from services.common.tracing import setup_tracing
from services.common.vault_secrets import load_kv_secret
from services.common.idempotency import generate_for_memory_payload
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from services.common.memory_write_outbox import MemoryWriteOutbox
from services.common.slm_client import SLMClient, ChatMessage

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

# Global exception handler to surface unexpected errors (helps during dev)
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
    try:
        LOGGER.error(
            "Unhandled exception",
            exc_info=True,
            extra={
                "path": str(getattr(request, "url", "")),
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
    except Exception:
        pass
    return JSONResponse({"detail": "internal error", "error_type": type(exc).__name__}, status_code=500)

# Defer mounting the Web UI to later in the file to ensure explicit routes like
# /ui/config.json take precedence over the static mount.


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

# Include UI proxy routes to provide legacy-compatible UI endpoints like /v1/ui/poll
# This allows the Web UI to aggregate sessions and events via the gateway process.
# If the router import fails (older image/build), we install a safe fallback below.
try:
    from services.ui_proxy.routes import router as ui_proxy_router  # type: ignore

    app.include_router(ui_proxy_router)
except Exception as _e:  # pragma: no cover - optional wiring for local/dev
    # If UI proxy is not available at import time, log and fall back to inline endpoints below.
    logging.getLogger(__name__).warning("UI proxy router import failed, will install inline fallback endpoints: %s", _e)

# Install inline fallback implementations for /v1/ui/poll and /v1/ui/message if not already registered
def _route_exists(path: str, methods: set[str]) -> bool:
    try:
        for r in getattr(app, "routes", []):
            r_path = getattr(r, "path", None)
            r_methods = set(getattr(r, "methods", set()) or set())
            if r_path == path and methods.issubset(r_methods):
                return True
    except Exception:
        pass
    return False

try:
    from services.ui_proxy.service import PollAggregator, UiMessageService  # type: ignore
    from services.ui_proxy.client import GatewayClient  # type: ignore
except Exception:
    PollAggregator = None  # type: ignore
    UiMessageService = None  # type: ignore
    GatewayClient = None  # type: ignore

if PollAggregator and GatewayClient and not _route_exists("/v1/ui/poll", {"POST"}):
    async def _ui_poll_fallback(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            body = {}
        # Use default internal client; avoid request.base_url which may be host-mapped
        client = GatewayClient()
        aggregator = PollAggregator(client)
        payload = await aggregator.poll(body)
        return JSONResponse(payload)

    app.add_api_route("/v1/ui/poll", _ui_poll_fallback, methods=["POST"])

if UiMessageService and GatewayClient and not _route_exists("/v1/ui/message", {"POST"}):
    async def _ui_message_fallback(request: Request) -> JSONResponse:
        # Use default internal client; avoid request.base_url which may be host-mapped
        client = GatewayClient()
        service = UiMessageService()
        payload = await service.handle_request(request, client)
        return JSONResponse(payload)

    app.add_api_route("/v1/ui/message", _ui_message_fallback, methods=["POST"])

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

# Upload metrics
GATEWAY_UPLOADS = _get_or_create_counter(
    "gateway_uploads_total",
    "Gateway file upload outcomes",
    labelnames=("result",),  # ok|blocked|error
)
GATEWAY_UPLOAD_SECONDS = _get_or_create_histogram(
    "gateway_upload_seconds",
    "Gateway file upload processing time (seconds)",
)

# Antivirus metrics (optional)
GATEWAY_AV_SCANS = _get_or_create_counter(
    "gateway_av_scans_total",
    "Gateway antivirus scan results",
    labelnames=("result",),  # clean|infected|error|disabled
)

# Janitor metrics
JANITOR_FILES_DELETED = _get_or_create_counter(
    "gateway_uploads_janitor_files_deleted_total",
    "Total files deleted by uploads janitor",
)
JANITOR_ERRORS = _get_or_create_counter(
    "gateway_uploads_janitor_errors_total",
    "Total errors encountered by uploads janitor",
)
JANITOR_LAST_RUN = _get_or_create_gauge(
    "gateway_uploads_janitor_last_run_timestamp",
    "Last uploads janitor run timestamp (seconds since epoch)",
)


def _uploads_root() -> Path:
    # Respect global file-saving disable switch; never create directories when disabled
    if os.getenv("DISABLE_FILE_SAVING", "true").lower() in {"true", "1", "yes", "on"} or os.getenv(
        "GATEWAY_DISABLE_FILE_SAVING", "true"
    ).lower() in {"true", "1", "yes", "on"}:
        return Path("/")  # dummy path; callers should have short-circuited already
    base = os.getenv("GATEWAY_UPLOAD_DIR", "/git/agent-zero/tmp/uploads")
    p = Path(base)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        LOGGER.debug("Failed to ensure uploads root exists", exc_info=True)
    return p


def _csv_env(name: str) -> set[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _upload_limits() -> tuple[int, int]:
    # Prefer runtime overlays saved via UI settings; fall back to env
    cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
    try:
        max_mb = float(cfg.get("uploads_max_mb", os.getenv("GATEWAY_UPLOAD_MAX_MB", "25")))
    except Exception:
        max_mb = 25.0
    try:
        max_files = int(cfg.get("uploads_max_files", os.getenv("GATEWAY_UPLOAD_MAX_FILES", "10")))
    except Exception:
        max_files = 10
    return int(max_mb * 1024 * 1024), max_files


def _mime_allowed(mime: str) -> bool:
    # Prefer overlays
    mime = (mime or "").lower() or "application/octet-stream"
    cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
    raw_allowed = cfg.get("uploads_allowed_mime") if isinstance(cfg, dict) else None
    raw_denied = cfg.get("uploads_denied_mime") if isinstance(cfg, dict) else None
    def _parse_list(val: Any) -> set[str]:
        if not isinstance(val, str) or not val.strip():
            return set()
        items = []
        for part in val.replace("\n", ",").split(","):
            part = part.strip()
            if part:
                items.append(part.lower())
        return set(items)
    allowed = _parse_list(raw_allowed) or _csv_env("GATEWAY_UPLOAD_ALLOWED_MIME")
    denied = _parse_list(raw_denied) or _csv_env("GATEWAY_UPLOAD_DENIED_MIME")
    if denied and mime in denied:
        return False
    if allowed and mime not in allowed:
        return False
    return True


def _clamav_enabled() -> bool:
    # Prefer overlays from settings
    cfg = getattr(app.state, "av_cfg", {}) if hasattr(app, "state") else {}
    if isinstance(cfg, dict) and cfg.get("av_enabled") is not None:
        return bool(cfg.get("av_enabled"))
    return os.getenv("CLAMAV_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def _clamav_strict() -> bool:
    cfg = getattr(app.state, "av_cfg", {}) if hasattr(app, "state") else {}
    if isinstance(cfg, dict) and cfg.get("av_strict") is not None:
        return bool(cfg.get("av_strict"))
    return False


async def _clamav_scan(path: Path) -> tuple[str, str]:
    """Scan a file on disk with ClamAV (legacy path-based). Prefer _clamav_scan_bytes."""
    try:
        # Try python-clamd (optional dependency)
        try:
            import clamd  # type: ignore

            host = os.getenv("CLAMAV_HOST", "clamav")
            port = int(os.getenv("CLAMAV_PORT", "3310"))
            cd = clamd.ClamdNetworkSocket(host=host, port=port)
            resp = await asyncio.to_thread(cd.scan, str(path))
            # resp like {"/path": ("OK"|"FOUND"|"ERROR", "detail")}
            _, (status, detail) = next(iter(resp.items()))
            if status == "OK":
                return "clean", detail or ""
            if status == "FOUND":
                return "infected", detail or "infected"
            return "error", detail or status
        except Exception:
            pass

        # Fallback to clamdscan CLI
        try:
            proc = await asyncio.create_subprocess_exec(
                "clamdscan", "--no-summary", str(path),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            out = (stdout or b"").decode("utf-8", errors="ignore").strip()
            err = (stderr or b"").decode("utf-8", errors="ignore").strip()
            if proc.returncode == 0:
                return "clean", out
            if proc.returncode == 1:
                return "infected", out
            return "error", err or out or str(proc.returncode)
        except FileNotFoundError:
            return "error", "clamdscan not installed"
    except Exception as exc:
        return "error", str(exc)


async def _clamav_scan_bytes(data: bytes) -> tuple[str, str]:
    """Scan bytes in-memory using clamd INSTREAM.

    Returns (result, detail): result in {clean, infected, error}.
    """
    try:
        try:
            import clamd  # type: ignore
            host = os.getenv("CLAMAV_HOST", "clamav")
            port = int(os.getenv("CLAMAV_PORT", "3310"))
            cd = clamd.ClamdNetworkSocket(host=host, port=port)
            # clamd expects a file-like object; wrap bytes
            import io
            bio = io.BytesIO(data)
            resp = await asyncio.to_thread(cd.instream, bio)
            # resp like {'stream': ('OK'|'FOUND'|'ERROR', detail)}
            _, (status, detail) = next(iter(resp.items()))
            if status == "OK":
                return "clean", detail or ""
            if status == "FOUND":
                return "infected", detail or "infected"
            return "error", detail or status
        except Exception as exc:
            return "error", str(exc)
    except Exception as exc:
        return "error", str(exc)

# -----------------------------
# Kafka debug (dev-only admin) endpoint
# -----------------------------

@app.get("/v1/admin/kafka/status")
async def kafka_status(topic: str = Query(...), group: str = Query(...)) -> dict[str, Any]:
    """Return partition end offsets and group committed offsets for a topic.

    Development aid to diagnose publish/consume mismatches without external tools.
    """
    try:
        from aiokafka import AIOKafkaConsumer  # type: ignore
        from aiokafka.structs import TopicPartition  # type: ignore
    except Exception as exc:  # pragma: no cover - env dependent
        raise HTTPException(status_code=500, detail=f"aiokafka unavailable: {exc}")

    ks = _kafka_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=ks.bootstrap_servers,
        group_id=group,
        enable_auto_commit=False,
        security_protocol=ks.security_protocol,
        sasl_mechanism=ks.sasl_mechanism,
        sasl_plain_username=ks.sasl_username,
        sasl_plain_password=ks.sasl_password,
    )
    await consumer.start()
    try:
        # partitions_for_topic returns a set synchronously once metadata is available
        parts = consumer.partitions_for_topic(topic) or set()
        tps = [TopicPartition(topic, p) for p in sorted(parts)]
        end_offsets = await consumer.end_offsets(tps) if tps else {}
        committed = {tp: (await consumer.committed(tp)) for tp in tps}
        return {
            "topic": topic,
            "group": group,
            "bootstrap": ks.bootstrap_servers,
            "partitions": [
                {
                    "partition": tp.partition,
                    "committed": int(committed.get(tp) or -1),
                    "end": int(end_offsets.get(tp) or -1),
                    "lag": max(0, int((end_offsets.get(tp) or 0) - (committed.get(tp) or 0))),
                }
                for tp in tps
            ],
        }
    finally:
        await consumer.stop()


@app.post("/v1/admin/kafka/seek_to_end")
async def kafka_seek_to_end(topic: str = Query(...), group: str = Query(...)) -> dict[str, Any]:
    """DEV‑only: set the consumer group's committed offsets to end for a topic."""
    try:
        from aiokafka import AIOKafkaConsumer  # type: ignore
        from aiokafka.structs import TopicPartition  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"aiokafka unavailable: {exc}")

    ks = _kafka_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=ks.bootstrap_servers,
        group_id=group,
        enable_auto_commit=False,
        security_protocol=ks.security_protocol,
        sasl_mechanism=ks.sasl_mechanism,
        sasl_plain_username=ks.sasl_username,
        sasl_plain_password=ks.sasl_password,
        auto_offset_reset="latest",
    )
    await consumer.start()
    try:
        parts = consumer.partitions_for_topic(topic) or set()
        tps = [TopicPartition(topic, p) for p in sorted(parts)]
        if not tps:
            return {"topic": topic, "group": group, "updated": [], "detail": "no partitions"}
        await consumer.assign(tps)
        await consumer.seek_to_end(*tps)
        offsets = {}
        for tp in tps:
            pos = await consumer.position(tp)
            offsets[tp] = pos
        # Commit the end positions
        await consumer.commit(offsets=offsets)
        return {
            "topic": topic,
            "group": group,
            "updated": [
                {"partition": tp.partition, "committed": int(offsets.get(tp) or -1)} for tp in tps
            ],
        }
    finally:
        await consumer.stop()

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

    # Initialize export jobs store and schema, then start worker (skip local-file exports entirely)
    if False:
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

    # Ensure UI settings schema exists (best-effort)
    try:
        await get_ui_settings_store().ensure_schema()
    except Exception:
        LOGGER.debug("UI settings schema ensure failed", exc_info=True)

    # Load runtime overlays for uploads/antivirus from stored UI settings
    try:
        doc = await get_ui_settings_store().get()
        if isinstance(doc, dict):
            app.state.uploads_cfg = dict(doc.get("uploads") or {})
            app.state.av_cfg = dict(doc.get("antivirus") or {})
        # Enforce uploads disabled when file saving is disabled
        if _file_saving_disabled():
            cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
            if isinstance(cfg, dict):
                cfg["uploads_enabled"] = False
                app.state.uploads_cfg = cfg
    except Exception:
        LOGGER.debug("Failed to load UI settings overlays at startup", exc_info=True)

    # Ensure memory replica schema exists (best-effort)
    try:
        store = get_replica_store()
        await ensure_replica_schema(store)
    except Exception:
        LOGGER.debug("Memory replica schema ensure failed", exc_info=True)

    # Ensure attachments schema exists (best-effort)
    try:
        await get_attachments_store().ensure_schema()
    except Exception:
        LOGGER.debug("Attachments store schema ensure failed", exc_info=True)

    # Ensure audit schema exists (best-effort)
    try:
        await get_audit_store().ensure_schema()
    except Exception:
        LOGGER.debug("Audit store schema ensure failed", exc_info=True)

    # Ensure session schema exists so SSE/poll can function even before worker runs
    try:
        await ensure_session_schema(get_session_store())
    except Exception:
        LOGGER.debug("Session schema ensure failed", exc_info=True)


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


def _file_saving_disabled() -> bool:
    """Global guard to disable any on-disk writes from the gateway by default.

    Controlled via either DISABLE_FILE_SAVING or GATEWAY_DISABLE_FILE_SAVING env vars.
    Defaults to True (disabled) to honor strict no-file-saving mode.
    """
    # This flag disables local filesystem writes, not database persistence.
    return _flag_truthy(os.getenv("DISABLE_FILE_SAVING", "true"), True) or _flag_truthy(
        os.getenv("GATEWAY_DISABLE_FILE_SAVING", "true"), True
    )


# -----------------------------
# Attachments store accessor
# -----------------------------

_ATTACHMENTS_STORE: AttachmentsStore | None = None


def get_attachments_store() -> AttachmentsStore:
    global _ATTACHMENTS_STORE
    if _ATTACHMENTS_STORE is None:
        _ATTACHMENTS_STORE = AttachmentsStore(dsn=os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn))
    return _ATTACHMENTS_STORE


# -----------------------------
# Central CSRF token issuance (browser flow)
# -----------------------------


@app.get("/v1/csrf")
async def issue_csrf_token(request: Request) -> JSONResponse:
    """Issue a CSRF token and set the matching cookie for double‑submit validation.

    - Returns JSON: {"token": <token>} for the SPA to attach in X-CSRF-Token.
    - Sets cookie named by GATEWAY_CSRF_COOKIE_NAME (default: csrf_token).
    - Cookie attributes: SameSite=Lax, Secure when HTTPS or GATEWAY_COOKIE_SECURE=true.

    Gateway middleware enforces CSRF only when enabled via GATEWAY_CSRF_ENABLED
    and primarily for cookie-authenticated browser flows.
    """
    token = secrets.token_urlsafe(32)
    cookie_name = os.getenv("GATEWAY_CSRF_COOKIE_NAME", "csrf_token")
    same_site = os.getenv("GATEWAY_CSRF_COOKIE_SAMESITE", "Lax")
    # Treat forwarded https as secure in typical reverse-proxy deployments
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    secure_env = os.getenv("GATEWAY_COOKIE_SECURE", "false").lower() in {"true", "1", "yes", "on"}
    secure = secure_env or request.url.scheme == "https" or forwarded_proto == "https"

    resp = JSONResponse({"token": token})
    http_only_env = os.getenv("GATEWAY_CSRF_COOKIE_HTTPONLY", "true").lower() in {"true", "1", "yes", "on"}
    resp.set_cookie(
        key=cookie_name,
        value=token,
        httponly=http_only_env,  # SPA reads token from JSON body; cookie can be HttpOnly in hardened setups
        secure=secure,
        samesite=same_site,
        path="/",
    )
    return resp

_API_KEY_STORE: Optional[ApiKeyStore] = None
_DLQ_STORE: Optional[DLQStore] = None
_REPLICA_STORE: Optional[MemoryReplicaStore] = None
_LLM_CRED_STORE: Optional[LlmCredentialsStore] = None
_UI_SETTINGS_STORE: Optional[UiSettingsStore] = None
_UI_SETTINGS_STORE: Optional[UiSettingsStore] = None


@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    if "X-API-Version" not in response.headers:
        response.headers["X-API-Version"] = API_VERSION
    return response


# -----------------------------
# Security headers (env-driven)
# -----------------------------

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # X-Content-Type-Options
    response.headers.setdefault("X-Content-Type-Options", "nosniff")

    # X-Frame-Options
    if os.getenv("GATEWAY_FRAME_OPTIONS", "DENY").upper() in {"DENY", "SAMEORIGIN"}:
        response.headers.setdefault("X-Frame-Options", os.getenv("GATEWAY_FRAME_OPTIONS", "DENY").upper())

    # Referrer-Policy
    response.headers.setdefault("Referrer-Policy", os.getenv("GATEWAY_REFERRER_POLICY", "no-referrer"))

    # Permissions-Policy (string, optional)
    perm = os.getenv("GATEWAY_PERMISSIONS_POLICY")
    if perm:
        response.headers.setdefault("Permissions-Policy", perm)

    # Content-Security-Policy (string, optional)
    csp = os.getenv("GATEWAY_CSP")
    if csp:
        response.headers.setdefault("Content-Security-Policy", csp)

    # HSTS (enable only when TLS is terminated upstream)
    if os.getenv("GATEWAY_HSTS", "false").lower() in {"true", "1", "yes", "on"}:
        max_age = os.getenv("GATEWAY_HSTS_MAX_AGE", "15552000")  # ~180 days
        inc_sub = "; includeSubDomains" if os.getenv("GATEWAY_HSTS_INCLUDE_SUBDOMAINS", "true").lower() in {"true", "1", "yes", "on"} else ""
        preload = "; preload" if os.getenv("GATEWAY_HSTS_PRELOAD", "false").lower() in {"true", "1", "yes", "on"} else ""
        response.headers.setdefault("Strict-Transport-Security", f"max-age={max_age}{inc_sub}{preload}")

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


def _session_claims_from_cookie(request: Request) -> dict[str, Any] | None:
    """Decode the session JWT from cookie if present and valid.

    Only verifies signature/exp using the configured JWT_SECRET or public key.
    """
    try:
        cookie_name = os.getenv("GATEWAY_JWT_COOKIE_NAME", "jwt")
        token = request.cookies.get(cookie_name)
        if not token:
            return None
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        key = None
        if alg and alg.startswith("HS"):
            key = JWT_SECRET
        elif alg and (alg.startswith("RS") or alg.startswith("ES")):
            key = JWT_PUBLIC_KEY
        if not key:
            # Re-read env in case tests or runtime set it after import
            env_secret = os.getenv("GATEWAY_JWT_SECRET")
            env_pub = os.getenv("GATEWAY_JWT_PUBLIC_KEY")
            key = JWT_SECRET or env_secret or JWT_PUBLIC_KEY or env_pub
        if not key:
            return None
        claims = jwt.decode(token, key=key, algorithms=[alg] if alg else (JWT_ALGORITHMS or ["HS256"]))
        return dict(claims)
    except Exception:
        return None


@app.middleware("http")
async def ui_auth_guard(request: Request, call_next):
    """Redirect unauthenticated users to /login for top-level UI routes when auth is required.

    - Allows API paths (/v1/...), auth endpoints, docs, and static assets to pass through.
    - When OIDC is enabled or REQUIRE_AUTH is true, and request is for '/', '/ui', '/ui/', or '/ui/index.html',
      redirect to /login if no valid session cookie is present.
    """
    path = request.url.path
    if path.startswith("/v1/auth") or path.startswith("/v1/csrf") or path.startswith("/openapi") or path.startswith("/docs"):
        return await call_next(request)

    need_auth = _oidc_enabled() or REQUIRE_AUTH
    if need_auth:
        # Permit visiting /login and its assets without auth
        if path == "/login" or path.startswith("/ui/login"):
            return await call_next(request)
        # Guard common UI entry points
        if path in {"/", "/ui", "/ui/", "/ui/index", "/ui/index.html"}:
            if _session_claims_from_cookie(request) is None:
                return RedirectResponse(url="/login")
    return await call_next(request)


# -----------------------------
# Minimal Login UI and OIDC login/logout
# -----------------------------

def _oidc_enabled() -> bool:
    return os.getenv("OIDC_ENABLED", "false").lower() in {"true", "1", "yes", "on"}


def _oidc_client() -> dict[str, Any]:
    return {
        "issuer": os.getenv("OIDC_ISSUER", os.getenv("GOOGLE_ISSUER", "https://accounts.google.com")),
        "client_id": os.getenv("OIDC_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID", "")),
        "client_secret": os.getenv("OIDC_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET", "")),
        "redirect_uri": os.getenv("OIDC_REDIRECT_URI", os.getenv("GATEWAY_BASE_URL", "http://localhost:8080").rstrip("/") + "/v1/auth/callback"),
        "scopes": os.getenv("OIDC_SCOPES", "openid email profile"),
        "provider": os.getenv("OIDC_PROVIDER", "google"),
    }


async def _oidc_discovery() -> dict[str, Any]:
    global _OIDC_DISCOVERY_CACHE, _OIDC_DISCOVERY_TS
    if not _oidc_enabled():
        return {}
    cli = _oidc_client()
    issuer = str(cli["issuer"]).rstrip("/")
    now = time.time()
    # Cache discovery for 10 minutes
    if _OIDC_DISCOVERY_CACHE and _OIDC_DISCOVERY_TS and (now - _OIDC_DISCOVERY_TS) < 600:
        return _OIDC_DISCOVERY_CACHE
    url = issuer + "/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _OIDC_DISCOVERY_CACHE = resp.json()
        _OIDC_DISCOVERY_TS = now
        return _OIDC_DISCOVERY_CACHE


def _jwt_cookie_flags(request: Request) -> dict[str, Any]:
    same_site = os.getenv("GATEWAY_JWT_COOKIE_SAMESITE", os.getenv("GATEWAY_CSRF_COOKIE_SAMESITE", "Lax"))
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    secure_env = os.getenv("GATEWAY_COOKIE_SECURE", "false").lower() in {"true", "1", "yes", "on"}
    secure = secure_env or request.url.scheme == "https" or forwarded_proto == "https"
    http_only_env = os.getenv("GATEWAY_JWT_COOKIE_HTTPONLY", "true").lower() in {"true", "1", "yes", "on"}
    path = os.getenv("GATEWAY_JWT_COOKIE_PATH", "/")
    domain = os.getenv("GATEWAY_JWT_COOKIE_DOMAIN")
    max_age = os.getenv("GATEWAY_JWT_COOKIE_MAX_AGE")
    try:
        max_age_int = int(max_age) if max_age else None
    except Exception:
        max_age_int = None
    return {
        "httponly": http_only_env,
        "secure": secure,
        "samesite": same_site,
        "path": path,
        "domain": domain,
        "max_age": max_age_int,
    }


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    # If already authenticated, go to main UI
    if _session_claims_from_cookie(request):
        # Route authenticated users to the root UI entrypoint
        return RedirectResponse(url="/")
    enabled = _oidc_enabled()
    provider = _oidc_client().get("provider") or "SSO"
    # Prefer serving the repo's webui/login.html if present
    try:
        ui_dir = (Path(__file__).resolve().parents[2] / "webui").resolve()
        login_file = ui_dir / "login.html"
        if login_file.exists():
            content = login_file.read_text(encoding="utf-8")
            # Ensure the button points to our OIDC start if the template uses a placeholder
            content = content.replace("/auth/login", "/v1/auth/login")
            return HTMLResponse(content=content)
    except Exception:
        LOGGER.debug("Failed to serve webui/login.html; falling back to inline", exc_info=True)
    btn = "<button disabled>SSO not configured</button>" if not enabled else f"<a href=\"/v1/auth/login?provider={provider}\"><button>Continue with {provider.title()}</button></a>"
    html = f"""
    <html><head><title>Sign in</title></head><body>
    <h1>Sign in</h1>
    <p>{'Use your organization SSO to continue.' if enabled else 'Single Sign-On is not configured.'}</p>
    <div>{btn}</div>
    </body></html>
    """
    return HTMLResponse(content=html)


@app.get("/v1/auth/login")
async def auth_login(request: Request, provider: str = "google") -> RedirectResponse:
    if not _oidc_enabled():
        raise HTTPException(status_code=503, detail="OIDC not enabled")
    disc = await _oidc_discovery()
    cli = _oidc_client()
    auth_url = disc.get("authorization_endpoint")
    if not auth_url:
        raise HTTPException(status_code=500, detail="OIDC discovery failed")
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    # Cache state+nonce to validate callback
    try:
        cache = get_session_cache()
        await cache.set(f"oidc:state:{state}", {"nonce": nonce}, ex=300)
    except Exception:
        LOGGER.debug("Failed to save OIDC state in cache", exc_info=True)
    params = {
        "response_type": "code",
        "client_id": cli["client_id"],
        "redirect_uri": cli["redirect_uri"],
        "scope": cli["scopes"],
        "state": state,
        "nonce": nonce,
    }
    url = auth_url + ("?" + urlencode(params))
    return RedirectResponse(url)


@app.get("/v1/auth/callback")
async def auth_callback(request: Request, code: str | None = None, state: str | None = None) -> Response:
    if not _oidc_enabled():
        raise HTTPException(status_code=503, detail="OIDC not enabled")
    if not code or not state:
        raise HTTPException(status_code=400, detail="missing code/state")
    disc = await _oidc_discovery()
    token_url = disc.get("token_endpoint")
    if not token_url:
        raise HTTPException(status_code=500, detail="OIDC discovery incomplete")
    cli = _oidc_client()
    # Validate state and retrieve nonce
    nonce_expected = None
    try:
        cache = get_session_cache()
        item = await cache.get(f"oidc:state:{state}")
        if isinstance(item, dict):
            nonce_expected = item.get("nonce")
        await cache.delete(f"oidc:state:{state}")
    except Exception:
        LOGGER.debug("Failed to read OIDC state from cache", exc_info=True)
    if not nonce_expected:
        raise HTTPException(status_code=400, detail="state expired or invalid")

    # Exchange code for tokens
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cli["redirect_uri"],
        "client_id": cli["client_id"],
        "client_secret": cli["client_secret"],
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.post(token_url, data=data)
        try:
            resp.raise_for_status()
        except Exception as exc:
            LOGGER.warning("OIDC token exchange failed", extra={"status": getattr(resp, 'status_code', None), "error": str(exc)})
            raise HTTPException(status_code=502, detail="OIDC token exchange failed")
        token = resp.json()
    id_token = token.get("id_token")
    if not id_token:
        raise HTTPException(status_code=502, detail="id_token missing")

    # Verify ID token
    try:
        jwks_uri = disc.get("jwks_uri")
        keys = []
        if jwks_uri:
            async with httpx.AsyncClient(timeout=5.0) as client:
                jwks_resp = await client.get(jwks_uri)
                jwks_resp.raise_for_status()
                keys = jwks_resp.json().get("keys", [])
        unverified = jwt.get_unverified_header(id_token)
        key = None
        for jwk in keys:
            if unverified.get("kid") and jwk.get("kid") != unverified.get("kid"):
                continue
            key = _load_key_from_jwk(jwk, unverified.get("alg"))
            if key:
                break
        claims = jwt.decode(
            id_token,
            key=key,
            algorithms=[unverified.get("alg")],
            audience=cli["client_id"],
            issuer=str(_oidc_client()["issuer"]).rstrip("/"),
        )
    except Exception as exc:
        LOGGER.warning("ID token verification failed", extra={"error": str(exc)})
        raise HTTPException(status_code=401, detail="invalid id_token")

    if claims.get("nonce") != nonce_expected:
        raise HTTPException(status_code=401, detail="nonce mismatch")

    # Issue our own session JWT cookie for the Gateway
    global JWT_SECRET
    if not JWT_SECRET:
        # Attempt vault load if configured
        _hydrate_jwt_credentials_from_vault()
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="server not configured to sign session JWTs")
    cookie_name = os.getenv("GATEWAY_JWT_COOKIE_NAME", "jwt")
    # Build minimal session claims
    session_claims: dict[str, Any] = {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "name": claims.get("name") or claims.get("given_name"),
        "iss": "gateway",
    }
    if os.getenv("OIDC_TENANT_FROM_EMAIL_DOMAIN", "true").lower() in {"true", "1", "yes"}:
        email = (claims.get("email") or "").strip()
        if "@" in email:
            session_claims["tenant"] = email.split("@", 1)[1]
    token_ttl = int(os.getenv("GATEWAY_JWT_TTL_SECONDS", "3600"))
    now = int(time.time())
    session_claims.update({"iat": now, "exp": now + token_ttl})
    session_jwt = jwt.encode(session_claims, JWT_SECRET, algorithm=(JWT_ALGORITHMS[0] if JWT_ALGORITHMS else "HS256"))

    # After successful login, send the user to the root UI entrypoint
    resp = RedirectResponse(url="/")
    flags = _jwt_cookie_flags(request)
    resp.set_cookie(
        key=cookie_name,
        value=session_jwt,
        httponly=flags["httponly"],
        secure=flags["secure"],
        samesite=flags["samesite"],
        path=flags["path"],
        domain=flags["domain"],
        max_age=flags["max_age"],
    )
    return resp


@app.get("/")
async def root_entry(request: Request) -> Response:
    """Top-level entry: if auth required and missing → /login; else redirect to the UI index.

    Returning a redirect keeps behavior stable for tests and avoids duplicate HTML serving paths.
    """
    need_auth = _oidc_enabled() or REQUIRE_AUTH
    if need_auth and _session_claims_from_cookie(request) is None:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/ui/index.html")


@app.post("/v1/auth/logout")
async def auth_logout(request: Request) -> Response:
    cookie_name = os.getenv("GATEWAY_JWT_COOKIE_NAME", "jwt")
    resp = JSONResponse({"status": "ok"})
    flags = _jwt_cookie_flags(request)
    resp.delete_cookie(key=cookie_name, path=flags["path"], domain=flags["domain"])
    return resp


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
    try:
        LOGGER.info("get_publisher called")
    except Exception:
        pass
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


_SESSION_CACHE: RedisSessionCache | None = None
_AUDIT_STORE: _AuditStore | None = None


def get_session_cache() -> RedisSessionCache:
    """Return a process-wide RedisSessionCache singleton.

    Creating a new cache instance per request is wasteful and can contribute
    to connection churn. Reuse a single instance for the lifetime of the
    gateway process.
    """
    global _SESSION_CACHE
    if _SESSION_CACHE is None:
        try:
            LOGGER.info("initializing session cache", extra={"url": _redis_url()})
        except Exception:
            pass
        _SESSION_CACHE = RedisSessionCache(url=_redis_url())
    return _SESSION_CACHE


_SESSION_STORE: PostgresSessionStore | None = None


def get_session_store() -> PostgresSessionStore:
    """Return a process-wide PostgresSessionStore singleton.

    Previously, a new PostgresSessionStore (and asyncpg pool) was created on
    every dependency resolution, quickly exhausting PostgreSQL connections and
    causing 500s like "sorry, too many clients already". Centralize on a
    single store instance so only one pool is maintained per process.
    """
    global _SESSION_STORE
    if _SESSION_STORE is None:
        dsn = os.getenv("POSTGRES_DSN", APP_SETTINGS.postgres_dsn)
        try:
            LOGGER.info("initializing session store")
        except Exception:
            pass
        _SESSION_STORE = PostgresSessionStore(dsn=dsn)
    return _SESSION_STORE


def get_audit_store() -> _AuditStore:
    """Process-wide audit store singleton.

    Uses Postgres by default; for tests AUDIT_STORE_MODE=memory provides an
    in-memory implementation.
    """
    global _AUDIT_STORE
    if _AUDIT_STORE is not None:
        return _AUDIT_STORE
    _AUDIT_STORE = audit_store_from_env()
    return _AUDIT_STORE


def get_api_key_store() -> ApiKeyStore:
    global _API_KEY_STORE
    if _API_KEY_STORE is not None:
        return _API_KEY_STORE

    # Require Redis configuration for production use
    redis_url = _redis_url()
    redis_password = get_dotenv_value("REDIS_PASSWORD")
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


@app.get("/v1/admin/memory", response_model=AdminMemoryListResponse, tags=["admin"], summary="List memory replica rows")
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
    """List memory replica rows with filters and pagination.

    - Filters: tenant, persona_id, role, session_id, universe, namespace, q, min/max wal_timestamp
    - Pagination: id-desc cursor via 'after' and 'limit' (max 200)
    """
    await _enforce_admin_rate_limit(request)
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


@app.get("/v1/admin/memory/{event_id}", response_model=AdminMemoryItem, tags=["admin"], summary="Get memory by event_id")
async def get_admin_memory_item(
    event_id: str,
    request: Request,
    store: Annotated[MemoryReplicaStore, Depends(get_replica_store)] = None,  # type: ignore[assignment]
) -> AdminMemoryItem:
    """Fetch a single memory replica item by its event_id."""
    await _enforce_admin_rate_limit(request)
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


@app.get("/v1/memory/export", tags=["admin"], summary="Export memory as NDJSON stream")
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
    """Stream an NDJSON export of memory replica rows.

    Applies filters similar to the admin list endpoint. Concurrency is
    bounded by a semaphore; optional rate limits can also apply.
    """
    await _enforce_admin_rate_limit(request)
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


@app.post("/v1/memory/export/jobs", response_model=dict, tags=["admin"], summary="Create async export job")
async def export_jobs_create(request: Request, payload: ExportJobCreate) -> dict:
    if _file_saving_disabled():
        raise HTTPException(status_code=403, detail="File export is disabled")
    await _enforce_admin_rate_limit(request)
    auth = await authorize_request(request, payload.model_dump())
    _require_admin_scope(auth)
    if os.getenv("GATEWAY_EXPORT_REQUIRE_TENANT", "false").lower() in {"true", "1", "yes", "on"} and not payload.tenant:
        raise HTTPException(status_code=400, detail="tenant parameter required for export jobs")

    job_id = await get_export_job_store().create(params=payload.model_dump(), tenant=payload.tenant)
    return {"job_id": job_id, "status": "queued"}


@app.get("/v1/memory/export/jobs/{job_id}", response_model=ExportJobStatus, tags=["admin"], summary="Get export job status")
async def export_jobs_status(job_id: int, request: Request) -> ExportJobStatus:
    if _file_saving_disabled():
        raise HTTPException(status_code=403, detail="File export is disabled")
    await _enforce_admin_rate_limit(request)
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


@app.get("/v1/memory/export/jobs/{job_id}/download", tags=["admin"], summary="Download export result")
async def export_jobs_download(job_id: int, request: Request):
    if _file_saving_disabled():
        raise HTTPException(status_code=403, detail="File export is disabled")
    await _enforce_admin_rate_limit(request)
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
    # Make metadata optional to avoid edge-cases in request parsing when clients send an explicit empty object
    metadata: dict[str, str] | None = Field(default=None)

    # Normalize session_id early to avoid downstream UUID assumptions elsewhere in the stack
    @field_validator("session_id", mode="before")
    @classmethod
    def _validate_session_id(cls, v: Any) -> str | None:
        if not v:
            return None
        try:
            uuid.UUID(str(v))
            return str(v)
        except Exception:
            # Force None so the handler can generate a new UUID
            return None


# -----------------------------
# Conversation: message ingress and session/event queries
# -----------------------------


def _inbound_topic() -> str:
    return os.getenv("CONVERSATION_INBOUND", "conversation.inbound")


# Removed DEV echo: no synthetic assistant responses. The gateway never fabricates events.


# Removed legacy /v1/session/message implementation that synthesized events. See the unified
# enqueue_message implementation below for the only supported behavior.


# Removed legacy dict-shaped /v1/sessions; keeping the typed response version below.


# Removed legacy dict-shaped /v1/sessions/{id}/events; keeping the typed response version below.


# Removed legacy SSE endpoint that polled the session store to avoid duplicate route definitions.


# -----------------------------
# Minimal health and uploads endpoints used by UI
# -----------------------------


# Removed minimal /v1/health; keeping the comprehensive health_check implementation below.


# Removed DEV-safe uploads stub; keeping the full-featured /v1/uploads below.


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
class ToolRequestPayload(BaseModel):
    session_id: str = Field(..., description="Target session identifier")
    tool_name: str = Field(..., description="Registered tool name to execute")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool input arguments")
    persona_id: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class ToolsListResponse(BaseModel):
    tools: list[ToolInfo]
    count: int


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
JWT_SECRET = get_dotenv_value("GATEWAY_JWT_SECRET")
JWT_PUBLIC_KEY = get_dotenv_value("GATEWAY_JWT_PUBLIC_KEY")
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
_OIDC_DISCOVERY_CACHE: dict[str, Any] | None = None
_OIDC_DISCOVERY_TS: float | None = None


# -----------------------------
# Optional admin rate limiter (token bucket)
# -----------------------------

class _TokenBucketLimiter:
    """Simple token bucket limiter keyed by an arbitrary string.

    Not distributed; intended for single-process gateway instances or as a
    best-effort protection when running behind a global rate limiter.
    """

    def __init__(self, rate_per_sec: float, burst: int) -> None:
        self.rate = max(0.0, float(rate_per_sec))
        self.capacity = max(1, int(burst))
        self._buckets: dict[str, tuple[float, float]] = {}
        # key -> (tokens, last_refill_ts)

    def allow(self, key: str, *, now: float | None = None) -> bool:
        if self.rate <= 0:
            return True
        t = now if now is not None else time.monotonic()
        tokens, last = self._buckets.get(key, (float(self.capacity), t))
        # Refill tokens
        if t > last:
            tokens = min(self.capacity, tokens + (t - last) * self.rate)
            last = t
        if tokens >= 1.0:
            tokens -= 1.0
            self._buckets[key] = (tokens, last)
            return True
        self._buckets[key] = (tokens, last)
        return False


def _admin_rate_limiter() -> _TokenBucketLimiter | None:
    lim = getattr(app.state, "_admin_rl", None)
    if lim is not None:
        return lim  # type: ignore[return-value]
    try:
        rps = float(os.getenv("GATEWAY_ADMIN_RPS", "0"))
        burst = int(os.getenv("GATEWAY_ADMIN_BURST", "10"))
    except Exception:
        rps, burst = 0.0, 10
    if rps <= 0:
        app.state._admin_rl = None
        return None
    app.state._admin_rl = _TokenBucketLimiter(rate_per_sec=rps, burst=burst)
    return app.state._admin_rl


async def _enforce_admin_rate_limit(request: Request) -> None:
    limiter = _admin_rate_limiter()
    if not limiter:
        return
    key = request.url.path  # global per-path limiter; refine by tenant/subject if needed
    if not limiter.allow(key):
        raise HTTPException(status_code=429, detail="Too Many Requests (admin rate limit)")


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


def _get_openfga_client() -> OpenFGAClient:
    """Return a process-wide OpenFGA client.

    Hardened behavior: fail-closed. If OpenFGA is not configured or cannot
    be initialized, raise to indicate service misconfiguration rather than
    silently skipping enforcement.
    """

    global _OPENFGA_CLIENT

    if _OPENFGA_CLIENT is not None:
        return _OPENFGA_CLIENT

    try:
        _OPENFGA_CLIENT = OpenFGAClient()
        return _OPENFGA_CLIENT
    except Exception as exc:
        # Treat missing configuration (ValueError) and other errors uniformly
        # to ensure we never run without authorization enforcement.
        LOGGER.error(
            "OpenFGA client initialization failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        raise


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

    # Enforce OpenFGA in fail-closed mode when auth is required
    if REQUIRE_AUTH:
        # Require basic identity attributes
        if not tenant or not subject:
            raise HTTPException(status_code=401, detail="Missing identity claims")
        try:
            client = _get_openfga_client()
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Authorization not configured") from exc
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
            raise HTTPException(status_code=502, detail="Authorization service unavailable") from exc
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
    try:
        LOGGER.info(
            "enqueue_message start",
            extra={
                "has_session_id": bool(payload.session_id),
                "persona_id": payload.persona_id,
                "msg_len": len(payload.message) if isinstance(payload.message, str) else None,
            },
        )
    except Exception:
        pass
    auth_metadata = await authorize_request(request, payload.model_dump())
    base_meta = _apply_auth_metadata(payload.metadata or {}, auth_metadata)
    metadata, persona_hdr = _apply_header_metadata(request, base_meta)
    # Default tenant for unauthenticated/dev requests to align with OPA policy
    # so conversation.send is allowed in local development without identity.
    # This only applies when auth is not required and the client did not supply
    # an explicit tenant in headers or metadata.
    if not REQUIRE_AUTH and not metadata.get("tenant"):
        try:
            metadata["tenant"] = os.getenv("SOMA_TENANT_ID", "public")
        except Exception:
            metadata["tenant"] = "public"

    session_id = payload.session_id or str(uuid.uuid4())
    # Normalize session_id to a UUID string for envelope storage compatibility
    try:
        _ = uuid.UUID(str(session_id))
    except Exception:
        try:
            LOGGER.warning(
                "Invalid session_id provided; generating a new UUID",
                extra={"provided": str(session_id)},
            )
        except Exception:
            pass
        session_id = str(uuid.uuid4())
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

    try:
        validate_event(event, "conversation_event")
        LOGGER.info("validate_event ok", extra={"event_id": event_id})
    except Exception as exc:
        LOGGER.error("validate_event failed", exc_info=True, extra={"error": str(exc)})
        raise

    # Durable publish: prefer direct Kafka; avoid outbox fallback here to reduce DB pressure
    try:
        result = await publisher.publish(
            "conversation.inbound",
            event,
            dedupe_key=event_id,
            session_id=session_id,
            tenant=metadata.get("tenant"),
        )
    except Exception as exc:
        LOGGER.warning(
            "Inbound publish failed",
            extra={
                "error": str(exc),
                "session_id": session_id,
                "event_id": event_id,
            },
        )
        raise HTTPException(status_code=502, detail="Unable to enqueue message")
    try:
        LOGGER.info(
            "Published inbound message",
            extra={
                "topic": "conversation.inbound",
                "session_id": session_id,
                "event_id": event_id,
                "result": {k: bool(v) if isinstance(v, (bool, int)) else v for k, v in (result or {}).items()},
            },
        )
    except Exception:
        LOGGER.debug("Failed to log publish result (conversation.inbound)", exc_info=True)
    if not result.get("published") and not result.get("enqueued"):
        raise HTTPException(status_code=502, detail="Unable to enqueue message")

    # Audit: message enqueued (best-effort; do not block request)
    try:
        from opentelemetry import trace as _trace
        ctx = _trace.get_current_span().get_span_context()
        trace_id_hex = f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
    except Exception:
        trace_id_hex = None
    try:
        req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        await get_audit_store().log(
            request_id=req_id,
            trace_id=trace_id_hex,
            session_id=session_id,
            tenant=metadata.get("tenant"),
            subject=auth_metadata.get("subject"),
            action="message.enqueue",
            resource="conversation.message",
            target_id=event_id,
            details={
                "persona_id": event.get("persona_id"),
                "attachments": len(payload.attachments or []),
                "published": bool(result.get("published")),
                "enqueued": bool(result.get("enqueued")),
            },
            diff=None,
            ip=getattr(request.client, "host", None) if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        LOGGER.debug("Failed to write audit log for message.enqueue", exc_info=True)

    # Cache most recent metadata and append event to session store (best-effort; don't fail request)
    try:
        await _cache_session_metadata(cache, session_id, payload.persona_id, metadata)
    except Exception:
        LOGGER.debug("Session metadata cache write failed", exc_info=True)
    try:
        await store.append_event(session_id, {"type": "user", **event})
    except Exception:
        LOGGER.debug("Session event append failed", exc_info=True)

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


@app.post("/v1/uploads")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
) -> JSONResponse:
    """Upload one or more files and return normalized descriptors.

    - Enforces per-file size caps and per-request file count caps.
    - Applies optional allow/deny MIME rules.
    - Stores files under a durable, worker-readable path within the shared volume.
    - Evaluates OPA when auth is enforced (reuses existing authorize_request evaluation).
    """
    start = time.perf_counter()
    max_bytes, max_files = _upload_limits()

    # Enforce uploads enabled
    uploads_cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
    if isinstance(uploads_cfg, dict) and uploads_cfg.get("uploads_enabled") is False:
        raise HTTPException(status_code=403, detail="Uploads are disabled by administrator")

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > max_files:
        raise HTTPException(status_code=400, detail=f"Too many files (max {max_files})")

    # Validate auth and (if enabled) policy at request-level
    auth_meta = await authorize_request(request, {"action": "attachments.upload", "count": len(files)})
    tenant = auth_meta.get("tenant") or "public"
    sess = (session_id or "").strip() or "unspecified"

    results: list[dict[str, Any]] = []

    for upl in files:
        fname = upl.filename or "file"
        safe_name = secure_filename(fname) or "file"
        mime = upl.content_type or "application/octet-stream"

        if not _mime_allowed(mime):
            GATEWAY_UPLOADS.labels("blocked").inc()
            raise HTTPException(status_code=415, detail=f"MIME type not allowed: {mime}")

        sha = hashlib.sha256()
        size = 0
        chunks: list[bytes] = []
        try:
            while True:
                chunk = await upl.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    GATEWAY_UPLOADS.labels("blocked").inc()
                    raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes} bytes)")
                sha.update(chunk)
                chunks.append(chunk)
        except HTTPException:
            raise
        except Exception as exc:
            LOGGER.error("Upload read failed", extra={"file": safe_name, "error": str(exc)})
            GATEWAY_UPLOADS.labels("error").inc()
            raise HTTPException(status_code=500, detail="Upload failed")
        finally:
            with contextlib.suppress(Exception):
                await upl.close()

        # Optional antivirus scan
        quarantined = False
        quarantine_reason = None
        if _clamav_enabled():
            data = b"".join(chunks)
            status, detail = await _clamav_scan_bytes(data)
            GATEWAY_AV_SCANS.labels(status).inc()
            if status == "infected":
                quarantined = True
                quarantine_reason = "infected"
            elif status == "error":
                LOGGER.warning("AV scan error", extra={"file": safe_name, "detail": detail})
                if _clamav_strict():
                    GATEWAY_UPLOADS.labels("blocked").inc()
                    raise HTTPException(status_code=502, detail="Antivirus error (strict mode)")
                else:
                    quarantined = True
                    quarantine_reason = "av_error"

        # Per-file OPA evaluation (optional; piggybacks on authorize_request)
        try:
            if REQUIRE_AUTH and OPA_URL:
                await _evaluate_opa(
                    request,
                    {
                        "action": "attachments.upload.file",
                        "tenant": tenant,
                        "session_id": sess,
                        "filename": safe_name,
                        "mime": mime,
                        "size": size,
                    },
                    {},
                )
        except HTTPException:
            GATEWAY_UPLOADS.labels("blocked").inc()
            raise

        # Persist to Postgres attachments store
        content_bytes: bytes | None = b"".join(chunks)
        # Inline cap (optional); default to min(max_mb, 16MB)
        try:
            cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
            inline_mb = float(cfg.get("uploads_inline_max_mb", min(max_bytes / (1024 * 1024), 16)))
        except Exception:
            inline_mb = min(max_bytes / (1024 * 1024), 16)
        inline_cap = int(inline_mb * 1024 * 1024)
        if size > inline_cap:
            # For now reject oversize inline; external_ref path can be added later via settings
            GATEWAY_UPLOADS.labels("blocked").inc()
            raise HTTPException(status_code=413, detail=f"File exceeds inline cap ({inline_mb} MB)")

        try:
            att_store = get_attachments_store()
            att_id = await att_store.insert(
                tenant=tenant,
                session_id=sess,
                persona_id=auth_meta.get("persona_id"),
                filename=safe_name,
                mime=mime,
                size=size,
                sha256=sha.hexdigest(),
                status="quarantined" if quarantined else "clean",
                quarantine_reason=quarantine_reason,
                content=content_bytes,
            )
        except Exception as exc:
            LOGGER.error("Attachment persist failed", extra={"file": safe_name, "error": str(exc)})
            GATEWAY_UPLOADS.labels("error").inc()
            raise HTTPException(status_code=500, detail="Unable to persist attachment")

        descriptor = {
            "id": str(att_id),
            "filename": safe_name,
            "mime": mime,
            "size": size,
            "sha256": sha.hexdigest(),
            "created_at": time.time(),
            "tenant": tenant,
            "session_id": sess,
            "status": "quarantined" if quarantined else "clean",
            "quarantine_reason": quarantine_reason if quarantined else None,
            # Provide a stable download path usable by the Web UI
            "path": f"/v1/attachments/{str(att_id)}",
        }
        results.append(descriptor)
        GATEWAY_UPLOADS.labels("ok" if not quarantined else "blocked").inc()

    GATEWAY_UPLOAD_SECONDS.observe(time.perf_counter() - start)
    return JSONResponse(results)


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
        # Ensure metadata/analysis are dicts for pydantic model validation.
        md = envelope.metadata
        if isinstance(md, str):
            try:
                from json import loads as _loads
                parsed = _loads(md)
                md = parsed if isinstance(parsed, dict) else {}
            except Exception:
                md = {}
        elif not isinstance(md, dict):
            md = {}

        an = envelope.analysis
        if isinstance(an, str):
            try:
                from json import loads as _loads
                parsed = _loads(an)
                an = parsed if isinstance(parsed, dict) else {}
            except Exception:
                an = {}
        elif not isinstance(an, dict):
            an = {}
        summaries.append(
            SessionSummary(
                session_id=str(envelope.session_id),
                persona_id=envelope.persona_id,
                tenant=envelope.tenant,
                subject=envelope.subject,
                issuer=envelope.issuer,
                scope=envelope.scope,
                metadata=md,
                analysis=an,
                created_at=envelope.created_at,
                updated_at=envelope.updated_at,
            )
        )
    return summaries
@app.delete("/v1/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    request: Request,
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
) -> dict[str, Any]:
    # Authz: reuse request auth to hydrate tenant for auditing
    auth_metadata = await authorize_request(request, {"session_id": session_id})
    _ = auth_metadata  # currently unused for decision; can enforce ownership with OpenFGA later
    result = await store.delete_session(session_id)
    try:
        await cache.delete(cache.format_key(session_id))
    except Exception:
        LOGGER.debug("Failed to delete session cache key", exc_info=True)
    return {"status": "deleted", "result": result}

@app.post("/v1/sessions/{session_id}/reset")
async def reset_session_endpoint(
    session_id: str,
    request: Request,
    store: Annotated[PostgresSessionStore, Depends(get_session_store)],
) -> dict[str, Any]:
    auth_metadata = await authorize_request(request, {"session_id": session_id})
    _ = auth_metadata
    result = await store.reset_session(session_id)
    return {"status": "reset", "result": result}

@app.post("/v1/sessions/{session_id}/pause")
async def pause_session_endpoint(
    session_id: str,
    payload: dict[str, Any],
    request: Request,
    cache: Annotated[RedisSessionCache, Depends(get_session_cache)],
) -> dict[str, Any]:
    # payload expects {"paused": true|false}
    auth_metadata = await authorize_request(request, {"session_id": session_id})
    _ = auth_metadata
    paused = bool(payload.get("paused"))
    try:
        # Preserve existing persona/metadata if present; otherwise seed
        existing = await cache.get(cache.format_key(session_id)) or {}
        persona_id = existing.get("persona_id") or ""
        md = dict((existing.get("metadata") or {}))
        md["paused"] = paused
        await cache.write_context(session_id, persona_id, md)
    except Exception:
        LOGGER.debug("Failed to update session paused flag in cache", exc_info=True)
        raise HTTPException(status_code=500, detail="failed to update pause state")
    return {"status": "ok", "paused": paused}

@app.post("/v1/tool/request")
async def request_tool_execution(
    payload: ToolRequestPayload,
    request: Request,
    publisher: Annotated[DurablePublisher, Depends(get_publisher)],
) -> dict[str, Any]:
    auth_metadata = await authorize_request(request, payload.model_dump())
    metadata, persona_hdr = _apply_header_metadata(request, {**payload.metadata, **auth_metadata})
    persona_id = payload.persona_id or persona_hdr
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": payload.session_id,
        "persona_id": persona_id,
        "tool_name": payload.tool_name,
        "args": payload.args,
        "metadata": metadata,
    }
    try:
        validate_event(event, "tool_request")
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"invalid tool request: {exc}") from exc

    topic = os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests")
    await publisher.publish(
        topic,
        event,
        dedupe_key=event_id,
        session_id=payload.session_id,
        tenant=metadata.get("tenant"),
    )
    # Audit enqueue (best-effort)
    try:
        from opentelemetry import trace as _trace
        ctx = _trace.get_current_span().get_span_context()
        trace_id_hex = f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
    except Exception:
        trace_id_hex = None
    try:
        req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        await get_audit_store().log(
            request_id=req_id,
            trace_id=trace_id_hex,
            session_id=payload.session_id,
            tenant=metadata.get("tenant"),
            subject=auth_metadata.get("subject"),
            action="tool.request.enqueue",
            resource="tool.request",
            target_id=event_id,
            details={
                "tool_name": payload.tool_name,
                "args_keys": sorted(list((payload.args or {}).keys())),
                "metadata_keys": sorted(list((metadata or {}).keys())),
                "topic": topic,
            },
            diff=None,
            ip=getattr(request.client, "host", None) if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        LOGGER.debug("Failed to write audit log for tool.request.enqueue", exc_info=True)
    return {"status": "enqueued", "event_id": event_id}


@app.get("/v1/tools", response_model=ToolsListResponse)
async def list_tools() -> ToolsListResponse:
    """List available tools from the in-repo tool registry.

    This reflects the Tool Executor's built-in registry to keep UI/Worker prompts
    aligned without a separate network hop.
    """
    try:
        from services.tool_executor.tool_registry import ToolRegistry  # type: ignore
    except Exception as exc:  # pragma: no cover - env dependent
        raise HTTPException(status_code=503, detail=f"tool registry unavailable: {exc}")

    reg = ToolRegistry()
    try:
        await reg.load_all_tools()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to load tools: {exc}")

    tools: list[ToolInfo] = []
    for t in reg.list():
        schema = None
        try:
            handler = getattr(t, "handler", None)
            if handler is not None and hasattr(handler, "input_schema"):
                schema = handler.input_schema()  # type: ignore[assignment]
        except Exception:
            schema = None
        tools.append(ToolInfo(name=t.name, description=getattr(t, "description", None), parameters=schema))
    return ToolsListResponse(tools=tools, count=len(tools))


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
# Static UI note
# -----------------------------
"""
Serve the Web UI under /ui, but mount it AFTER defining explicit /ui/* routes
like /ui/config.json so those routes take precedence over static files.
"""

try:
    UI_DIR = (Path(__file__).resolve().parents[2] / "webui").resolve()
    if UI_DIR.exists():
        # Mount the Web UI root under /ui so /ui/index.html and related relative paths work
        app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

        # Serve the UI at root path as the default entrypoint
        index_html = UI_DIR / "index.html"
        if index_html.exists():
            @app.get("/", include_in_schema=False)
            @app.get("/index.html", include_in_schema=False)
            async def _root_ui() -> Response:  # type: ignore
                # Always redirect to the canonical UI path to avoid duplicate roots
                return RedirectResponse(url="/ui/index.html")

        # Additionally mount common asset subpaths at the root to satisfy absolute imports
        # used by the UI (e.g., "/js/...", "/public/...", "/components/...").
        for sub in ("js", "css", "components", "public", "vendor"):
            subdir = UI_DIR / sub
            if subdir.exists():
                # Do not use html=True for asset folders
                app.mount(f"/{sub}", StaticFiles(directory=str(subdir), html=False), name=f"ui-{sub}")

        # Serve root-level index.js for absolute imports (e.g., import "/index.js") used by some modules
        index_js = UI_DIR / "index.js"
        if index_js.exists():
            @app.get("/index.js", include_in_schema=False)
            async def _index_js() -> FileResponse:  # type: ignore
                return FileResponse(str(index_js), media_type="application/javascript")

        # Serve root-level index.css so the homepage styles load when UI is mounted at root
        index_css = UI_DIR / "index.css"
        if index_css.exists():
            @app.get("/index.css", include_in_schema=False)
            async def _index_css() -> FileResponse:  # type: ignore
                return FileResponse(str(index_css), media_type="text/css")

        # Serve a favicon for browsers that automatically request /favicon.ico
        favicon_svg = UI_DIR / "public" / "favicon.svg"
        favicon_round_svg = UI_DIR / "public" / "favicon_round.svg"
        if favicon_svg.exists() or favicon_round_svg.exists():
            chosen = str(favicon_svg if favicon_svg.exists() else favicon_round_svg)

            @app.get("/favicon.ico", include_in_schema=False)
            async def _favicon_ico() -> FileResponse:  # type: ignore
                # Many modern browsers accept SVG as favicon; serve SVG to avoid bundling .ico
                return FileResponse(chosen, media_type="image/svg+xml")

            @app.get("/favicon.svg", include_in_schema=False)
            async def _favicon_svg() -> FileResponse:  # type: ignore
                return FileResponse(chosen, media_type="image/svg+xml")

        # Optional: serve common root-level pages and their styles if present
        login_html = UI_DIR / "login.html"
        if login_html.exists():
            @app.get("/login.html", include_in_schema=False)
            async def _login_html() -> FileResponse:  # type: ignore
                return FileResponse(str(login_html), media_type="text/html")

        login_css = UI_DIR / "login.css"
        if login_css.exists():
            @app.get("/login.css", include_in_schema=False)
            async def _login_css() -> FileResponse:  # type: ignore
                return FileResponse(str(login_css), media_type="text/css")

        LOGGER.info("Mounted WebUI", extra={"path": str(UI_DIR)})
    else:
        LOGGER.info("WebUI directory not found", extra={"expected": str(UI_DIR)})
except Exception:
    LOGGER.debug("Failed to mount WebUI", exc_info=True)


# -----------------------------
# Uploads janitor (TTL cleanup)
# -----------------------------

# -----------------------------
# Optional tunnel proxy compatibility
# -----------------------------

@app.post("/tunnel_proxy")
async def tunnel_proxy(request: Request) -> JSONResponse:  # type: ignore
    """Compatibility stub for the UI tunnel feature.

    The UI may call /tunnel_proxy on load to check tunnel status. In this build,
    we return a 200 with a structured payload instead of 404 to avoid console errors.
    Supported actions (all no-ops by default): get, create, verify, stop.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    action = str(data.get("action", "get")).lower()

    # Default response indicating tunnel is not configured
    base = {"success": False, "message": "Tunnel not configured in this deployment"}

    if action == "get":
        return JSONResponse({**base, "tunnel_url": None})
    if action == "verify":
        return JSONResponse({"success": True, "is_valid": False})
    if action == "create":
        # In future, wire to actual tunnel provider; for now, return not configured
        return JSONResponse(base)
    if action == "stop":
        return JSONResponse({"success": True})

    return JSONResponse(base)


async def _uploads_janitor(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        rows_deleted = 0
        try:
            cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
            try:
                ttl_days = float(cfg.get("uploads_ttl_days", os.getenv("GATEWAY_UPLOAD_TTL_DAYS", "7")))
            except Exception:
                ttl_days = 7.0
            if ttl_days <= 0:
                ttl_days = 0.0
            if ttl_days > 0:
                try:
                    rows_deleted = await get_attachments_store().delete_older_than(ttl_days)
                except Exception:
                    JANITOR_ERRORS.inc()
            JANITOR_FILES_DELETED.inc(rows_deleted)
            JANITOR_LAST_RUN.set(time.time())
        except Exception:
            JANITOR_ERRORS.inc()
            LOGGER.debug("Uploads janitor pass failed", exc_info=True)
        try:
            cfg = getattr(app.state, "uploads_cfg", {}) if hasattr(app, "state") else {}
            try:
                interval = float(cfg.get("uploads_janitor_interval_seconds", os.getenv("GATEWAY_UPLOAD_JANITOR_INTERVAL_SECONDS", "3600")))
            except Exception:
                interval = 3600.0
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


@app.on_event("startup")
async def _start_uploads_janitor() -> None:
    try:
        app.state._uploads_stop = asyncio.Event()
        asyncio.create_task(_uploads_janitor(app.state._uploads_stop))
    except Exception:
        LOGGER.debug("Failed to start uploads janitor", exc_info=True)


@app.on_event("shutdown")
async def _stop_uploads_janitor() -> None:
    try:
        if hasattr(app.state, "_uploads_stop"):
            app.state._uploads_stop.set()
    except Exception:
        pass

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
        # Normalise kwargs to a dict (DB may return JSON as text depending on driver settings)
        from json import loads as _json_loads
        kwargs: dict[str, Any] | None
        if isinstance(profile.kwargs, dict):
            kwargs = profile.kwargs
        elif isinstance(profile.kwargs, str):
            try:
                parsed = _json_loads(profile.kwargs)
                kwargs = parsed if isinstance(parsed, dict) else None
            except Exception:
                kwargs = None
        else:
            kwargs = None
        profile_payload = {
            "role": profile.role,
            "deployment_mode": profile.deployment_mode,
            "model": profile.model,
            "base_url": profile.base_url,
            "temperature": profile.temperature,
            "kwargs": kwargs or {},
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


def _normalize_llm_base_url(raw: str) -> str:
    """Normalize an OpenAI-compatible base URL to its root.

    - Trims whitespace
    - Removes trailing slashes
    - Removes a single trailing "/v1" and "/chat/completions" if present
    - In non-DEV, enforces https scheme when a scheme is present
    """
    s = (raw or "").strip()
    if not s:
        return s
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(s)
        scheme = (parsed.scheme or "").lower()
        netloc = parsed.netloc
        path = parsed.path or ""
        # Remove trailing slashes
        path = path.rstrip("/")
        # Drop a single trailing /v1 and/or /chat/completions
        if path.endswith("/chat/completions"):
            path = path[: -len("/chat/completions")]
            path = path.rstrip("/")
        if path.endswith("/v1"):
            path = path[: -len("/v1")]
            path = path.rstrip("/")
        # Enforce https in non-DEV when scheme is present
        deployment = APP_SETTINGS.deployment_mode.upper()
        if scheme and deployment != "DEV" and scheme != "https":
            scheme = "https"
        # Rebuild URL without query/fragment
        normalized = urlunparse((scheme, netloc, path, "", "", ""))
        return normalized or s
    except Exception:
        # Best-effort string ops fallback
        s = s.rstrip("/")
        if s.endswith("/chat/completions"):
            s = s[: -len("/chat/completions")]
            s = s.rstrip("/")
        if s.endswith("/v1"):
            s = s[: -len("/v1")]
            s = s.rstrip("/")
        return s

def _detect_provider_from_base(base_url: str) -> str:
    host = ""
    try:
        from urllib.parse import urlparse
        host = (urlparse(base_url).netloc or "").lower()
    except Exception:
        host = base_url.lower()
    if "groq" in host:
        return "groq"
    if "openrouter" in host:
        return "openrouter"
    if "openai" in host:
        return "openai"
    return "other"


@app.put("/v1/ui/settings")
async def put_ui_settings(payload: UiSettingsPayload) -> dict[str, Any]:
    if payload.agent:
        agent_cfg = _default_ui_agent() | payload.agent
        await get_ui_settings_store().set(agent_cfg)

    if payload.model_profile:
        mp = payload.model_profile
        deployment = APP_SETTINGS.deployment_mode
        # Normalise kwargs to a dict (may arrive as JSON string)
        extra = mp.get("kwargs")
        if isinstance(extra, str):
            try:
                from json import loads as _loads
                loaded = _loads(extra)
                extra = loaded if isinstance(loaded, dict) else None
            except Exception:
                extra = None
        base_url = _normalize_llm_base_url(str(mp.get("base_url", "")))
        to_save = ModelProfile(
            role="dialogue",
            deployment_mode=deployment,
            model=str(mp.get("model", "")),
            base_url=base_url,
            temperature=float(mp.get("temperature", 0.2)),
            kwargs=extra if isinstance(extra, dict) else None,
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
# UI-shaped settings endpoints (compatibility for SPA "sections")
# -----------------------------


@app.get("/v1/ui/settings/sections")
async def ui_sections_get() -> dict[str, Any]:
    """Return the UI modal 'sections' structure assembled from Gateway stores.

    This preserves the simple front-end contract while centralizing the source
    of truth in the Gateway. It overlays agent settings and model profile values
    into the default UI sections.
    """
    # Base UI sections from server-side defaults
    out = ui_convert_out(ui_get_defaults())

    # Load current UI settings document (top-level dict)
    agent_cfg = await get_ui_settings_store().get()
    deployment = APP_SETTINGS.deployment_mode
    profile = await PROFILE_STORE.get("dialogue", deployment)

    # Apply overlays to fields
    try:
        sections = out.get("sections", [])
        # Agent overlays
        if agent_cfg:
            for sec in sections:
                for fld in sec.get("fields", []):
                    fid = fld.get("id")
                    if fid in {"agent_profile", "agent_memory_subdir", "agent_knowledge_subdir"}:
                        val = agent_cfg.get(fid)
                        if val:
                            fld["value"] = val
        # Model overlays
        if profile:
            provider = ""
            host = (profile.base_url or "").lower()
            if "groq" in host:
                provider = "groq"
            elif "openrouter" in host:
                provider = "openrouter"
            for sec in sections:
                for fld in sec.get("fields", []):
                    fid = fld.get("id")
                    if fid == "chat_model_provider" and provider:
                        fld["value"] = provider
                    elif fid == "chat_model_name" and profile.model:
                        fld["value"] = profile.model
                    elif fid == "chat_model_api_base" and profile.base_url:
                        fld["value"] = profile.base_url
                    elif fid == "chat_model_kwargs" and profile.kwargs:
                        kv = profile.kwargs or {}
                        try:
                            fld["value"] = "\n".join(f"{k}={v}" for k, v in kv.items())
                        except Exception:
                            fld["value"] = kv

        # Credentials overlay: mark providers with stored secrets using placeholder
        try:
            creds_store = get_llm_credentials_store()
            providers_with_keys = set(await creds_store.list_providers())
        except Exception:
            providers_with_keys = set()
        if providers_with_keys:
            for sec in sections:
                for fld in sec.get("fields", []):
                    try:
                        fid = fld.get("id") or ""
                        if isinstance(fid, str) and fid.startswith("api_key_"):
                            prov = fid[len("api_key_"):].strip().lower()
                            if prov in providers_with_keys:
                                # Use the same placeholder the UI expects
                                fld["value"] = "************"
                                # Prefer password type for secrets if not already
                                if fld.get("type") not in {"password"}:
                                    fld["type"] = "password"
                    except Exception:
                        # non-fatal; continue overlaying others
                        pass
    except Exception:
        LOGGER.debug("Failed to overlay UI sections", exc_info=True)

    # Append Uploads and Antivirus sections using the existing sections/fields schema
    uploads = agent_cfg.get("uploads") if isinstance(agent_cfg, dict) else None
    antivirus = agent_cfg.get("antivirus") if isinstance(agent_cfg, dict) else None

    uploads_defaults = {
        "uploads_enabled": True,
        "uploads_max_mb": 25,
        "uploads_max_files": 10,
        "uploads_allowed_mime": "",
        "uploads_denied_mime": "",
        "uploads_dir": "postgres",  # storage backend label (read-only)
        "uploads_ttl_days": 7,
        "uploads_janitor_interval_seconds": 3600,
        "uploads_inline_max_mb": 16,
        "uploads_allow_external_ref": False,
        "uploads_external_ref_allowlist": "",
        "uploads_dedup_sha256": False,
        "uploads_quarantine_policy": "store_and_block",
        "uploads_download_token_ttl_seconds": 0,
    }
    av_defaults = {
        "av_enabled": False,
        "av_strict": False,
        "av_host": os.getenv("CLAMAV_HOST", "clamav"),
        "av_port": int(os.getenv("CLAMAV_PORT", "3310")),
    }

    def _merge(defs: dict[str, Any], doc: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(defs)
        if isinstance(doc, dict):
            for k, v in doc.items():
                if k in merged:
                    merged[k] = v
        return merged

    uploads_vals = _merge(uploads_defaults, uploads if isinstance(uploads, dict) else None)
    av_vals = _merge(av_defaults, antivirus if isinstance(antivirus, dict) else None)

    sections = out.get("sections", [])
    sections.append(
        {
            "id": "uploads",
            "title": "Uploads",
            "description": "Configure file upload behavior and limits.",
            "tab": "agent",
            "fields": [
                {"id": "uploads_enabled", "title": "Enable Uploads", "type": "switch", "value": uploads_vals["uploads_enabled"]},
                {"id": "uploads_max_mb", "title": "Max File Size (MB)", "type": "number", "value": uploads_vals["uploads_max_mb"]},
                {"id": "uploads_max_files", "title": "Max Files Per Message", "type": "number", "value": uploads_vals["uploads_max_files"]},
                {"id": "uploads_allowed_mime", "title": "Allowed MIME Types (CSV/lines)", "type": "textarea", "value": uploads_vals["uploads_allowed_mime"]},
                {"id": "uploads_denied_mime", "title": "Denied MIME Types (CSV/lines)", "type": "textarea", "value": uploads_vals["uploads_denied_mime"]},
                {"id": "uploads_dir", "title": "Storage Backend", "type": "text", "value": uploads_vals["uploads_dir"], "readonly": True},
                {"id": "uploads_ttl_days", "title": "Retention TTL (days)", "type": "number", "value": uploads_vals["uploads_ttl_days"]},
                {"id": "uploads_janitor_interval_seconds", "title": "Janitor Interval (seconds)", "type": "number", "value": uploads_vals["uploads_janitor_interval_seconds"]},
                {"id": "uploads_inline_max_mb", "title": "Inline Cap (MB)", "type": "number", "value": uploads_vals["uploads_inline_max_mb"]},
                {"id": "uploads_allow_external_ref", "title": "Allow External References (URLs)", "type": "switch", "value": uploads_vals["uploads_allow_external_ref"]},
                {"id": "uploads_external_ref_allowlist", "title": "External URL Allowlist (CSV domains)", "type": "textarea", "value": uploads_vals["uploads_external_ref_allowlist"]},
                {"id": "uploads_dedup_sha256", "title": "Enable SHA256 Dedup (per tenant)", "type": "switch", "value": uploads_vals["uploads_dedup_sha256"]},
                {"id": "uploads_quarantine_policy", "title": "Quarantine Policy", "type": "select", "options": ["store_and_block", "drop_bytes_keep_meta"], "value": uploads_vals["uploads_quarantine_policy"]},
                {"id": "uploads_download_token_ttl_seconds", "title": "Signed Download Token TTL (seconds)", "type": "number", "value": uploads_vals["uploads_download_token_ttl_seconds"]},
            ],
        }
    )

    sections.append(
        {
            "id": "antivirus",
            "title": "Antivirus",
            "description": "Scan uploaded files with ClamAV (disabled by default).",
            "tab": "agent",
            "fields": [
                {"id": "av_enabled", "title": "Enable Antivirus", "type": "switch", "value": av_vals["av_enabled"]},
                {"id": "av_strict", "title": "Strict Mode (block on AV error)", "type": "switch", "value": av_vals["av_strict"]},
                {"id": "av_host", "title": "ClamAV Host", "type": "text", "value": av_vals["av_host"]},
                {"id": "av_port", "title": "ClamAV Port", "type": "number", "value": av_vals["av_port"]},
                {"id": "av_test", "title": "Test Scan", "type": "button", "value": "Test Scan"},
            ],
        }
    )

    out["sections"] = sections
    return {"settings": out}


class UiSectionsPayload(BaseModel):
    sections: list[Dict[str, Any]]


@app.post("/v1/ui/settings/sections")
async def ui_sections_set(payload: UiSectionsPayload, request: Request) -> dict[str, Any]:
    """Accept UI 'sections' and persist to Gateway stores.

    - Persists agent settings (ui_settings table).
    - Upserts the dialogue model profile.
    - Stores any provider credentials embedded in fields (keys starting with 'api_key_').
    Returns refreshed UI sections.
    """
    sections = payload.sections or []
    # Extract top-level agent settings and new nested groups
    agent: Dict[str, Any] = {}
    model_profile: Dict[str, Any] = {}
    creds: list[tuple[str, str]] = []
    uploads_cfg: Dict[str, Any] = {}
    av_cfg: Dict[str, Any] = {}
    explicit_provider: str | None = None

    def _as_env_kv(text: str) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for line in (text or "").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
        return out

    for sec in sections:
        for fld in sec.get("fields", []):
            fid = (fld.get("id") or "").strip()
            val = fld.get("value")
            if not fid:
                continue
            if fid in {"agent_profile", "agent_memory_subdir", "agent_knowledge_subdir"} and val:
                agent[fid] = val
            elif fid == "chat_model_provider" and isinstance(val, str):
                explicit_provider = val.strip().lower() or None
            elif fid == "chat_model_name" and isinstance(val, str):
                model_profile["model"] = val.strip()
            elif fid == "chat_model_api_base" and isinstance(val, str):
                model_profile["base_url"] = val.strip()
            elif fid == "chat_model_kwargs" and isinstance(val, str):
                kv = _as_env_kv(val)
                model_profile["kwargs"] = kv
                if "temperature" in kv:
                    try:
                        model_profile["temperature"] = float(kv["temperature"])  # type: ignore
                    except Exception:
                        pass
            elif fid.startswith("api_key_") and isinstance(val, str) and val and val != "************":
                provider = fid[len("api_key_") :].strip().lower()
                creds.append((provider, val))
            # Uploads config fields
            elif fid in {
                "uploads_enabled",
                "uploads_max_mb",
                "uploads_max_files",
                "uploads_allowed_mime",
                "uploads_denied_mime",
                "uploads_ttl_days",
                "uploads_janitor_interval_seconds",
                "uploads_inline_max_mb",
                "uploads_allow_external_ref",
                "uploads_external_ref_allowlist",
                "uploads_dedup_sha256",
                "uploads_quarantine_policy",
                "uploads_download_token_ttl_seconds",
            }:
                uploads_cfg[fid] = val
            elif fid == "uploads_dir":
                # read-only; ignore client attempts to change
                pass
            # Antivirus config fields
            elif fid in {"av_enabled", "av_strict", "av_host", "av_port"}:
                av_cfg[fid] = val

    # Persist settings (merge with existing document)
    ui_store = get_ui_settings_store()
    current_doc = await ui_store.get()
    original_doc = copy.deepcopy(current_doc) if isinstance(current_doc, dict) else {}
    if not isinstance(current_doc, dict):
        current_doc = {}
    # Agent settings are top-level keys
    for k, v in agent.items():
        current_doc[k] = v
    # Nested groups
    if uploads_cfg:
        current_doc["uploads"] = {**dict(current_doc.get("uploads") or {}), **uploads_cfg}
    if av_cfg:
        current_doc["antivirus"] = {**dict(current_doc.get("antivirus") or {}), **av_cfg}
    await ui_store.set(current_doc)

    # Prepare audit context now that the new doc is set
    try:
        auth_meta = await authorize_request(request, {"action": "settings.update"})
    except Exception:
        auth_meta = {}

    # Validate and upsert dialogue model profile
    if model_profile:
        # Basic field validation
        model_name = (str(model_profile.get("model")) or "").strip()
        base_url_raw = (str(model_profile.get("base_url", "")) or "").strip()
        if not model_name:
            raise HTTPException(status_code=400, detail="chat_model_name is required")
        # Normalize base_url before saving (allows empty -> provider default)
        normalized_base = _normalize_llm_base_url(base_url_raw)

        # Determine provider for credential validation
        provider = explicit_provider or ""
        host = normalized_base.lower()
        if not provider:
            if "groq" in host:
                provider = "groq"
            elif "openrouter" in host:
                provider = "openrouter"
            elif "openai" in host:
                provider = "openai"
        # If we recognized a provider (or user explicitly selected one), ensure a key exists
        if provider:
            try:
                creds_store = get_llm_credentials_store()
                have = await creds_store.has(provider)
            except Exception:
                have = False
            if not have and not any(c[0] == provider for c in creds):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing API key for provider '{provider}'. Add it in the API Keys section (field id: api_key_{provider}).",
                )

        # Clamp temperature if provided via kwargs
        try:
            temp = float(model_profile.get("temperature", 0.2))
            if temp < 0.0:
                temp = 0.0
            if temp > 2.0:
                temp = 2.0
        except Exception:
            temp = 0.2

        mp = ModelProfile(
            role="dialogue",
            deployment_mode=APP_SETTINGS.deployment_mode,
            model=model_name,
            base_url=normalized_base,
            temperature=temp,
            kwargs=(model_profile.get("kwargs") if isinstance(model_profile.get("kwargs"), dict) else None),
        )
        await PROFILE_STORE.upsert(mp)

    # Store provider credentials
    if creds:
        store = get_llm_credentials_store()
        for provider, secret in creds:
            try:
                await store.set(provider, secret)
            except Exception as exc:
                LOGGER.warning("Failed to store LLM credentials", extra={"provider": provider, "error": str(exc)})

    # Emit audit log (masking secrets) – best-effort
    try:
        def _mask_value(k: str, v: Any) -> Any:
            if not isinstance(k, str):
                return v
            k_lower = k.lower()
            if k_lower.startswith("api_key_") or any(s in k_lower for s in ("secret", "password", "token")):
                return "************"
            return v

        def _masked(d: dict) -> dict:
            out: dict[str, Any] = {}
            for k, v in (d or {}).items():
                if isinstance(v, dict):
                    out[k] = _masked(v)
                else:
                    out[k] = _mask_value(k, v)
            return out

        before = _masked(original_doc if isinstance(original_doc, dict) else {})
        after = _masked(current_doc if isinstance(current_doc, dict) else {})
        # naive diff: include both before/after for now
        diff = {"before": before, "after": after}

        # Trace id from current span
        try:
            from opentelemetry import trace as _trace
            ctx = _trace.get_current_span().get_span_context()
            trace_id_hex = f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
        except Exception:
            trace_id_hex = None

        req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        await get_audit_store().log(
            request_id=req_id,
            trace_id=trace_id_hex,
            session_id=None,
            tenant=auth_meta.get("tenant"),
            subject=auth_meta.get("subject"),
            action="settings.update",
            resource="ui.settings",
            target_id=None,
            details={
                "providers_updated": [p for p, _ in creds],
                "explicit_provider": explicit_provider,
            },
            diff=diff,
            ip=getattr(request.client, "host", None) if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        LOGGER.debug("Failed to write audit log for settings.update", exc_info=True)

    # Return refreshed sections
    return await ui_sections_get()


@app.get("/v1/av/test")
async def av_test() -> dict[str, Any]:
    """Connectivity check to ClamAV daemon using current settings (or env defaults)."""
    # Determine current AV config (merge store values on top of defaults)
    doc = await get_ui_settings_store().get()
    cfg = dict(doc.get("antivirus")) if isinstance(doc, dict) and isinstance(doc.get("antivirus"), dict) else {}
    host = str(cfg.get("av_host") or os.getenv("CLAMAV_HOST", "clamav"))
    try:
        port = int(cfg.get("av_port") or int(os.getenv("CLAMAV_PORT", "3310")))
    except Exception:
        port = 3310
    # Attempt TCP connect with short timeout
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=2.0)
        try:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
        except Exception:
            pass
        return {"status": "ok", "host": host, "port": port}
    except Exception as exc:
        return {"status": "error", "host": host, "port": port, "detail": str(exc)}


@app.get("/v1/ui/settings/backup")
async def backup_ui_settings() -> dict[str, Any]:
    """Return a JSON backup of current UI settings.

    This includes agent config, dialogue model profile, credential presence map,
    and metadata with an export timestamp.
    """
    data = await get_ui_settings()
    return {
        "version": 1,
        "format": "ui_settings",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "data": data,
    }


@app.get("/v1/attachments/{att_id}")
async def download_attachment(att_id: str, request: Request):
    """Download an attachment stored in Postgres (no local files).

    Enforces auth/tenant scoping and quarantine policy.
    """
    try:
        att_uuid = uuid.UUID(att_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid attachment id")

    # Basic authz: include attachment id in context; OPA may consult tenant/session
    _ = await authorize_request(request, {"action": "attachments.download", "id": att_id})

    store = get_attachments_store()
    meta = await store.get_metadata(att_uuid)
    if not meta:
        raise HTTPException(status_code=404, detail="not found")

    # Quarantine policy: block downloads when status is quarantined (store_and_block)
    if meta.status == "quarantined":
        raise HTTPException(status_code=403, detail="attachment quarantined")

    content = await store.get_content(att_uuid)
    if content is None:
        raise HTTPException(status_code=410, detail="content unavailable")

    headers = {
        "Content-Type": meta.mime or "application/octet-stream",
        "Content-Disposition": f"attachment; filename={meta.filename}",
    }

    async def streamer():
        # Chunk the in-memory bytes to avoid sending as one huge payload
        view = memoryview(content)
        chunk_size = 64 * 1024
        for i in range(0, len(view), chunk_size):
            yield bytes(view[i : i + chunk_size])

    return StreamingResponse(streamer(), headers=headers)


def _require_internal_token(request: Request) -> dict[str, str]:
    """Validate internal service token for internal-only endpoints.

    Returns a dict with optional tenant context derived from headers.
    """
    provided = request.headers.get("x-internal-token") or request.headers.get("X-Internal-Token")
    expected = os.getenv("GATEWAY_INTERNAL_TOKEN", "")
    if not expected or not provided or provided != expected:
        raise HTTPException(status_code=403, detail="forbidden (internal)")
    # Optional tenant scoping header for additional checks
    tenant = request.headers.get("x-tenant-id") or request.headers.get("X-Tenant-Id")
    return {"tenant": tenant} if tenant else {}


@app.get("/internal/attachments/{att_id}/binary")
async def internal_download_attachment(att_id: str, request: Request):
    """Internal service-to-service attachment fetch.

    - Requires X-Internal-Token header matching GATEWAY_INTERNAL_TOKEN.
    - Optional X-Tenant-Id header to enforce tenant scoping against stored metadata.
    - Unlike the public endpoint, quarantined attachments are still retrievable for ingestion
      (status is surfaced via X-Attachment-Status), leaving policy to the caller.
    """
    _ctx = _require_internal_token(request)
    try:
        att_uuid = uuid.UUID(att_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid attachment id")

    store = get_attachments_store()
    meta = await store.get_metadata(att_uuid)
    if not meta:
        raise HTTPException(status_code=404, detail="not found")

    # If caller supplied a tenant, enforce equality
    tenant_hdr = _ctx.get("tenant")
    if tenant_hdr and (meta.tenant or "") != tenant_hdr:
        raise HTTPException(status_code=403, detail="tenant mismatch")

    content = await store.get_content(att_uuid)
    if content is None:
        raise HTTPException(status_code=410, detail="content unavailable")

    headers = {
        "Content-Type": meta.mime or "application/octet-stream",
        "Content-Disposition": f"attachment; filename={meta.filename}",
        "X-Attachment-Status": meta.status,
        "X-Attachment-Size": str(meta.size),
    }

    async def streamer():
        view = memoryview(content)
        chunk_size = 64 * 1024
        for i in range(0, len(view), chunk_size):
            yield bytes(view[i : i + chunk_size])

    return StreamingResponse(streamer(), headers=headers)


@app.head("/internal/attachments/{att_id}/binary")
async def internal_head_attachment(att_id: str, request: Request) -> Response:
    """Return metadata headers for an attachment without the body (internal-only).

    Mirrors the GET endpoint's header contract to enable size/status checks
    without transferring content. Requires the same internal token and
    optional tenant scoping.
    """
    _ctx = _require_internal_token(request)
    try:
        att_uuid = uuid.UUID(att_id)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid attachment id")

    store = get_attachments_store()
    meta = await store.get_metadata(att_uuid)
    if not meta:
        raise HTTPException(status_code=404, detail="not found")

    tenant_hdr = _ctx.get("tenant")
    if tenant_hdr and (meta.tenant or "") != tenant_hdr:
        raise HTTPException(status_code=403, detail="tenant mismatch")

    headers = {
        "Content-Type": meta.mime or "application/octet-stream",
        "Content-Disposition": f"attachment; filename={meta.filename}",
        "X-Attachment-Status": meta.status,
        "X-Attachment-Size": str(meta.size),
    }
    # No body for HEAD response; just return headers
    return Response(status_code=200, headers=headers)


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


# -----------------------------
# Centralized LLM Invoke (single source of truth)
# -----------------------------

# -----------------------------
# Audit admin endpoints
# -----------------------------


class AuditExportQuery(BaseModel):
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant: Optional[str] = None
    action: Optional[str] = None


@app.get("/v1/admin/audit/export")
async def audit_export(
    request: Request,
    request_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    tenant: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
) -> StreamingResponse:
    """Export audit events as NDJSON (admin-only).

    Filters are optional; when absent, returns recent events in ascending id order.
    """
    await _enforce_admin_rate_limit(request)
    auth = await authorize_request(request, {
        "request_id": request_id,
        "session_id": session_id,
        "tenant": tenant,
        "action": action,
    })
    _require_admin_scope(auth)

    store = get_audit_store()

    async def _streamer():
        import json as _json
        after_id: Optional[int] = None
        yielded = 0
        # simple bounded window to avoid infinite streams
        max_rows = 10000
        while yielded < max_rows:
            rows = await store.list(
                request_id=request_id,
                session_id=session_id,
                tenant=tenant,
                action=action,
                limit=500,
                after_id=after_id,
            )
            if not rows:
                break
            for r in rows:
                obj = {
                    "id": r.id,
                    "ts": r.ts.isoformat() + "Z",
                    "request_id": r.request_id,
                    "trace_id": r.trace_id,
                    "session_id": r.session_id,
                    "tenant": r.tenant,
                    "subject": r.subject,
                    "action": r.action,
                    "resource": r.resource,
                    "target_id": r.target_id,
                    "ip": r.ip,
                    "user_agent": r.user_agent,
                    "details": r.details,
                    "diff": r.diff,
                }
                line = _json.dumps(obj, ensure_ascii=False) + "\n"
                yield line.encode("utf-8")
                yielded += 1
                after_id = r.id
            if len(rows) < 500:
                break
    return StreamingResponse(_streamer(), headers={"Content-Type": "application/x-ndjson"})

class LlmInvokeMessage(BaseModel):
    role: str
    content: str


class LlmInvokeOverrides(BaseModel):
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    kwargs: Optional[Dict[str, Any]] = None


class LlmInvokeRequest(BaseModel):
    role: str = Field(..., pattern="^(dialogue|escalation)$")
    session_id: Optional[str] = None
    persona_id: Optional[str] = None
    tenant: Optional[str] = None
    messages: List[LlmInvokeMessage]
    overrides: Optional[LlmInvokeOverrides] = None


def _gateway_slm_client() -> SLMClient:
    # Create a fresh client per request to avoid credential races; caller closes it.
    return SLMClient()


async def _resolve_profile_and_creds(payload: LlmInvokeRequest) -> tuple[str, str, float, dict[str, Any]]:
    """Return (model, base_url, temperature, extra_kwargs) after applying overrides and normalization.

    Raises HTTPException on config/credentials errors.
    """
    # Load profile for role/deployment
    profile = await PROFILE_STORE.get(payload.role, APP_SETTINGS.deployment_mode)
    if not profile and not payload.overrides:
        raise HTTPException(status_code=400, detail="model profile not configured for role")

    model = (payload.overrides.model if payload.overrides and payload.overrides.model else (profile.model if profile else "")).strip()
    base_url_raw = (payload.overrides.base_url if payload.overrides and payload.overrides.base_url else (profile.base_url if profile else ""))
    base_url = _normalize_llm_base_url(str(base_url_raw))
    try:
        temperature = float(payload.overrides.temperature) if (payload.overrides and payload.overrides.temperature is not None) else (float(profile.temperature) if profile else 0.2)
    except Exception:
        temperature = 0.2
    extra_kwargs: dict[str, Any] = {}
    if profile and isinstance(profile.kwargs, dict):
        extra_kwargs.update(profile.kwargs)
    if payload.overrides and isinstance(payload.overrides.kwargs, dict):
        extra_kwargs.update(payload.overrides.kwargs)

    if not model or not base_url:
        raise HTTPException(status_code=400, detail="invalid model/base_url after normalization")

    provider = _detect_provider_from_base(base_url)
    # Fetch credentials (fail-closed)
    store = get_llm_credentials_store()
    secret = await store.get(provider)
    if not secret:
        raise HTTPException(status_code=404, detail=f"credentials not found for provider: {provider}")

    return model, base_url, temperature, {**extra_kwargs, "_provider": provider, "_secret": secret}


@app.post("/v1/llm/invoke")
async def llm_invoke(payload: LlmInvokeRequest, request: Request) -> dict:
    # Only allow internal calls
    if not _internal_token_ok(request):
        raise HTTPException(status_code=403, detail="forbidden")

    model, base_url, temperature, meta = await _resolve_profile_and_creds(payload)

    # Prepare messages for SLMClient
    messages = [ChatMessage(role=m.role, content=m.content) for m in payload.messages]

    client = _gateway_slm_client()
    # Inject credential into this ephemeral client
    client.api_key = meta["_secret"]
    # Audit/tracing context
    try:
        from opentelemetry import trace as _trace
        ctx = _trace.get_current_span().get_span_context()
        trace_id_hex = f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
    except Exception:
        trace_id_hex = None

    req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")

    start = time.time()
    try:
        content, usage = await client.chat(
            messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            **{k: v for k, v in meta.items() if not k.startswith("_")},
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        # Audit error
        try:
            await get_audit_store().log(
                request_id=req_id,
                trace_id=trace_id_hex,
                session_id=payload.session_id,
                tenant=payload.tenant,
                subject=None,
                action="llm.invoke",
                resource="llm.chat",
                target_id=None,
                details={
                    "provider": meta.get("_provider"),
                    "model": model,
                    "base_url": base_url,
                    "status": "error",
                    "http_status": status,
                    "error_type": type(exc).__name__,
                },
                diff=None,
                ip=getattr(request.client, "host", None) if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:
            LOGGER.debug("Failed to write audit log for llm.invoke error", exc_info=True)
        raise HTTPException(status_code=status, detail=f"provider_error: {exc}") from exc
    except httpx.RequestError as exc:
        # Audit timeout
        try:
            await get_audit_store().log(
                request_id=req_id,
                trace_id=trace_id_hex,
                session_id=payload.session_id,
                tenant=payload.tenant,
                subject=None,
                action="llm.invoke",
                resource="llm.chat",
                target_id=None,
                details={
                    "provider": meta.get("_provider"),
                    "model": model,
                    "base_url": base_url,
                    "status": "timeout",
                    "error_type": type(exc).__name__,
                },
                diff=None,
                ip=getattr(request.client, "host", None) if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:
            LOGGER.debug("Failed to write audit log for llm.invoke timeout", exc_info=True)
        raise HTTPException(status_code=504, detail=f"provider_timeout: {exc}") from exc
    finally:
        try:
            await client.close()
        except Exception:
            pass

    # Successful audit
    try:
        elapsed = max(0.0, time.time() - start)
        await get_audit_store().log(
            request_id=req_id,
            trace_id=trace_id_hex,
            session_id=payload.session_id,
            tenant=payload.tenant,
            subject=None,
            action="llm.invoke",
            resource="llm.chat",
            target_id=None,
            details={
                "provider": meta.get("_provider"),
                "model": model,
                "base_url": base_url,
                "status": "ok",
                "latency_ms": int(elapsed * 1000),
                "usage": usage,
            },
            diff=None,
            ip=getattr(request.client, "host", None) if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        LOGGER.debug("Failed to write audit log for llm.invoke", exc_info=True)

    return {
        "content": content,
        "usage": usage,
        "model": model,
        "base_url": base_url,
    }


@app.post("/v1/llm/invoke/stream")
async def llm_invoke_stream(payload: LlmInvokeRequest, request: Request):
    # Only allow internal calls
    if not _internal_token_ok(request):
        raise HTTPException(status_code=403, detail="forbidden")

    model, base_url, temperature, meta = await _resolve_profile_and_creds(payload)
    messages = [ChatMessage(role=m.role, content=m.content) for m in payload.messages]

    client = _gateway_slm_client()
    client.api_key = meta["_secret"]

    # Audit/tracing context
    try:
        from opentelemetry import trace as _trace
        ctx = _trace.get_current_span().get_span_context()
        trace_id_hex = f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
    except Exception:
        trace_id_hex = None
    req_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    start = time.time()

    async def streamer():
        try:
            async for chunk in client.chat_stream(
                messages,
                model=model,
                base_url=base_url,
                temperature=temperature,
                **{k: v for k, v in meta.items() if not k.startswith("_")},
            ):
                # Re-emit upstream chunk as OpenAI-style SSE data line
                import json as _json
                line = "data: " + _json.dumps(chunk, ensure_ascii=False) + "\n\n"
                yield line.encode("utf-8")
        except httpx.HTTPStatusError as exc:
            detail = f"provider_error: {exc}"
            # Audit error
            try:
                status = exc.response.status_code if exc.response is not None else 502
                await get_audit_store().log(
                    request_id=req_id,
                    trace_id=trace_id_hex,
                    session_id=payload.session_id,
                    tenant=payload.tenant,
                    subject=None,
                    action="llm.invoke.stream",
                    resource="llm.chat",
                    target_id=None,
                    details={
                        "provider": meta.get("_provider"),
                        "model": model,
                        "base_url": base_url,
                        "status": "error",
                        "http_status": status,
                        "error_type": type(exc).__name__,
                    },
                    diff=None,
                    ip=getattr(request.client, "host", None) if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
            except Exception:
                LOGGER.debug("Failed to write audit log for llm.invoke.stream error", exc_info=True)
            msg = "data: " + "{\"error\": \"" + detail.replace("\n", " ") + "\"}" + "\n\n"
            yield msg.encode("utf-8")
        except httpx.RequestError as exc:
            detail = f"provider_timeout: {exc}"
            try:
                await get_audit_store().log(
                    request_id=req_id,
                    trace_id=trace_id_hex,
                    session_id=payload.session_id,
                    tenant=payload.tenant,
                    subject=None,
                    action="llm.invoke.stream",
                    resource="llm.chat",
                    target_id=None,
                    details={
                        "provider": meta.get("_provider"),
                        "model": model,
                        "base_url": base_url,
                        "status": "timeout",
                        "error_type": type(exc).__name__,
                    },
                    diff=None,
                    ip=getattr(request.client, "host", None) if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
            except Exception:
                LOGGER.debug("Failed to write audit log for llm.invoke.stream timeout", exc_info=True)
            msg = "data: " + "{\"error\": \"" + detail.replace("\n", " ") + "\"}" + "\n\n"
            yield msg.encode("utf-8")
        finally:
            # Close client and send [DONE]
            try:
                await client.close()
            except Exception:
                pass
            # Success audit at end of stream
            try:
                elapsed = max(0.0, time.time() - start)
                await get_audit_store().log(
                    request_id=req_id,
                    trace_id=trace_id_hex,
                    session_id=payload.session_id,
                    tenant=payload.tenant,
                    subject=None,
                    action="llm.invoke.stream",
                    resource="llm.chat",
                    target_id=None,
                    details={
                        "provider": meta.get("_provider"),
                        "model": model,
                        "base_url": base_url,
                        "status": "ok",
                        "latency_ms": int(elapsed * 1000),
                    },
                    diff=None,
                    ip=getattr(request.client, "host", None) if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
            except Exception:
                LOGGER.debug("Failed to write audit log for llm.invoke.stream", exc_info=True)
            yield b"data: [DONE]\n\n"

    headers = {"Content-Type": "text/event-stream"}
    return StreamingResponse(streamer(), headers=headers)
