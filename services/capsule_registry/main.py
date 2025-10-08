"""Capsule Registry Service
Provides a minimal REST API to upload, list and retrieve capsule artifacts.
Artifacts are stored on a shared volume (default ``/capsules``) and metadata
is persisted in the existing Postgres database (table ``capsules``).
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import List
import subprocess

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from datetime import datetime

from services.common.session_repository import PostgresSessionStore
from python.somaagent.capsule import install_capsule

app = FastAPI(title="Capsule Registry")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CAPSULE_STORAGE_PATH = Path(os.getenv("CAPSULE_STORAGE_PATH", "/capsules"))
CAPSULE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

CAPSULE_INSTALL_BASE = Path(
    os.getenv("CAPSULE_INSTALL_PATH", str(CAPSULE_STORAGE_PATH / "installed"))
)
CAPSULE_INSTALL_BASE.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CapsuleMeta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    description: str | None = None
    filename: str  # stored filename on disk
    signature: str | None = None
    created_at: datetime | None = None

# ---------------------------------------------------------------------------
# Simple DB helper – we reuse the existing PostgresSessionStore for a tiny table.
# In a real implementation you would create a proper SQLAlchemy model.
# ---------------------------------------------------------------------------
async def get_store() -> PostgresSessionStore:
    return PostgresSessionStore()

def _sign_blob(file_path: str) -> str:
    """Sign the given file with cosign and return the base64 signature.

    The function expects the environment variable ``COSIGN_KEY_PATH`` to point to a
    cosign private key. If signing fails, an empty string is returned.
    """
    key_path = os.getenv("COSIGN_KEY_PATH")
    if not key_path:
        return ""
    try:
        result = subprocess.run(
            ["cosign", "sign-blob", "--key", key_path, file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        # cosign prints the signature to stdout
        return result.stdout.strip()
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/capsules", response_model=CapsuleMeta)
async def upload_capsule(
    name: str = Form(..., description="Capsule name"),
    version: str = Form(..., description="Semantic version"),
    description: str | None = Form(None, description="Optional description"),
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

    # Sign the stored artifact using cosign (optional)
    signature = _sign_blob(str(dest_path))

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
                signature TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
            """
        )
        await conn.execute(
            "INSERT INTO capsules (id, name, version, description, filename, signature) VALUES ($1, $2, $3, $4, $5, $6)",
            capsule_id,
            name,
            version,
            description,
            stored_name,
            signature,
        )
        row = await conn.fetchrow(
            "SELECT id, name, version, description, filename, signature, created_at FROM capsules WHERE id = $1",
            capsule_id,
        )

    if not row:
        raise HTTPException(status_code=500, detail="Failed to persist capsule metadata")

    return CapsuleMeta(**dict(row))


@app.get("/capsules", response_model=List[CapsuleMeta])
async def list_capsules(store: PostgresSessionStore = Depends(get_store)):
    async with store.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, version, description, filename, signature, created_at FROM capsules ORDER BY created_at DESC"
        )
    return [CapsuleMeta(**dict(row)) for row in rows]


@app.post("/capsules/{capsule_id}/install")
async def install_capsule_via_sdk(
    capsule_id: str,
    store: PostgresSessionStore = Depends(get_store),
):
    async with store.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT signature FROM capsules WHERE id = $1",
            capsule_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail="Capsule not found")

    install_dir = CAPSULE_INSTALL_BASE / capsule_id
    install_dir.mkdir(parents=True, exist_ok=True)

    try:
        extracted = await asyncio.to_thread(
            install_capsule,
            capsule_id,
            str(install_dir),
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "capsule_id": capsule_id,
        "install_path": str(extracted),
        "signature": row.get("signature"),
    }


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