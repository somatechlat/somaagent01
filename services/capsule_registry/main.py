"""Capsule Registry Service
Provides a minimal REST API to upload, list and retrieve capsule artifacts.
Artifacts are stored on a shared volume (default ``/capsules``) and metadata
is persisted in the existing Postgres database (table ``capsules``).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.common.session_repository import PostgresSessionStore

app = FastAPI(title="Capsule Registry")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CAPSULE_STORAGE_PATH = Path(os.getenv("CAPSULE_STORAGE_PATH", "/capsules"))
CAPSULE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CapsuleMeta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    description: str | None = None
    filename: str  # stored filename on disk

# ---------------------------------------------------------------------------
# Simple DB helper – we reuse the existing PostgresSessionStore for a tiny table.
# In a real implementation you would create a proper SQLAlchemy model.
# ---------------------------------------------------------------------------
async def get_store() -> PostgresSessionStore:
    return PostgresSessionStore()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/capsules", response_model=CapsuleMeta)
async def upload_capsule(
    name: str = Field(..., description="Capsule name"),
    version: str = Field(..., description="Semantic version"),
    description: str | None = None,
    file: UploadFile = File(...),
    store: PostgresSessionStore = Depends(get_store),
):
    # Save file to storage directory
    capsule_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix
    stored_name = f"{capsule_id}{suffix}"
    dest_path = CAPSULE_STORAGE_PATH / stored_name
    with dest_path.open("wb") as out:
        content = await file.read()
        out.write(content)

    meta = CapsuleMeta(
        id=capsule_id,
        name=name,
        version=version,
        description=description,
        filename=stored_name,
    )

    # Persist minimal metadata (JSON) in Postgres – we store it in a generic key/value table.
    # For simplicity we just insert a row into a table ``capsules`` (create if missing).
    async with store.pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capsules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                filename TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
            """
        )
        await conn.execute(
            "INSERT INTO capsules (id, name, version, description, filename) VALUES ($1, $2, $3, $4, $5)",
            meta.id,
            meta.name,
            meta.version,
            meta.description,
            meta.filename,
        )
    return meta


@app.get("/capsules", response_model=List[CapsuleMeta])
async def list_capsules(store: PostgresSessionStore = Depends(get_store)):
    async with store.pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, version, description, filename FROM capsules")
    return [CapsuleMeta(**dict(row)) for row in rows]


@app.get("/capsules/{capsule_id}")
async def download_capsule(capsule_id: str, store: PostgresSessionStore = Depends(get_store)):
    async with store.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT filename FROM capsules WHERE id = $1", capsule_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Capsule not found")
    file_path = CAPSULE_STORAGE_PATH / row["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    return FileResponse(path=file_path, filename=file_path.name)