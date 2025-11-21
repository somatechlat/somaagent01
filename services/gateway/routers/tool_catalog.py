"""Tool catalog endpoints extracted from gateway monolith."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.tool_catalog import ToolCatalogStore, ToolCatalogEntry

router = APIRouter(prefix="/v1/tool-catalog", tags=["tools"])
CATALOG = ToolCatalogStore()


class ToolCatalogItem(BaseModel):
    name: str
    description: str | None = None
    tags: list[str] | None = None
    enabled: bool = True


@router.get("", response_model=list[ToolCatalogItem])
async def list_catalog() -> list[ToolCatalogItem]:
    await CATALOG.ensure_schema()
    items = await CATALOG.list()
    return [ToolCatalogItem(**entry.__dict__) for entry in items]


@router.put("/{name}")
async def upsert_catalog_item(name: str, item: ToolCatalogItem) -> ToolCatalogItem:
    await CATALOG.ensure_schema()
    entry = ToolCatalogEntry(
        name=name,
        description=item.description or "",
        tags=item.tags or [],
        enabled=item.enabled,
    )
    await CATALOG.upsert(entry)
    return ToolCatalogItem(**entry.__dict__)
