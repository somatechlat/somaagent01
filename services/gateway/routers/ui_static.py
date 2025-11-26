"""Serve the bundled Web UI assets from the `webui/` directory."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

WEBUI_ROOT = Path(__file__).resolve().parents[3] / "webui"


def _resolve_path(path: str) -> Path:
    # Prevent path traversal outside the webui directory
    candidate = (WEBUI_ROOT / path).resolve()
    if not str(candidate).startswith(str(WEBUI_ROOT)):
        raise HTTPException(status_code=404, detail="not_found")
    if candidate.is_file():
        return candidate
    index = WEBUI_ROOT / "index.html"
    if index.is_file():
        return index
    raise HTTPException(status_code=404, detail="not_found")


@router.get("/ui", include_in_schema=False)
async def ui_root():
    file_path = _resolve_path("index.html")
    return FileResponse(file_path)


@router.get("/ui/{path:path}", include_in_schema=False)
async def ui_static(path: str):
    path = path or "index.html"
    file_path = _resolve_path(path)
    return FileResponse(file_path)


__all__ = ["router"]
