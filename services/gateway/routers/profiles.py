"""Model/agent profile endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.model_profiles import ModelProfile, ModelProfileStore

router = APIRouter(prefix="/v1", tags=["profiles"])
STORE = ModelProfileStore()


class ModelProfileCreate(BaseModel):
    role: str
    deployment_mode: str
    config: dict


@router.get("/model-profiles")
async def list_model_profiles():
    return await STORE.list()


@router.post("/model-profiles", status_code=201)
async def create_model_profile(body: ModelProfileCreate):
    profile = ModelProfile(role=body.role, deployment_mode=body.deployment_mode, config=body.config)
    await STORE.upsert(profile)
    return {"status": "created"}


@router.put("/model-profiles/{role}/{deployment_mode}")
async def update_model_profile(role: str, deployment_mode: str, body: ModelProfileCreate):
    profile = ModelProfile(role=role, deployment_mode=deployment_mode, config=body.config)
    await STORE.upsert(profile)
    return {"status": "updated"}


@router.delete("/model-profiles/{role}/{deployment_mode}")
async def delete_model_profile(role: str, deployment_mode: str):
    deleted = await STORE.delete(role, deployment_mode)
    if not deleted:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return {"deleted": f"{role}/{deployment_mode}"}


@router.get("/agents/profiles")
async def list_agent_profiles():
    return await STORE.list()
