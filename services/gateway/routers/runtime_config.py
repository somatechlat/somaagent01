"""Runtime config router extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter

from services.common.attachments_store import AttachmentsStore
from services.common.ui_settings_store import UiSettingsStore
from src.core.config import cfg

router = APIRouter(prefix="/v1", tags=["runtime-config"])

_ATTACHMENTS_STORE: AttachmentsStore | None = None


def _get_attachments_store() -> AttachmentsStore:
    """Lazily create a singleton :class:`AttachmentsStore`.

    The historic implementation used ``ADMIN_SETTINGS.postgres_dsn`` which
    proxied to the legacy configuration object.  We now obtain the DSN
    directly from the canonical configuration singleton ``cfg``.
    """
    global _ATTACHMENTS_STORE
    if _ATTACHMENTS_STORE is None:
        # ``cfg.settings()`` returns the full ``Config`` model; the PostgreSQL
        # DSN lives under ``database.dsn``.
        _ATTACHMENTS_STORE = AttachmentsStore(dsn=cfg.settings().database.dsn)
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
