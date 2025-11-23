"""Uploads router skeleton."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])


@router.post("/")
async def upload(file: UploadFile = File(...)) -> dict[str, str]:
    # Consume the file to demonstrate functional behaviour.
    await file.read()
    return {"filename": file.filename, "status": "received"}
