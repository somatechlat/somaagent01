"""Workdir file operations extracted from gateway monolith (minimal functional set)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/v1/workdir", tags=["workdir"])

WORKDIR = Path(os.getenv("WORKDIR", "./tmp"))
WORKDIR.mkdir(parents=True, exist_ok=True)


@router.get("/list")
async def list_workdir() -> List[str]:
    return [p.name for p in WORKDIR.iterdir() if p.is_file()]


@router.post("/delete")
async def delete_file(name: str) -> dict:
    target = WORKDIR / name
    if not target.exists():
        raise HTTPException(status_code=404, detail="file_not_found")
    target.unlink()
    return {"deleted": name}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    target = WORKDIR / file.filename
    target.write_bytes(data)
    return {"stored": file.filename, "size": len(data)}


@router.get("/download")
async def download_file(name: str):
    target = WORKDIR / name
    if not target.exists():
        raise HTTPException(status_code=404, detail="file_not_found")
    return FileResponse(target)
