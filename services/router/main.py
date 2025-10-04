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

from services.common.telemetry_store import TelemetryStore

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Router")


def get_store() -> TelemetryStore:
    return TelemetryStore()


class RouteRequest(BaseModel):
    role: str = Field(default="dialogue")
    candidates: list[str]
    deployment_mode: str = Field(default="LOCAL")


class RouteResponse(BaseModel):
    model: str
    score: float


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
    return RouteResponse(model=payload.candidates[0], score=0.0)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8013")))
