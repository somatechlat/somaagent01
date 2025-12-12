"""Attachment download endpoints extracted from gateway monolith."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from services.common.attachments_store import AttachmentsStore

# Legacy admin settings removed – use the central cfg singleton.
from src.core.config import cfg

router = APIRouter(prefix="/v1/attachments", tags=["attachments"])
internal_router = APIRouter(prefix="/internal/attachments", tags=["attachments-internal"])


def _store() -> AttachmentsStore:
    # Use the canonical configuration for the PostgreSQL DSN.
    return AttachmentsStore(dsn=cfg.settings().database.dsn)


@router.get("/{attachment_id}")
async def download_attachment(attachment_id: str):
    store = _store()
    att_uuid = uuid.UUID(str(attachment_id))
    meta = await store.get_metadata(att_uuid)
    content = await store.get_content(att_uuid)
    if not meta or content is None:
        raise HTTPException(status_code=404, detail="attachment_not_found")
    headers = {
        "Content-Disposition": f'attachment; filename="{meta.filename}"',
        "X-Attachment-SHA256": meta.sha256 or "",
        "Content-Type": meta.mime or "application/octet-stream",
    }
    return Response(content=content, media_type=None, headers=headers)


@internal_router.api_route("/{attachment_id}/binary", methods=["GET", "HEAD"])
async def download_internal_binary(
    attachment_id: str,
    internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    """Internal-only attachment download that requires an explicit token."""
    expected = cfg.env("SA01_AUTH_INTERNAL_TOKEN") or cfg.env("INTERNAL_API_TOKEN")
    if not internal_token or not expected or internal_token != expected:
        raise HTTPException(status_code=403, detail="forbidden")

    store = _store()
    att_uuid = uuid.UUID(str(attachment_id))
    meta = await store.get_metadata(att_uuid)
    content = await store.get_content(att_uuid)
    if not meta or content is None:
        raise HTTPException(status_code=404, detail="attachment_not_found")

    headers = {
        "Content-Disposition": f'attachment; filename="{meta.filename}"',
        "X-Attachment-SHA256": meta.sha256 or "",
        "X-Attachment-Size": str(meta.size),
        "X-Attachment-Status": meta.status or "",
        "Content-Type": meta.mime or "application/octet-stream",
    }
    return Response(content=content if internal_token else b"", media_type=None, headers=headers)
