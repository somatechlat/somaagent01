"""Tool Catalog & Discovery API Router.

Canonical source: admin.core.models.Capability (replaces ToolCatalogStore).
Pure Django Ninja implementation.
"""

from __future__ import annotations

import logging
from typing import Optional

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.core.models.core import Capability
from services.common.authorization import authorize

router = Router(tags=["tools"])
logger = logging.getLogger(__name__)


class ToolInfo(BaseModel):
    """Tool information schema."""

    name: str
    description: Optional[str] = None
    parameters: Optional[dict] = None


class ToolCatalogItem(BaseModel):
    """Tool catalog entry schema."""

    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    enabled: bool = True


class ToolsListResponse(BaseModel):
    """Tools list response."""

    tools: list[ToolInfo]
    count: int


@router.get("", response=ToolsListResponse, summary="List all available tools", auth=AuthBearer())
async def list_tools(request: HttpRequest) -> dict:
    """List all enabled tools with their schemas.

    Queries the canonical Capability model.
    """
    await authorize(request, action="resource:tool_read", resource="tools")
    capabilities = await sync_to_async(list)(
        Capability.objects.filter(is_enabled=True).values("name", "description", "schema")
    )

    tools: list[dict] = []
    for c in capabilities:
        schema = c.get("schema") or {}
        tools.append(
            {
                "name": c["name"],
                "description": c["description"],
                "parameters": schema,
            }
        )

    return {"tools": tools, "count": len(tools)}


@router.get("/catalog", response=list[ToolCatalogItem], summary="List tool catalog", auth=AuthBearer())
async def list_catalog(request: HttpRequest) -> list[dict]:
    """List all tool catalog entries."""
    await authorize(request, action="resource:tool_read", resource="tools")
    items = await sync_to_async(list)(
        Capability.objects.all().values("name", "description", "category", "is_enabled")
    )

    return [
        {
            "name": item["name"],
            "description": item["description"],
            "category": item["category"],
            "enabled": item["is_enabled"],
        }
        for item in items
    ]


@router.put("/catalog/{name}", response=ToolCatalogItem, summary="Upsert tool catalog entry", auth=AuthBearer())
async def upsert_catalog_item(request: HttpRequest, name: str, item: ToolCatalogItem) -> dict:
    """Create or update a tool catalog entry."""
    await authorize(request, action="resource:tool_configure", resource="tools")
    capability, _created = await sync_to_async(Capability.objects.update_or_create)(
        name=name,
        defaults={
            "description": item.description or "",
            "category": item.category or "general",
            "is_enabled": item.enabled,
        },
    )

    return {
        "name": capability.name,
        "description": capability.description,
        "category": capability.category,
        "enabled": capability.is_enabled,
    }
