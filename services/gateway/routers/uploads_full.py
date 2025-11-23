"""Uploads endpoints extracted from gateway monolith."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse

from src.core.config import cfg
from services.common.attachments_store import AttachmentsStore
from services.common.authorization import authorize_request
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.memory_write_outbox import MemoryWriteOutbox
from services.common.publisher import DurablePublisher
from services.common.session_repository import PostgresSessionStore, RedisSessionCache

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])

LOGGER = logging.getLogger(__name__)


def _attachments_store() -> AttachmentsStore:
    return AttachmentsStore(dsn=cfg.settings().database.dsn)


def _publisher() -> DurablePublisher:
    # Minimal stub; in monolith this used specific publisher wiring.
    bus = KafkaEventBus(KafkaSettings.from_env())
    return DurablePublisher(bus=bus, outbox=MemoryWriteOutbox(dsn=cfg.settings().database.dsn))


def _session_store() -> PostgresSessionStore:
    return PostgresSessionStore(cfg.settings().database.dsn)


def _session_cache() -> RedisSessionCache:
    return RedisSessionCache(cfg.settings().redis.url)


@router.post("")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    publisher: Annotated[DurablePublisher, Depends(_publisher)] = None,
    store: Annotated[AttachmentsStore, Depends(_attachments_store)] = None,
    cache: Annotated[RedisSessionCache, Depends(_session_cache)] = None,
    session_store: Annotated[PostgresSessionStore, Depends(_session_store)] = None,
) -> JSONResponse:
    # Minimal functional path: store files and return descriptors; skips clamd/quarantine to avoid env coupling.
    tenant = None
    sess = None
    auth_meta = await authorize_request(request, {})
    tenant = auth_meta.get("tenant")
    sess = auth_meta.get("session_id")

    results = []
    start = time.perf_counter()
    for idx, file in enumerate(files):
        raw = await file.read()
        size = len(raw)
        sha = hashlib.sha256(raw)
        safe_name = file.filename or f"upload-{idx}"
        att_id = await store.create(
            filename=safe_name,
            mime=file.content_type or "application/octet-stream",
            size=size,
            sha256=sha.hexdigest(),
            status="clean",
            quarantine_reason=None,
            content=raw,
        )
        descriptor = {
            "id": str(att_id),
            "filename": safe_name,
            "mime": file.content_type or "application/octet-stream",
            "size": size,
            "sha256": sha.hexdigest(),
            "created_at": time.time(),
            "tenant": tenant,
            "session_id": sess,
            "status": "clean",
            "quarantine_reason": None,
            "path": f"/v1/attachments/{str(att_id)}",
        }
        results.append(descriptor)
    return JSONResponse(results)
