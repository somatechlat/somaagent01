"""Migration admin API endpoints.

Migrated from: services/gateway/routers/admin_migrate.py
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel, Field

from admin.common.auth import RoleRequired

router = Router(tags=["admin-migrate"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class MigrateExportRequest(BaseModel):
    """Request payload for memory export."""

    include_wm: bool = Field(..., description="Include working memory in export")
    wm_limit: int = Field(..., ge=0, description="Maximum WM items to export")


class MigrateImportRequest(BaseModel):
    """Request payload for memory import."""

    manifest: dict[str, Any]
    memories: list[dict[str, Any]]
    wm: Optional[list[dict[str, Any]]] = None
    replace: bool = False


class MigrateExportResponse(BaseModel):
    """Export result."""

    manifest: dict[str, Any]
    memories: list[dict[str, Any]]
    wm: Optional[list[dict[str, Any]]] = None
    count: int


class MigrateImportResponse(BaseModel):
    """Import result."""

    status: str
    imported_count: int
    errors: list[str] = []


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/export",
    response=dict,
    summary="Export memory data for migration",
    auth=RoleRequired("admin", "saas_admin"),
)
async def admin_migrate_export(
    request: HttpRequest,
    payload: MigrateExportRequest,
) -> dict:
    """Export all memory data for migration to another instance.

    This exports:
    - Memory manifests
    - Long-term memories
    - Optionally working memory (with limit)
    """
    from admin.agents.services.somabrain_integration import SomaBrainClient

    client = SomaBrainClient.get()
    result = await client.migrate_export(
        include_wm=payload.include_wm,
        wm_limit=payload.wm_limit,
    )

    return result


@router.post(
    "/import",
    response=dict,
    summary="Import memory data from migration",
    auth=RoleRequired("admin", "saas_admin"),
)
async def admin_migrate_import(
    request: HttpRequest,
    payload: MigrateImportRequest,
) -> dict:
    """Import memory data from another instance.

    This imports:
    - Memory manifests
    - Long-term memories
    - Optionally working memory

    If replace=True, existing data is replaced.
    """
    from admin.agents.services.somabrain_integration import SomaBrainClient

    client = SomaBrainClient.get()
    result = await client.migrate_import(
        manifest=payload.manifest,
        memories=payload.memories,
        wm=payload.wm,
        replace=payload.replace,
    )

    return result