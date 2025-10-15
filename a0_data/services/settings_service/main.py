"""Settings service for managing model profiles."""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.common.logging_config import setup_logging
from services.common.model_profiles import ModelProfile, ModelProfileStore
from services.common.settings_sa01 import SA01Settings
from services.common.tracing import setup_tracing

setup_logging()
LOGGER = logging.getLogger(__name__)

app = FastAPI(title="SomaAgent 01 Settings Service")
SVC_SETTINGS = SA01Settings.from_env()
setup_tracing("settings-service", endpoint=SVC_SETTINGS.otlp_endpoint)
PROFILE_STORE = ModelProfileStore.from_settings(SVC_SETTINGS)


def get_store() -> ModelProfileStore:
    return PROFILE_STORE


class ModelProfilePayload(BaseModel):
    role: str
    deployment_mode: str = Field(default=SVC_SETTINGS.deployment_mode)
    model: str
    base_url: str
    temperature: float = Field(default=0.2)
    extra: dict[str, Any] = Field(default_factory=dict)


@app.on_event("startup")
async def startup_event() -> None:
    await PROFILE_STORE.ensure_schema()
    await PROFILE_STORE._ensure_pool()
    await PROFILE_STORE.sync_from_settings(SVC_SETTINGS)


@app.get("/v1/model-profiles")
async def list_profiles(
    store: Annotated[ModelProfileStore, Depends(get_store)],
    deployment_mode: str | None = None,
) -> list[ModelProfile]:
    return await store.list(deployment_mode)


@app.post("/v1/model-profiles")
async def create_profile(
    payload: ModelProfilePayload,
    store: Annotated[ModelProfileStore, Depends(get_store)],
) -> dict[str, str]:
    profile = ModelProfile(
        role=payload.role,
        deployment_mode=payload.deployment_mode,
        model=payload.model,
        base_url=payload.base_url,
        temperature=payload.temperature,
        kwargs=payload.extra,
    )
    await store.upsert(profile)
    return {"status": "ok"}


@app.put("/v1/model-profiles/{role}/{deployment_mode}")
async def update_profile(
    role: str,
    deployment_mode: str,
    payload: ModelProfilePayload,
    store: Annotated[ModelProfileStore, Depends(get_store)],
) -> dict[str, str]:
    if payload.role != role or payload.deployment_mode != deployment_mode:
        raise HTTPException(status_code=400, detail="Role or deployment_mode mismatch")
    profile = ModelProfile(
        role=payload.role,
        deployment_mode=payload.deployment_mode,
        model=payload.model,
        base_url=payload.base_url,
        temperature=payload.temperature,
        kwargs=payload.extra,
    )
    await store.upsert(profile)
    return {"status": "ok"}


@app.delete("/v1/model-profiles/{role}/{deployment_mode}")
async def delete_profile(
    role: str,
    deployment_mode: str,
    store: Annotated[ModelProfileStore, Depends(get_store)],
) -> dict[str, str]:
    await store.delete(role, deployment_mode)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8011")))
