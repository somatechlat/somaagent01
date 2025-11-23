"""Delegation gateway service for SomaAgent 01."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    generate_latest,
    Histogram,
    start_http_server,
)
from pydantic import BaseModel
from starlette.responses import Response

# Legacy settings removed – use central config façade instead.
# Legacy ADMIN_SETTINGS import removed – configuration accessed via `cfg.settings()`.
from services.common.delegation_store import DelegationStore
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.outbox_repository import ensure_schema as ensure_outbox_schema, OutboxStore
from services.common.publisher import DurablePublisher
from services.common.tracing import setup_tracing
from src.core.config import cfg

setup_logging()
LOGGER = logging.getLogger(__name__)

# ``cfg.settings()`` provides the same fields that ``SA01Settings`` exposed.
setup_tracing("delegation-gateway", endpoint=cfg.settings().external.otlp_endpoint)

app = FastAPI(title="SomaAgent 01 Delegation Gateway")


REQUEST_COUNT = Counter(
    "delegation_gateway_requests_total",
    "HTTP requests processed by the delegation gateway",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "delegation_gateway_request_duration_seconds",
    "Latency of HTTP requests processed by the delegation gateway",
    ["method", "path"],
)

QUEUE_DEPTH = Gauge(
    "delegation_gateway_tasks_inflight",
    "Number of delegation tasks currently queued",
)

_METRICS_SERVER_STARTED = False


def ensure_metrics_server() -> None:
    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return
    port = int(cfg.env("DELEGATION_METRICS_PORT", str(cfg.settings().service.metrics_port)))
    if port <= 0:
        LOGGER.warning("Delegation metrics server disabled", extra={"port": port})
        _METRICS_SERVER_STARTED = True
        return
    host = cfg.env("DELEGATION_METRICS_HOST", cfg.settings().service.host)
    start_http_server(port, addr=host)
    LOGGER.info(
        "Delegation gateway metrics server started",
        extra={"host": host, "port": port},
    )
    _METRICS_SERVER_STARTED = True


def get_bus() -> KafkaEventBus:
    kafka_settings = KafkaSettings(
        bootstrap_servers=cfg.settings().kafka.bootstrap_servers,
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )
    return KafkaEventBus(kafka_settings)


def get_publisher() -> DurablePublisher:
    # Shared durable publisher; construct lazily for DI, ensure outbox schema
    # on first use to avoid race at startup.
    bus = get_bus()
    outbox = OutboxStore(dsn=cfg.settings().database.dsn)
    # best-effort ensure schema
    try:
        import asyncio as _asyncio

        async def _ensure():
            await ensure_outbox_schema(outbox)

        # If already in an event loop (typical in FastAPI), schedule it
        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_ensure())
        else:
            loop.run_until_complete(_ensure())
    except Exception:
        LOGGER.debug("Outbox schema ensure failed", exc_info=True)
    return DurablePublisher(bus=bus, outbox=outbox)


def get_store() -> DelegationStore:
    return DelegationStore(dsn=cfg.settings().database.dsn)


class DelegationRequest(BaseModel):
    task_id: str | None = None
    payload: dict[str, Any]
    callback_url: str | None = None
    metadata: dict[str, Any] | None = None


class DelegationCallback(BaseModel):
    status: str
    result: dict[str, Any] | None = None


@app.on_event("startup")
async def startup_event() -> None:
    ensure_metrics_server()
    store = DelegationStore(dsn=cfg.settings().database.dsn)
    await store.ensure_schema()


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start_time

    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)

    REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()

    return response


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/delegation/task")
async def create_delegation_task(
    request: DelegationRequest,
    publisher: DurablePublisher = Depends(get_publisher),
    store: DelegationStore = Depends(get_store),
) -> dict[str, str]:
    task_id = request.task_id or str(uuid.uuid4())
    await store.create_task(
        task_id=task_id,
        payload=request.payload,
        status="queued",
        callback_url=request.callback_url,
        metadata=request.metadata,
    )
    QUEUE_DEPTH.inc()
    event = {
        "task_id": task_id,
        "payload": request.payload,
        "callback_url": request.callback_url,
        "metadata": request.metadata or {},
    }
    topic = cfg.env("DELEGATION_TOPIC", "somastack.delegation")
    await publisher.publish(
        topic,
        event,
        dedupe_key=task_id,
        session_id=str(event.get("metadata", {}).get("session_id", "")),
        tenant=(event.get("metadata") or {}).get("tenant"),
    )
    return {"task_id": task_id, "status": "queued"}


@app.get("/v1/delegation/task/{task_id}")
async def get_delegation_task(
    task_id: str,
    store: DelegationStore = Depends(get_store),
) -> dict[str, Any]:
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


@app.post("/v1/delegation/task/{task_id}/callback")
async def delegation_callback(
    task_id: str,
    payload: DelegationCallback,
    store: DelegationStore = Depends(get_store),
) -> dict[str, Any]:
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    await store.update_task(task_id, status=payload.status, result=payload.result)
    if payload.status in {"completed", "failed", "cancelled"}:
        QUEUE_DEPTH.dec()
    return {"task_id": task_id, "status": payload.status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(cfg.env("PORT", "8015")))
