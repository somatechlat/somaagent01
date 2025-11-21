"""Attachment download endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.attachments_store import AttachmentsStore

router = APIRouter(prefix="/v1/attachments", tags=["attachments"])


def _store() -> AttachmentsStore:
    return AttachmentsStore(dsn=ADMIN_SETTINGS.postgres_dsn)


@router.get("/{attachment_id}")
async def download_attachment(attachment_id: str):
    store = _store()
    row = await store.get(attachment_id)
    if not row:
        raise HTTPException(status_code=404, detail="attachment_not_found")
    return Response(
        content=row.content,
        media_type=row.mime or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{row.filename}"',
            "X-Attachment-SHA256": row.sha256 or "",
        },
    )
