"""Files & Attachments API Router.

Migrated from: services/gateway/routers/attachments.py
Django Ninja.
"""

from __future__ import annotations

import uuid
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from ninja import Router

from admin.common.exceptions import NotFoundError, ForbiddenError

router = Router(tags=["attachments"])
logger = logging.getLogger(__name__)


def _get_store():
    from services.common.attachments_store import AttachmentsStore
    from django.conf import settings

    return AttachmentsStore(dsn=settings.DATABASE_DSN)


@router.get("/{attachment_id}", summary="Download attachment")
async def download_attachment(request: HttpRequest, attachment_id: str):
    """Download an attachment by ID."""
    store = _get_store()
    att_uuid = uuid.UUID(str(attachment_id))
    meta = await store.get_metadata(att_uuid)
    content = await store.get_content(att_uuid)

    if not meta or content is None:
        raise NotFoundError("attachment", attachment_id)

    response = HttpResponse(
        content=content,
        content_type=meta.mime or "application/octet-stream",
    )
    response["Content-Disposition"] = f'attachment; filename="{meta.filename}"'
    response["X-Attachment-SHA256"] = meta.sha256 or ""

    return response
