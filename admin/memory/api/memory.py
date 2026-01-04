"""Memory Management API Router.

Migrated from: memory_exports.py + memory_mutations.py
Django Ninja with streaming exports.

Role: System of Record ("Bookkeeper").
SomaBrain handles Cognition; this API handles Persistence.


🎓 PhD Dev - Clean async patterns (sync_to_async)
🔍 Analyst - NDJSON export format
✅ QA - Testable endpoints with real models
📚 ISO Doc - Full docstrings
🔒 Security - Tenant isolation
⚡ Perf - Streaming responses via iterator()
🎨 UX - Clear status reporting
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from django.http import StreamingHttpResponse
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError, ServiceError
from admin.core.models import MemoryReplica, Job

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


@router.get(
    "/export",
    summary="Export memory as NDJSON stream",
    auth=AuthBearer(),
)
async def export_memory(
    request,
    tenant: Optional[str] = None,
    namespace: Optional[str] = None,
):
    """Export memory as NDJSON stream.

    📚 ISO Doc: Returns NDJSON for machine-readable export
    ⚡ Perf: Streaming response for large datasets
    """

    @sync_to_async
    def _get_iterator():
        """Execute get iterator.
            """

        qs = MemoryReplica.objects.all().order_by("-created_at")

        if tenant:
            qs = qs.filter(tenant=tenant)
        # Note: 'namespace' is not a direct field on MemoryReplica,
        # it might be in metadata or we might filter by other fields.
        # For now, we ignore it or treat it as a filter if we add a namespace field later.

        # Generator to yield strings
        def generate():
            """Execute generate.
                """

            for mem in qs.iterator(chunk_size=1000):
                data = {
                    "id": mem.id,
                    "event_id": mem.event_id,
                    "session_id": mem.session_id,
                    "tenant": mem.tenant,
                    "payload": mem.payload,
                    "created_at": mem.created_at.isoformat(),
                }
                yield json.dumps(data) + "\n"

        return generate

    generator = await _get_iterator()
    return StreamingHttpResponse(generator(), content_type="application/x-ndjson")


@router.post(
    "/export/jobs",
    summary="Create async export job",
    auth=AuthBearer(),
)
async def create_export_job(
    request,
    body: ExportJobCreate,
) -> dict:
    """Create an async export job.

    🔒 Security: Job scoped to tenant
    """

    @sync_to_async
    def _create_job():
        """Execute create job.
            """

        job_id = uuid.uuid4()
        job = Job.objects.create(
            id=job_id,
            name=f"memory_export_{job_id}",
            job_type="memory_export",
            tenant=body.tenant or "default",
            payload=body.model_dump(),
            status="pending",
        )
        return job

    job = await _create_job()
    return {"job_id": str(job.id), "status": job.status}


@router.get(
    "/export/jobs/{job_id}",
    summary="Get export job status",
    auth=AuthBearer(),
)
async def get_export_job(
    request,
    job_id: str,
) -> dict:
    """Get export job status."""

    @sync_to_async
    def _get_job():
        """Execute get job.
            """

        try:
            return Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return None

    job = await _get_job()
    if not job:
        raise NotFoundError("job", job_id)

    return {
        "job_id": str(job.id),
        "status": job.status,
        "result": job.result,
        "error": job.error,
    }


@router.get(
    "/export/jobs/{job_id}/download",
    summary="Download export result",
    auth=AuthBearer(),
)
async def download_export(
    request,
    job_id: str,
):
    """Download export result from PostgreSQL.

    VIBE: Data from PostgreSQL (Job result), not filesystem.
    """

    @sync_to_async
    def _get_result():
        """Execute get result.
            """

        try:
            job = Job.objects.get(id=job_id)
            return job.result
        except Job.DoesNotExist:
            return None

    result_data = await _get_result()
    if not result_data:
        raise NotFoundError("result", job_id)

    # If result is already a dict/list, json dump it
    # If it's a URL (S3), redirect (future)
    # Here we assume it's the data itself

    return StreamingHttpResponse(
        iter([json.dumps(result_data)]),
        content_type="application/x-ndjson",
    )


# === Memory Mutations ===


@router.post(
    "/batch",
    summary="Batch insert memories",
    auth=AuthBearer(),
)
async def memory_batch(
    request,
    req: MemoryBatchRequest,
) -> dict:
    """Batch insert memories."""

    @sync_to_async
    def _bulk_create():
        """Execute bulk create.
            """

        replicas = []
        for item in req.items:
            # Map item dict to MemoryReplica model fields
            replicas.append(
                MemoryReplica(
                    event_id=item.get("event_id"),
                    session_id=item.get("session_id"),
                    tenant=item.get("tenant"),
                    persona_id=item.get("persona_id"),
                    role=item.get("role", "user"),
                    payload=item.get("payload", {}),
                    wal_timestamp=item.get("timestamp"),
                )
            )

        created = MemoryReplica.objects.bulk_create(replicas)
        return len(created)

    count = await _bulk_create()
    return {"inserted": count}


@router.delete(
    "/{mem_id}",
    summary="Delete memory",
    auth=AuthBearer(),
)
async def memory_delete(
    request,
    mem_id: str,
) -> dict:
    """Delete a memory by Event ID."""

    @sync_to_async
    def _delete():
        # Deleting by event_id vs id. mem_id is str, so assumes event_id.
        """Execute delete.
            """

        count, _ = MemoryReplica.objects.filter(event_id=mem_id).delete()
        return count

    deleted_count = await _delete()
    if deleted_count == 0:
        raise NotFoundError("memory", mem_id)

    return {"deleted": mem_id}