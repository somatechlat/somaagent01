"""Requeue management service for SomaAgent 01."""

from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.requeue_store import RequeueStore
from services.common.settings_sa01 import SA01Settings
from services.common.tracing import setup_tracing

setup_logging()
LOGGER = logging.getLogger(__name__)

APP_SETTINGS = SA01Settings.from_env()
setup_tracing("requeue-service", endpoint=APP_SETTINGS.otlp_endpoint)

app = FastAPI(title="SomaAgent 01 Requeue Service")


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


def get_store() -> RequeueStore:
    prefix = os.getenv(
        "POLICY_REQUEUE_PREFIX",
        APP_SETTINGS.extra.get("policy_requeue_prefix", "policy:requeue"),
    )
    return RequeueStore(url=_redis_url(), prefix=prefix)


def get_bus() -> KafkaEventBus:
    return KafkaEventBus(_kafka_settings())


class RequeueOverride(BaseModel):
    allow: bool = True


@app.get("/v1/requeue")
async def list_requeue(store: RequeueStore = Depends(get_store)) -> list[dict]:
    return await store.list()


@app.post("/v1/requeue/{requeue_id}/resolve")
async def resolve_requeue(
    requeue_id: str,
    payload: RequeueOverride,
    store: RequeueStore = Depends(get_store),
    bus: KafkaEventBus = Depends(get_bus),
) -> dict[str, str]:
    entry = await store.get(requeue_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Requeue entry not found")

    await store.remove(requeue_id)
    if payload.allow:
        entry.setdefault("metadata", {})
        entry["metadata"]["requeue_override"] = True
        await bus.publish(os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"), entry)
        status = "requeued"
    else:
        status = "discarded"

    LOGGER.info(
        "Resolved requeue entry",
        extra={"requeue_id": requeue_id, "status": status, "allowed": payload.allow},
    )

    return {"status": status}


@app.delete("/v1/requeue/{requeue_id}")
async def delete_requeue(
    requeue_id: str, store: RequeueStore = Depends(get_store)
) -> dict[str, str]:
    await store.remove(requeue_id)
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8012")))
