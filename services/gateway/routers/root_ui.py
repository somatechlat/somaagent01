"""Serve the Web UI from the root path (/) without a /ui prefix."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

WEBUI_ROOT = Path(__file__).resolve().parents[3] / "webui"
ALLOWED_DIRS = {"css", "js", "vendor", "public", "components", "assets"}


def _safe_path(path: Path) -> Path:
    path = path.resolve()
    if not str(path).startswith(str(WEBUI_ROOT)):
        raise HTTPException(status_code=404, detail="not_found")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="not_found")
    return path


@router.get("/", include_in_schema=False)
async def ui_root():
    return FileResponse(_safe_path(WEBUI_ROOT / "index.html"))


@router.get("/{filename}", include_in_schema=False)
async def ui_top_level(filename: str):
    # Avoid hijacking API routes
    if filename.startswith("v1"):
        raise HTTPException(status_code=404, detail="not_found")
    candidate = WEBUI_ROOT / filename
    return FileResponse(_safe_path(candidate))


@router.get("/{folder}/{path:path}", include_in_schema=False)
async def ui_assets(folder: str, path: str):
    candidate = WEBUI_ROOT / folder / path
    # Allow serving any file under webui (base path guard already applied in _safe_path)
    return FileResponse(_safe_path(candidate))


__all__ = ["router"]
