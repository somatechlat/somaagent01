"""UI settings endpoints extracted from gateway monolith (minimal functional)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.ui_settings_store import UiSettingsStore

router = APIRouter(prefix="/v1/ui/settings", tags=["ui"])
STORE = UiSettingsStore()


class UiSettingsUpdate(BaseModel):
    data: dict


@router.get("")
async def get_settings():
    return await STORE.get()


@router.put("")
async def put_settings(body: UiSettingsUpdate):
    await STORE.save(body.data)
    return {"status": "ok"}
