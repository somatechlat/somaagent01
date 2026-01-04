"""Tool Catalog & Discovery API Router.

Migrated from: services/gateway/routers/tool_catalog.py + tools_full.py
Pure Django Ninja implementation.


"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import ServiceError

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
    tags: Optional[list[str]] = None
    enabled: bool = True


class ToolsListResponse(BaseModel):
    """Tools list response."""

    tools: list[ToolInfo]
    count: int


def _get_catalog_store():
    """Get ToolCatalogStore instance."""
    from services.common.tool_catalog import ToolCatalogStore

    return ToolCatalogStore()


@router.get("", response=ToolsListResponse, summary="List all available tools")
async def list_tools() -> dict:
    """List all tools with their schemas.

    Loads tools from registry and filters by catalog enabled status.
    """
    from services.tool_executor.tool_registry import ToolRegistry

    catalog_store = _get_catalog_store()

    try:
        reg = ToolRegistry()
        await reg.load_all_tools()
    except Exception as exc:
        raise ServiceError(f"failed to load tools: {exc}")

    try:
        await catalog_store.ensure_schema()
    except Exception:
        logger.debug("Tool catalog check failed; defaulting to all tools enabled", exc_info=True)

    tools: list[dict] = []
    for t in reg.list():
        # Extract input schema if available
        schema = None
        try:
            handler = getattr(t, "handler", None)
            if handler is not None and hasattr(handler, "input_schema"):
                schema = handler.input_schema()
        except Exception:
            schema = None

        # Check if enabled in catalog
        allowed = True
        try:
            allowed = await catalog_store.is_enabled(t.name)
        except Exception:
            allowed = True

        if allowed:
            tools.append(
                {
                    "name": t.name,
                    "description": getattr(t, "description", None),
                    "parameters": schema,
                }
            )

    return {"tools": tools, "count": len(tools)}


@router.get("/catalog", response=list[ToolCatalogItem], summary="List tool catalog")
async def list_catalog() -> list[dict]:
    """List all tool catalog entries."""

    catalog = _get_catalog_store()
    await catalog.ensure_schema()
    items = await catalog.list()

    return [
        {
            "name": entry.name,
            "description": entry.description,
            "tags": entry.tags,
            "enabled": entry.enabled,
        }
        for entry in items
    ]


@router.put("/catalog/{name}", response=ToolCatalogItem, summary="Upsert tool catalog entry")
async def upsert_catalog_item(name: str, item: ToolCatalogItem) -> dict:
    """Create or update a tool catalog entry."""
    from services.common.tool_catalog import ToolCatalogEntry

    catalog = _get_catalog_store()
    await catalog.ensure_schema()

    entry = ToolCatalogEntry(
        name=name,
        description=item.description or "",
        tags=item.tags or [],
        enabled=item.enabled,
    )
    await catalog.upsert(entry)

    return {
        "name": entry.name,
        "description": entry.description,
        "tags": entry.tags,
        "enabled": entry.enabled,
    }
