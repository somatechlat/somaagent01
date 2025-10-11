"""Settings service for managing model profiles."""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.common.model_profiles import ModelProfile, ModelProfileStore

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Settings Service")


def get_store() -> ModelProfileStore:
    return ModelProfileStore()


class ModelProfilePayload(BaseModel):
    role: str
    deployment_mode: str = Field(default="LOCAL")
    model: str
    base_url: str
    temperature: float = Field(default=0.2)
    extra: dict[str, str] = Field(default_factory=dict)


@app.on_event("startup")
async def startup_event() -> None:
    store = ModelProfileStore()
    await store.ensure_schema()
    await store._ensure_pool()


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
