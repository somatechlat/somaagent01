"""Tools listing endpoint extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.tool_executor.tool_registry import ToolRegistry  # type: ignore
from services.common.tool_catalog import ToolCatalogStore
from services.common.logging_config import get_logger

router = APIRouter(prefix="/v1", tags=["tools"])

LOGGER = get_logger(__name__)
CATALOG_STORE = ToolCatalogStore()


class ToolInfo(BaseModel):
    name: str
    description: str | None = None
    parameters: dict | None = None


class ToolsListResponse(BaseModel):
    tools: list[ToolInfo]
    count: int


@router.get("/tools", response_model=ToolsListResponse)
async def list_tools() -> ToolsListResponse:
    try:
        reg = ToolRegistry()
        await reg.load_all_tools()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to load tools: {exc}")

    tools: list[ToolInfo] = []
    try:
        await CATALOG_STORE.ensure_schema()
    except Exception:
        LOGGER.debug("Tool catalog check failed; defaulting to all tools enabled", exc_info=True)
    for t in reg.list():
        # Optional input schema extraction
        schema = None
        try:
            handler = getattr(t, "handler", None)
            if handler is not None and hasattr(handler, "input_schema"):
                schema = handler.input_schema()  # type: ignore[assignment]
        except Exception:
            schema = None
        allowed = True
        try:
            allowed = await CATALOG_STORE.is_enabled(t.name)
        except Exception:
            allowed = True
        if allowed:
            tools.append(
                ToolInfo(
                    name=t.name, description=getattr(t, "description", None), parameters=schema
                )
            )
    return ToolsListResponse(tools=tools, count=len(tools))
