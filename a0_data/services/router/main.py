"""Dynamic routing service for SomaAgent 01.

This service scores available SLM providers based on telemetry and returns
routing decisions. Currently it supports OSS providers only. When additional
providers come online, extend the PROVIDERS list.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.common.logging_config import setup_logging
from services.common.memory_client import MemoryClient
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry_store import TelemetryStore
from services.common.tracing import setup_tracing

setup_logging()
LOGGER = logging.getLogger(__name__)

APP_SETTINGS = SA01Settings.from_env()
setup_tracing("router-service", endpoint=APP_SETTINGS.otlp_endpoint)

TELEMETRY_STORE = TelemetryStore.from_settings(APP_SETTINGS)
MEMORY_CLIENT = MemoryClient(settings=APP_SETTINGS)

app = FastAPI(title="SomaAgent 01 Router")


def get_store() -> TelemetryStore:
    return TELEMETRY_STORE


class RouteRequest(BaseModel):
    role: str = Field(default="dialogue")
    candidates: list[str]
    deployment_mode: str = Field(default=APP_SETTINGS.deployment_mode)
    tenant: str = Field(default="default")
    persona_id: str | None = None


class RouteResponse(BaseModel):
    model: str
    score: float


@app.on_event("startup")
async def on_startup() -> None:
    await TELEMETRY_STORE._ensure_pool()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await MEMORY_CLIENT.close()


@app.post("/v1/route", response_model=RouteResponse)
async def route_decision(
    payload: RouteRequest,
    store: Annotated[TelemetryStore, Depends(get_store)],
) -> RouteResponse:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT model, score
            FROM model_scores
            WHERE deployment_mode = $1 AND model = ANY($2)
            ORDER BY score DESC
            LIMIT 1
            """,
            payload.deployment_mode,
            payload.candidates,
        )
    if rows:
        row = rows[0]
        return RouteResponse(model=row["model"], score=row["score"])

    # Fallback: pick first candidate
    if not payload.candidates:
        raise HTTPException(status_code=400, detail="No candidates supplied")

    # Try to reuse recently successful model decisions stored via the memory service.
    try:
        memories = await MEMORY_CLIENT.list_memories(
            tenant=payload.tenant,
            persona_id=payload.persona_id,
            limit=5,
        )
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.debug("Memory lookup failed", exc_info=True)
    else:
        for record in memories:
            preferred = record.metadata.get("model") or record.metadata.get("tool_model")
            if preferred and preferred in payload.candidates:
                return RouteResponse(model=preferred, score=0.05)

    return RouteResponse(model=payload.candidates[0], score=0.0)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8013")))
