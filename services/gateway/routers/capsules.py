"""Capsule endpoints extracted from gateway monolith (minimal functional)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.capsule_store import CapsuleRecord, CapsuleStore

router = APIRouter(prefix="/v1/capsules", tags=["capsules"])
STORE = CapsuleStore()


class InstallRequest(BaseModel):
    capsule_id: str


@router.get("", response_model=List[CapsuleRecord])
async def list_capsules():
    return await STORE.list()


@router.get("/{capsule_id}")
async def get_capsule(capsule_id: str):
    rec = await STORE.get(capsule_id)
    if not rec:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return rec


@router.post("/{capsule_id}/install")
async def install_capsule(capsule_id: str):
    ok = await STORE.install(capsule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return {"status": "installed", "id": capsule_id}
