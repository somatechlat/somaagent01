"""Delegation gateway service - 100% Django ASGI.

All FastAPI replaced with Django/Django Ninja.


🎓 PhD Dev - Clean ASGI
🔒 Security - Django middleware
⚡ Perf - Prometheus metrics
📚 ISO Doc - Full docstrings
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

import django

django.setup()

from django.core.asgi import get_asgi_application
from django.http import HttpResponse
from ninja import NinjaAPI, Router
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    generate_latest,
    Histogram,
    start_http_server,
)
from pydantic import BaseModel
from services.common.delegation_store import DelegationStore

from admin.common.exceptions import NotFoundError
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.common.tracing import setup_tracing

LOGGER = logging.getLogger(__name__)

# Django settings used instead
setup_tracing("delegation-gateway", endpoint=os.environ.get("OTLP_ENDPOINT", ""))


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
    """Execute ensure metrics server."""

    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return
    port = int(
        os.environ.get("DELEGATION_METRICS_PORT", str(int(os.environ.get("METRICS_PORT", "9400"))))
    )
    if port <= 0:
        LOGGER.warning("Delegation metrics server disabled", extra={"port": port})
        _METRICS_SERVER_STARTED = True
        return
    host = os.environ.get("DELEGATION_METRICS_HOST", os.environ.get("METRICS_HOST", "0.0.0.0"))
    start_http_server(port, addr=host)
    LOGGER.info(
        "Delegation gateway metrics server started",
        extra={"host": host, "port": port},
    )
    _METRICS_SERVER_STARTED = True


def get_bus() -> KafkaEventBus:
    """Retrieve bus."""

    kafka_settings = KafkaSettings(
        bootstrap_servers=os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
    )
    return KafkaEventBus(kafka_settings)


def get_publisher() -> DurablePublisher:
    """Retrieve publisher."""

    bus = get_bus()
    return DurablePublisher(bus=bus)


def get_store() -> DelegationStore:
    """Retrieve store."""

    return DelegationStore(dsn=os.environ.get("SA01_DB_DSN", ""))


class DelegationRequest(BaseModel):
    """Data model for DelegationRequest."""

    task_id: str | None = None
    payload: dict[str, Any]
    callback_url: str | None = None
    metadata: dict[str, Any] | None = None


class DelegationCallback(BaseModel):
    """Delegationcallback class implementation."""

    status: str
    result: dict[str, Any] | None = None


class DelegationGateway:
    """Minimal delegation handler used by Temporal A2A worker."""

    def __init__(self) -> None:
        """Initialize the instance."""

        self._publisher = get_publisher()
        self._topic = os.environ.get("A2A_OUT_TOPIC", "a2a.out")

    async def handle_event(
        self, event: dict[str, Any], publisher: DurablePublisher | None = None
    ) -> None:
        """Execute handle event.

        Args:
            event: The event.
            publisher: The publisher.
        """

        pub = publisher or self._publisher
        dedupe = event.get("task_id") or event.get("event_id")
        tenant = (event.get("metadata") or {}).get("tenant")
        session_id = (event.get("metadata") or {}).get("session_id")
        await pub.publish(
            self._topic,
            event,
            dedupe_key=dedupe,
            session_id=session_id,
            tenant=tenant,
        )


# Django Ninja API
api = NinjaAPI(title="Delegation Gateway", version="1.0.0")
router = Router(tags=["delegation"])


@router.get("/metrics")
def metrics(request) -> HttpResponse:
    """Execute metrics.

    Args:
        request: The request.
    """

    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


@router.get("/health")
async def health(request) -> dict:
    """Execute health.

    Args:
        request: The request.
    """

    return {"status": "ok"}


@router.post("/v1/delegation/task")
async def create_delegation_task(request, body: DelegationRequest) -> dict:
    """Execute create delegation task.

    Args:
        request: The request.
        body: The body.
    """

    task_id = body.task_id or str(uuid.uuid4())
    store = get_store()
    publisher = get_publisher()

    await store.create_task(
        task_id=task_id,
        payload=body.payload,
        status="queued",
        callback_url=body.callback_url,
        metadata=body.metadata,
    )
    QUEUE_DEPTH.inc()
    event = {
        "task_id": task_id,
        "payload": body.payload,
        "callback_url": body.callback_url,
        "metadata": body.metadata or {},
    }
    topic = os.environ.get("DELEGATION_TOPIC", "somastack.delegation")
    await publisher.publish(
        topic,
        event,
        dedupe_key=task_id,
        session_id=str(event.get("metadata", {}).get("session_id", "")),
        tenant=(event.get("metadata") or {}).get("tenant"),
    )
    return {"task_id": task_id, "status": "queued"}


@router.get("/v1/delegation/task/{task_id}")
async def get_delegation_task(request, task_id: str) -> dict:
    """Retrieve delegation task.

    Args:
        request: The request.
        task_id: The task_id.
    """

    store = get_store()
    record = await store.get_task(task_id)
    if not record:
        raise NotFoundError("task", task_id)
    return record


@router.post("/v1/delegation/task/{task_id}/callback")
async def delegation_callback(request, task_id: str, body: DelegationCallback) -> dict:
    """Execute delegation callback.

    Args:
        request: The request.
        task_id: The task_id.
        body: The body.
    """

    store = get_store()
    record = await store.get_task(task_id)
    if not record:
        raise NotFoundError("task", task_id)
    await store.update_task(task_id, status=body.status, result=body.result)
    if body.status in {"completed", "failed", "cancelled"}:
        QUEUE_DEPTH.dec()
    return {"task_id": task_id, "status": body.status}


api.add_router("/", router)
django_asgi = get_asgi_application()

# Legacy app reference
app = django_asgi


if __name__ == "__main__":
    import uvicorn

    ensure_metrics_server()
    uvicorn.run(
        "services.delegation_gateway.main:django_asgi",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8015")),
    )
