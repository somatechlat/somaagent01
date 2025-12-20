"""Production-grade Upload Manager with TUS + ClamAV + SHA-256 integrity."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Annotated, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis.asyncio as redis

from services.common.attachments_store import AttachmentsStore
from services.common.authorization import authorize_request
from services.common.clamav_scanner import ClamAVScanner, ScanStatus
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import get_logger
from services.common.publisher import DurablePublisher
from services.gateway.limiter import limiter
from src.core.config import cfg

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])

LOGGER = get_logger(__name__)


class AttachmentRecord(BaseModel):
    id: str
    filename: str
    mime_type: str
    size: int
    sha256: str
    status: str  # clean | quarantined
    quarantine_reason: Optional[str]
    created_at: float
    tenant_id: Optional[str]
    session_id: Optional[str]
    download_url: str


@dataclass
class UploadSession:
    id: str
    filename: str
    size: int
    mime_type: str
    tenant_id: Optional[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    offset: int = 0
    buffer: bytearray = field(default_factory=bytearray)


class TUSUploadHandler:
    """TUS protocol handler with SHA-256 + ClamAV scanning.

    Backed by Redis for resumable sessions; falls back to in-memory if Redis
    is unavailable at runtime.
    """

    def __init__(
        self,
        store: AttachmentsStore,
        scanner: ClamAVScanner,
        *,
        max_size: int,
        quarantine_on_error: bool,
        clamav_enabled: bool,
        stream_max_bytes: int,
        session_ttl: int = 24 * 3600,
    ) -> None:
        self._store = store
        self._scanner = scanner
        # Enforce clamd stream size; overall max is the minimum of upload limit and clamd limit.
        self._max_size = min(max_size, stream_max_bytes)
        self._quarantine_on_error = quarantine_on_error
        self._clamav_enabled = clamav_enabled
        self._session_ttl = session_ttl
        self._uploads: Dict[str, UploadSession] = {}
        self._redis = None
        try:
            redis_url = cfg.settings().redis.url
            self._redis = redis.from_url(redis_url, decode_responses=False)
        except Exception:
            self._redis = None

    async def create_upload(
        self,
        *,
        filename: str,
        size: int,
        mime_type: str,
        tenant_id: Optional[str],
        session_id: Optional[str],
        persona_id: Optional[str],
    ) -> UploadSession:
        if size <= 0 or size > self._max_size:
            raise ValueError(f"upload size exceeds limit ({self._max_size} bytes)")
        upload_id = str(uuid.uuid4())
        sess = UploadSession(
            id=upload_id,
            filename=filename,
            size=size,
            mime_type=mime_type,
            tenant_id=tenant_id,
            session_id=session_id,
            persona_id=persona_id,
        )
        if self._redis:
            await self._redis.hset(
                f"tus:upload:{upload_id}:meta",
                mapping={
                    "filename": filename,
                    "size": str(size),
                    "mime": mime_type,
                    "tenant": tenant_id or "",
                    "session": session_id or "",
                    "persona": persona_id or "",
                    "offset": "0",
                },
            )
            await self._redis.expire(f"tus:upload:{upload_id}:meta", self._session_ttl)
            await self._redis.delete(f"tus:upload:{upload_id}:content")
        else:
            self._uploads[upload_id] = sess
        return sess

    async def append_chunk(
        self,
        upload_id: str,
        chunk: bytes,
        *,
        offset: int,
        checksum: Optional[str] = None,
    ) -> int:
        if self._redis:
            meta_key = f"tus:upload:{upload_id}:meta"
            content_key = f"tus:upload:{upload_id}:content"
            async with self._redis.pipeline(transaction=True) as pipe:
                while True:
                    try:
                        await pipe.watch(meta_key)
                        meta = await pipe.hgetall(meta_key)
                        if not meta:
                            raise ValueError("upload_not_found")
                        current_offset = int(meta.get(b"offset", b"0"))
                        size = int(meta.get(b"size", b"0"))
                        if offset != current_offset:
                            raise ValueError("offset_mismatch")
                        new_offset = offset + len(chunk)
                        if new_offset > size:
                            raise ValueError("chunk_exceeds_declared_size")
                        if checksum:
                            digest = hashlib.sha256(chunk).hexdigest()
                            if digest != checksum:
                                raise ValueError("checksum_mismatch")
                        pipe.multi()
                        pipe.append(content_key, chunk)
                        pipe.hset(meta_key, "offset", str(new_offset))
                        pipe.expire(meta_key, self._session_ttl)
                        pipe.expire(content_key, self._session_ttl)
                        await pipe.execute()
                        return new_offset
                    except redis.WatchError:
                        continue
        sess = self._uploads.get(upload_id)
        if not sess:
            raise ValueError("upload_not_found")
        if offset != sess.offset:
            raise ValueError("offset_mismatch")
        new_offset = offset + len(chunk)
        if new_offset > sess.size or new_offset > self._max_size:
            raise ValueError("chunk_exceeds_declared_size")
        if checksum:
            digest = hashlib.sha256(chunk).hexdigest()
            if digest != checksum:
                raise ValueError("checksum_mismatch")
        sess.buffer.extend(chunk)
        sess.offset = new_offset
        return new_offset

    async def finalize_upload(self, upload_id: str) -> AttachmentRecord:
        content: bytes
        sess: UploadSession
        if self._redis:
            meta_key = f"tus:upload:{upload_id}:meta"
            content_key = f"tus:upload:{upload_id}:content"
            meta = await self._redis.hgetall(meta_key)
            if not meta:
                raise ValueError("upload_not_found")
            size = int(meta.get(b"size", b"0"))
            offset = int(meta.get(b"offset", b"0"))
            if offset != size:
                raise ValueError("upload_incomplete")
            if size > self._max_size:
                raise ValueError("upload_exceeds_stream_limit")
            raw = await self._redis.get(content_key)
            content = raw or b""
            sess = UploadSession(
                id=upload_id,
                filename=meta.get(b"filename", b"").decode() or f"upload-{upload_id}",
                size=size,
                mime_type=meta.get(b"mime", b"").decode() or "application/octet-stream",
                tenant_id=(meta.get(b"tenant") or b"").decode() or None,
                session_id=(meta.get(b"session") or b"").decode() or None,
                persona_id=(meta.get(b"persona") or b"").decode() or None,
                offset=offset,
            )
            await self._redis.delete(meta_key, content_key)
        else:
            sess = self._uploads.get(upload_id)
            if not sess:
                raise ValueError("upload_not_found")
            if sess.offset != sess.size:
                raise ValueError("upload_incomplete")
            if sess.size > self._max_size:
                raise ValueError("upload_exceeds_stream_limit")
            content = bytes(sess.buffer)

        sha256_hex = hashlib.sha256(content).hexdigest()

        scan_result = self._scanner.scan_bytes(content) if self._clamav_enabled else None

        status = "clean"
        reason = None

        if scan_result:
            if scan_result.status == ScanStatus.QUARANTINED:
                status = "quarantined"
                reason = scan_result.threat_name
            elif scan_result.status == ScanStatus.ERROR:
                if self._quarantine_on_error:
                    status = "quarantined"
                    reason = scan_result.error_message or "scan_error"
                else:
                    raise RuntimeError(scan_result.error_message or "clamav_unavailable")
            elif scan_result.status == ScanStatus.SCAN_PENDING:
                # Quarantine with pending status until scan completes
                status = "quarantined"
                reason = "antivirus_scan_in_progress"

        att_id = await self._store.create(
            tenant=sess.tenant_id,
            session_id=sess.session_id,
            persona_id=sess.persona_id,
            filename=sess.filename,
            mime=sess.mime_type,
            size=sess.size,
            sha256=sha256_hex,
            status="quarantined" if status == "quarantined" else "clean",
            quarantine_reason=reason,
            content=content,
        )
        record = AttachmentRecord(
            id=str(att_id),
            filename=sess.filename,
            mime_type=sess.mime_type,
            size=sess.size,
            sha256=sha256_hex,
            status="quarantined" if status == "quarantined" else "clean",
            quarantine_reason=reason,
            created_at=time.time(),
            tenant_id=sess.tenant_id,
            session_id=sess.session_id,
            download_url=f"/v1/attachments/{att_id}",
        )
        self._uploads.pop(upload_id, None)
        return record

    async def get_offset(self, upload_id: str) -> Optional[int]:
        if self._redis:
            meta = await self._redis.hgetall(f"tus:upload:{upload_id}:meta")
            if not meta:
                return None
            return int(meta.get(b"offset", b"0"))
        sess = self._uploads.get(upload_id)
        return sess.offset if sess else None

    async def delete_upload(self, upload_id: str) -> None:
        if self._redis:
            await self._redis.delete(
                f"tus:upload:{upload_id}:meta",
                f"tus:upload:{upload_id}:content",
            )
        else:
            self._uploads.pop(upload_id, None)
    async def health(self) -> dict:
        """Return health snapshot including clamd reachability."""
        error = None
        scan_ok = self._scanner.ping() if self._clamav_enabled else True
        if not scan_ok and self._clamav_enabled:
            error = "ClamAV Unreachable"

        return {
            "status": "ok" if scan_ok else "degraded",
            "clamav": "ok" if scan_ok else "error",
            "clamav_error": error,
            "max_upload_bytes": self._max_size,
            "session_backend": "redis" if self._redis else "memory",
        }


def _attachments_store() -> AttachmentsStore:
    return AttachmentsStore(dsn=cfg.settings().database.dsn)


def _publisher() -> Optional[DurablePublisher]:
    """Create a durable publisher for upload events."""
    try:
        bus = KafkaEventBus(KafkaSettings.from_env())
        return DurablePublisher(bus=bus)
    except Exception:
        return None


_tus_handler_singleton: Optional[TUSUploadHandler] = None


def _tus_handler(store: AttachmentsStore = Depends(_attachments_store)) -> TUSUploadHandler:
    global _tus_handler_singleton
    if _tus_handler_singleton is None:
        max_size = int(cfg.env("SA01_UPLOAD_MAX_SIZE", str(100 * 1024 * 1024)))
        stream_max = int(cfg.env("SA01_CLAMAV_STREAM_MAX_BYTES", str(100 * 1024 * 1024)))
        quarantine_on_error = cfg.env("SA01_UPLOAD_QUARANTINE_ON_ERROR", "true").lower() == "true"
        clamav_enabled = cfg.env("SA01_CLAMAV_ENABLED", "true").lower() == "true"
        scanner = ClamAVScanner(
            socket_path=cfg.env("SA01_CLAMAV_SOCKET", "/var/run/clamav/clamd.sock"),
            host=cfg.env("SA01_CLAMAV_HOST"),
            port=int(cfg.env("SA01_CLAMAV_PORT", "3310"))
        )
        _tus_handler_singleton = TUSUploadHandler(
            store,
            scanner=scanner,
            max_size=max_size,
            quarantine_on_error=quarantine_on_error,
            clamav_enabled=clamav_enabled,
            stream_max_bytes=stream_max,
        )
    return _tus_handler_singleton


@router.post("")
@limiter.limit("10/minute")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    publisher: Annotated[Optional[DurablePublisher], Depends(_publisher)] = None,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)] = None,
) -> JSONResponse:
    """Multipart fast-path that still enforces hash + AV scan."""
    auth_meta = await authorize_request(request, {})
    tenant = auth_meta.get("tenant")
    sess = auth_meta.get("session_id")
    persona = auth_meta.get("persona_id")

    results: List[dict] = []
    for idx, file in enumerate(files):
        raw = await file.read()
        size = len(raw)
        mime = file.content_type or "application/octet-stream"
        filename = file.filename or f"upload-{idx}"
        tus_session = await handler.create_upload(
            filename=filename,
            size=size,
            mime_type=mime,
            tenant_id=tenant,
            session_id=sess,
            persona_id=persona,
        )
        await handler.append_chunk(tus_session.id, raw, offset=0)
        record = await handler.finalize_upload(tus_session.id)
        results.append(record.model_dump())

        if publisher:
            try:
                await publisher.publish(
                    cfg.env("SA01_UPLOAD_TOPIC", "file.uploaded"),
                    {
                        "type": "file.uploaded",
                        "id": record.id,
                        "filename": record.filename,
                        "mime": record.mime_type,
                        "size": record.size,
                        "sha256": record.sha256,
                        "status": record.status,
                        "tenant": tenant,
                        "session_id": sess,
                    },
                    tenant=tenant,
                    session_id=sess,
                )
            except Exception:
                LOGGER.warning("Failed to publish upload event", exc_info=True)
    return JSONResponse(results)


class UploadInitRequest(BaseModel):
    filename: str
    size: int
    mime_type: Optional[str] = "application/octet-stream"


@router.post("/tus")
@limiter.limit("20/minute")
async def tus_create(
    payload: UploadInitRequest,
    request: Request,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)],
) -> JSONResponse:
    auth_meta = await authorize_request(request, {})
    sess = await handler.create_upload(
        filename=payload.filename,
        size=payload.size,
        mime_type=payload.mime_type or "application/octet-stream",
        tenant_id=auth_meta.get("tenant"),
        session_id=auth_meta.get("session_id"),
        persona_id=auth_meta.get("persona_id"),
    )
    upload_url = f"/v1/uploads/tus/{sess.id}"
    return JSONResponse({"upload_id": sess.id, "upload_url": upload_url, "offset": 0})


@router.patch("/tus/{upload_id}")
@limiter.limit("100/minute")
async def tus_patch(
    upload_id: str,
    request: Request,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)],
    upload_offset: Annotated[int, Header(..., alias="Upload-Offset")],
    upload_checksum: Annotated[Optional[str], Header(alias="Upload-Checksum")] = None,
):
    chunk = await request.body()
    try:
        new_offset = await handler.append_chunk(
            upload_id, chunk, offset=int(upload_offset), checksum=upload_checksum
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return JSONResponse({"upload_id": upload_id, "offset": new_offset})


@router.head("/tus/{upload_id}")
async def tus_head(
    upload_id: str,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)],
):
    offset = await handler.get_offset(upload_id)
    if offset is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return Response(
        status_code=200,
        headers={
            "Upload-Offset": str(offset),
            "Tus-Resumable": "1.0.0",
            "Cache-Control": "no-store",
        }
    )


@router.delete("/tus/{upload_id}")
async def tus_delete(
    upload_id: str,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)],
):
    await handler.delete_upload(upload_id)
    return Response(status_code=204, headers={"Tus-Resumable": "1.0.0"})


@router.post("/tus/{upload_id}/finalize")
@limiter.limit("20/minute")
async def tus_finalize(
    upload_id: str,
    handler: Annotated[TUSUploadHandler, Depends(_tus_handler)],
):
    try:
        record = await handler.finalize_upload(upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(record.model_dump())


@router.get("/health")
async def uploads_health(handler: Annotated[TUSUploadHandler, Depends(_tus_handler)]):
    """Report upload subsystem health, including clamd reachability."""
    return JSONResponse(await handler.health())
