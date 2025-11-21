"""Runtime config router extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter

from src.core.config import cfg
from services.common.ui_settings_store import UiSettingsStore
from services.common.admin_settings import ADMIN_SETTINGS
from services.common.attachments_store import AttachmentsStore

router = APIRouter(prefix="/v1", tags=["runtime-config"])

_ATTACHMENTS_STORE: AttachmentsStore | None = None


def _get_attachments_store() -> AttachmentsStore:
    global _ATTACHMENTS_STORE
    if _ATTACHMENTS_STORE is None:
        _ATTACHMENTS_STORE = AttachmentsStore(dsn=ADMIN_SETTINGS.postgres_dsn)
    return _ATTACHMENTS_STORE


@router.get("/runtime-config")
async def get_runtime_config() -> dict:
    """Return UI-safe snapshot of runtime flags and derived state."""
    auth_cfg = {
        "require_auth": cfg.flag("AUTH_REQUIRED") or bool(cfg.env("AUTH_REQUIRED", False)),
        "opa_configured": bool(cfg.opa_url()),
    }

    sse_cfg = {"enabled": str(cfg.env("SSE_ENABLED", "true")).lower() in {"true", "1", "yes", "on"}}

    uploads_defaults = {
        "uploads_enabled": True,
        "uploads_max_mb": 25,
        "uploads_max_files": 10,
    }

    try:
        ui_doc = await UiSettingsStore().get()
    except Exception:
        ui_doc = None

    uploads_cfg = uploads_defaults | (ui_doc.get("uploads", {}) if ui_doc else {})

    # Attachments: report current disk usage and quota if available
    attachments = {}
    try:
        store = _get_attachments_store()
        attachments = {
            "disk_usage_bytes": await store.disk_usage_bytes(),
            "max_bytes": store.max_size_bytes,
        }
    except Exception:
        attachments = {}

    return {
        "auth": auth_cfg,
        "sse": sse_cfg,
        "uploads": uploads_cfg,
        "attachments": attachments,
    }
