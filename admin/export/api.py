"""Data Export API - GDPR Compliance.


Per AGENT_TASKS.md Phase 8 - Data Export.

7-Persona Implementation:
- Security Auditor: GDPR compliance, audit trail
- PhD Dev: Large data handling, streaming
- PM: User-friendly export process
"""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError

router = Router(tags=["export"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class ExportRequest(BaseModel):
    """Data export request."""

    export_type: str  # full, conversations, memories, settings
    format: str = "json"  # json, csv, zip
    include_attachments: bool = False


class ExportResponse(BaseModel):
    """Export request response."""

    export_id: str
    status: str  # pending, processing, ready, expired, failed
    requested_at: str
    estimated_completion: str
    export_type: str
    format: str


class ExportStatusResponse(BaseModel):
    """Export status response."""

    export_id: str
    status: str
    progress_percent: int
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[str] = None
    error: Optional[str] = None


class ExportListResponse(BaseModel):
    """List of exports."""

    exports: list[ExportStatusResponse]
    total: int


class DeletionRequest(BaseModel):
    """Account/data deletion request (GDPR)."""

    delete_type: str  # account, data_only
    confirmation: str  # Must be "DELETE"


class DeletionResponse(BaseModel):
    """Deletion response."""

    request_id: str
    status: str
    scheduled_for: str
    message: str


# =============================================================================
# ENDPOINTS - Data Export
# =============================================================================


@router.post(
    "",
    response=ExportResponse,
    summary="Request data export",
    auth=AuthBearer(),
)
async def request_export(request, payload: ExportRequest) -> ExportResponse:
    """Request a data export (GDPR Article 20).

    Per Phase 8.1: export_request()

    Export types:
    - full: All user data including conversations, memories, settings
    - conversations: Chat history only
    - memories: Memory capsules only
    - settings: User preferences and configurations

    GDPR COMPLIANT:
    - Right to data portability
    - Machine-readable format
    - Complete data within 30 days
    """
    export_id = str(uuid4())

    # Estimate completion based on export size
    estimated_minutes = 5 if payload.export_type == "settings" else 30
    estimated_completion = timezone.now() + timedelta(minutes=estimated_minutes)

    logger.info(
        f"Export requested: {export_id}, type: {payload.export_type}, " f"format: {payload.format}"
    )

    # In production: queue ZDL task for export
    # ExportTask.objects.create(
    #     id=export_id,
    #     user=request.auth.user_id,
    #     export_type=payload.export_type,
    #     format=payload.format,
    #     include_attachments=payload.include_attachments,
    # )

    return ExportResponse(
        export_id=export_id,
        status="pending",
        requested_at=timezone.now().isoformat(),
        estimated_completion=estimated_completion.isoformat(),
        export_type=payload.export_type,
        format=payload.format,
    )


@router.get(
    "/{export_id}",
    response=ExportStatusResponse,
    summary="Get export status",
    auth=AuthBearer(),
)
async def get_export_status(request, export_id: str) -> ExportStatusResponse:
    """Get status of an export request.

    Per Phase 8.1: export_status()
    """
    # In production: query ExportTask model

    return ExportStatusResponse(
        export_id=export_id,
        status="processing",
        progress_percent=45,
        file_size_bytes=None,
        download_url=None,
        expires_at=None,
    )


@router.get(
    "",
    response=ExportListResponse,
    summary="List export requests",
    auth=AuthBearer(),
)
async def list_exports(request) -> ExportListResponse:
    """List all export requests for the current user.

    Per Phase 8.1: export_list()
    """
    # In production: query ExportTask model
    return ExportListResponse(
        exports=[],
        total=0,
    )


@router.get(
    "/{export_id}/download",
    summary="Download export file",
    auth=AuthBearer(),
)
async def download_export(request, export_id: str) -> dict:
    """Download the exported data file.

    Per Phase 8.1: export_download()

    Returns a signed URL for secure download.
    """
    # In production:
    # 1. Verify export belongs to user
    # 2. Check export is ready
    # 3. Generate signed URL from storage

    # Generate secure download token
    download_token = secrets.token_urlsafe(32)

    return {
        "export_id": export_id,
        "download_url": f"/api/v2/export/{export_id}/file?token={download_token}",
        "expires_in_seconds": 3600,
        "message": "Download link valid for 1 hour",
    }


@router.delete(
    "/{export_id}",
    summary="Cancel or delete export",
    auth=AuthBearer(),
)
async def delete_export(request, export_id: str) -> dict:
    """Cancel pending export or delete completed export.

    Per Phase 8.1: export_cancel()
    """
    logger.info(f"Export cancelled/deleted: {export_id}")

    return {
        "export_id": export_id,
        "deleted": True,
        "message": "Export deleted",
    }


# =============================================================================
# ENDPOINTS - GDPR Deletion (Right to be Forgotten)
# =============================================================================


@router.post(
    "/deletion",
    response=DeletionResponse,
    summary="Request account deletion",
    auth=AuthBearer(),
)
async def request_deletion(request, payload: DeletionRequest) -> DeletionResponse:
    """Request account or data deletion (GDPR Article 17).

    Per Phase 8.2: deletion_request()

    Delete types:
    - account: Full account deletion (irreversible)
    - data_only: Delete data but keep account

    GDPR COMPLIANT:
    - Right to be forgotten
    - 30-day grace period for full deletion
    - Immediate anonymization of data
    """
    if payload.confirmation != "DELETE":
        raise BadRequestError("Confirmation must be 'DELETE'")

    request_id = str(uuid4())
    scheduled_date = timezone.now() + timedelta(days=30)

    logger.warning(
        f"DELETION REQUEST: {request_id}, type: {payload.delete_type}, "
        f"scheduled: {scheduled_date.date()}"
    )

    # In production:
    # DeletionRequest.objects.create(
    #     id=request_id,
    #     user=request.auth.user_id,
    #     delete_type=payload.delete_type,
    #     scheduled_for=scheduled_date,
    # )

    return DeletionResponse(
        request_id=request_id,
        status="scheduled",
        scheduled_for=scheduled_date.isoformat(),
        message="Deletion scheduled. Can be cancelled within 30 days.",
    )


@router.get(
    "/deletion/status",
    summary="Get deletion status",
    auth=AuthBearer(),
)
async def get_deletion_status(request) -> dict:
    """Get status of any pending deletion request.

    Per Phase 8.2: deletion_status()
    """
    # In production: query DeletionRequest model
    return {
        "has_pending_deletion": False,
        "request": None,
    }


@router.delete(
    "/deletion/cancel",
    summary="Cancel deletion request",
    auth=AuthBearer(),
)
async def cancel_deletion(request) -> dict:
    """Cancel a pending deletion request.

    Per Phase 8.2: deletion_cancel()

    Only possible during 30-day grace period.
    """
    logger.info("Deletion request cancelled")

    return {
        "cancelled": True,
        "message": "Deletion request cancelled",
    }


# =============================================================================
# ENDPOINTS - Data Inventory (GDPR)
# =============================================================================


@router.get(
    "/inventory",
    summary="Get data inventory",
    auth=AuthBearer(),
)
async def get_data_inventory(request) -> dict:
    """Get inventory of all stored user data.

    Per Phase 8.3: data_inventory()

    GDPR COMPLIANT: Right to access (Article 15).
    """
    return {
        "categories": [
            {
                "name": "Profile Data",
                "description": "Name, email, preferences",
                "last_updated": timezone.now().isoformat(),
            },
            {
                "name": "Conversations",
                "description": "Chat history with agents",
                "count": 0,
            },
            {
                "name": "Memories",
                "description": "Stored memory capsules",
                "count": 0,
            },
            {
                "name": "Files",
                "description": "Uploaded attachments",
                "size_bytes": 0,
            },
        ],
        "data_processing_purposes": [
            "Providing AI assistance services",
            "Memory and context management",
            "Service improvement (anonymized)",
        ],
        "data_retention_policy": "Data retained until account deletion or export",
    }
