"""Memory export/admin endpoints - VIBE COMPLIANT.

All export data stored in PostgreSQL BYTEA, not filesystem.
No Path operations for result storage.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.common.export_job_store import (
    ensure_schema as ensure_export_jobs_schema,
    ExportJobStore,
)
from src.core.config import cfg
from src.core.infrastructure.repositories import MemoryReplicaStore

router = APIRouter(prefix="/v1/memory", tags=["memory"])


class ExportJobCreate(BaseModel):
    tenant: str | None = None
    namespace: str | None = None
    limit: int | None = None


@router.get("/export", summary="Export memory as NDJSON stream")
async def export_memory(tenant: str | None = None, namespace: str | None = None):
    store = MemoryReplicaStore()
    rows = await store.list_memories(limit=1000, tenant=tenant, namespace=namespace)

    async def _stream():
        import json

        for r in rows:
            yield json.dumps(r.model_dump()) + "\n"

    return StreamingResponse(_stream(), media_type="application/x-ndjson")


@router.post("/export/jobs", summary="Create async export job")
async def create_export_job(body: ExportJobCreate):
    store = ExportJobStore(dsn=cfg.settings().database.dsn)
    await ensure_export_jobs_schema(store)
    job = await store.create_job(body.tenant, body.namespace, body.limit)
    return {"job_id": job.id, "status": job.status}


@router.get("/export/jobs/{job_id}", response_model=dict, summary="Get export job status")
async def get_export_job(job_id: int):
    store = ExportJobStore(dsn=cfg.settings().database.dsn)
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
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

    VIBE: Data retrieved directly from PostgreSQL BYTEA, not filesystem.
    """
    store = ExportJobStore(dsn=cfg.settings().database.dsn)
    result_data = await store.get_result_data(job_id)
    if not result_data:
        raise HTTPException(status_code=404, detail="no_result")
    return StreamingResponse(iter([result_data]), media_type="application/x-ndjson")
