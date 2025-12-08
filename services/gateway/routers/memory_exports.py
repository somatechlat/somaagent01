"""Memory export/admin endpoints extracted from gateway monolith."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.common.export_job_store import (
    ensure_schema as ensure_export_jobs_schema,
    ExportJobStore,
)

# Legacy admin settings removed – use the central cfg singleton.
from src.core.config import cfg
from src.core.domain.memory.replica_store import MemoryReplicaStore

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
    return {"job_id": job.id, "status": job.status, "result_path": job.result_path}


@router.get("/export/jobs/{job_id}/download", summary="Download export result")
async def download_export(job_id: int):
    store = ExportJobStore(dsn=cfg.settings().database.dsn)
    job = await store.get_job(job_id)
    if not job or not job.result_path:
        raise HTTPException(status_code=404, detail="no_result")
    try:
        data = Path(job.result_path).read_bytes()
    except Exception:
        raise HTTPException(status_code=404, detail="missing_file")
    return StreamingResponse(iter([data]), media_type="application/x-ndjson")
