"""UI settings endpoints extracted from gateway monolith (minimal functional)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.ui_settings_store import UiSettingsStore

# Updated to remove redundant '/ui' segment as per new architecture.
router = APIRouter(prefix="/v1/settings", tags=["settings"])
STORE = UiSettingsStore()


class UiSettingsUpdate(BaseModel):
    data: dict


@router.get("")
async def get_settings() -> dict:
    """Return UI settings from the persistent store.

    The endpoint now **does not provide any in‑memory fallback**. If the
    ``UiSettingsStore`` cannot be accessed or the data is malformed, a
    ``500`` HTTPException is raised so the caller can handle the error
    explicitly. This complies with the request to remove all legacy fallback
    logic.
    """
    await STORE.ensure_schema()
    data = await STORE.get()
    if not isinstance(data, dict) or not data.get("sections"):
        raise HTTPException(status_code=500, detail="UI settings sections missing")
    return data


# The UI expects the settings schema under the ``/sections`` sub‑path.
# Adjust the routes to match the ``API.UI_SETTINGS`` constant ("/settings/sections").
@router.get("/sections")
async def get_settings_sections() -> dict:
    """Return only the ``sections`` part of the UI settings.

    No fallback is provided; errors are propagated as ``HTTPException``
    responses.
    """
    await STORE.ensure_schema()
    data = await STORE.get()
    if not isinstance(data, dict) or not data.get("sections"):
        raise HTTPException(status_code=500, detail="UI settings sections missing")
    return {"sections": data["sections"]}

@router.put("/sections")
async def put_settings(body: UiSettingsUpdate):
    """Persist UI settings sections.

    The original implementation called ``STORE.save`` which does not exist on
    :class:`UiSettingsStore`. The correct method is ``set``. We also ensure the
    table exists before writing.
    """
    await STORE.ensure_schema()
    await STORE.set(body.data)
    return {"status": "ok"}
