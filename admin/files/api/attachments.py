"""Files & Attachments API Router.

Migrated from: services/gateway/routers/attachments.py
Django Ninja.
"""

from __future__ import annotations

import logging
import uuid

from django.http import HttpRequest, HttpResponse
from ninja import Router

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError
from services.common.authorization import authorize

router = Router(tags=["attachments"])
logger = logging.getLogger(__name__)


def _get_store():
    """Execute get store."""

    from services.common.attachments_store import AttachmentsStore

    return AttachmentsStore()


@router.get("/{attachment_id}", summary="Download attachment", auth=AuthBearer())
async def download_attachment(request: HttpRequest, attachment_id: str):
    """Download an attachment by ID."""
    await authorize(request, action="resource:file_read", resource="files")

    store = _get_store()
    att_uuid = uuid.UUID(str(attachment_id))
    meta = await store.get_metadata(att_uuid)  # type: ignore[union-attr]
    content = await store.get_content(att_uuid)  # type: ignore[union-attr]

    if not meta or content is None:
        raise NotFoundError("attachment", attachment_id)

    response = HttpResponse(
        content=content,
        content_type=meta.mime or "application/octet-stream",
    )
    response["Content-Disposition"] = f'attachment; filename="{meta.filename}"'
    response["X-Attachment-SHA256"] = meta.sha256 or ""

    return response
