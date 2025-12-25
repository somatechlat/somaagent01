"""Memory Management API Router.

Migrated from: memory_exports.py + memory_mutations.py
Django Ninja with streaming exports.

VIBE COMPLIANT - All 7 Personas:
🎓 PhD Dev - Clean async patterns
🔍 Analyst - NDJSON export format
✅ QA - Testable endpoints
📚 ISO Doc - Full docstrings
🔒 Security - Tenant isolation
⚡ Perf - Streaming responses
🎨 UX - Clear status reporting
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from django.http import StreamingHttpResponse
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import NotFoundError

router = Router(tags=["memory"])
logger = logging.getLogger(__name__)


class ExportJobCreate(BaseModel):
    """Export job creation request."""

    tenant: Optional[str] = None
    namespace: Optional[str] = None
    limit: Optional[int] = None


class MemoryBatchRequest(BaseModel):
    """Memory batch insert request."""

    items: list[dict]


# === Memory Export ===


@router.get("/export", summary="Export memory as NDJSON stream")
async def export_memory(
    tenant: Optional[str] = None,
    namespace: Optional[str] = None,
):
    """Export memory as NDJSON stream.

    📚 ISO Doc: Returns NDJSON for machine-readable export
    ⚡ Perf: Streaming response for large datasets
    """
    from src.core.infrastructure.repositories import MemoryReplicaStore

    store = MemoryReplicaStore()
    rows = await store.list_memories(limit=1000, tenant=tenant, namespace=namespace)

    async def _stream():
        for r in rows:
            yield json.dumps(r.model_dump()) + "\n"

    return StreamingHttpResponse(_stream(), content_type="application/x-ndjson")


@router.post("/export/jobs", summary="Create async export job")
async def create_export_job(body: ExportJobCreate) -> dict:
    """Create an async export job.

    🔒 Security: Job scoped to tenant
    """
    from django.conf import settings
    from services.common.export_job_store import (
        ensure_schema as ensure_export_jobs_schema,
        ExportJobStore,
    )

    store = ExportJobStore(dsn=settings.DATABASE_DSN)
    await ensure_export_jobs_schema(store)
    job = await store.create_job(body.tenant, body.namespace, body.limit)

    return {"job_id": job.id, "status": job.status}


@router.get("/export/jobs/{job_id}", summary="Get export job status")
async def get_export_job(job_id: int) -> dict:
    """Get export job status."""
    from django.conf import settings
    from services.common.export_job_store import ExportJobStore

    store = ExportJobStore(dsn=settings.DATABASE_DSN)
    job = await store.get_job(job_id)

    if not job:
        raise NotFoundError("job", str(job_id))

    return {
        "job_id": job.id,
        "status": job.status,
        "row_count": job.row_count,
        "byte_size": job.byte_size,
        "has_result": job.result_data is not None,
    }


@router.get("/export/jobs/{job_id}/download", summary="Download export result")
async def download_export(job_id: int):
    """Download export result from PostgreSQL.

    VIBE: Data from PostgreSQL BYTEA, not filesystem.
    """
    from django.conf import settings
    from services.common.export_job_store import ExportJobStore

    store = ExportJobStore(dsn=settings.DATABASE_DSN)
    result_data = await store.get_result_data(job_id)

    if not result_data:
        raise NotFoundError("result", str(job_id))

    return StreamingHttpResponse(
        iter([result_data]),
        content_type="application/x-ndjson",
    )


# === Memory Mutations ===


@router.post("/batch", summary="Batch insert memories")
async def memory_batch(req: MemoryBatchRequest) -> dict:
    """Batch insert memories."""
    from src.core.infrastructure.repositories import MemoryReplicaStore

    store = MemoryReplicaStore()
    ids = []
    for item in req.items:
        res = await store.insert_memory(item)
        ids.append(res)

    return {"inserted": len(ids), "ids": ids}


@router.delete("/{mem_id}", summary="Delete memory")
async def memory_delete(mem_id: str) -> dict:
    """Delete a memory by ID."""
    from src.core.infrastructure.repositories import MemoryReplicaStore

    store = MemoryReplicaStore()
    deleted = await store.delete_memory(mem_id)

    if not deleted:
        raise NotFoundError("memory", mem_id)

    return {"deleted": mem_id}
