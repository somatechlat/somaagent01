"""
Minimal mock SomaFractalMemory service for standalone development.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Mock SomaFractalMemory", version="1.0.0")


class StoreRequest(BaseModel):
    key: str
    value: Any


class RecallRequest(BaseModel):
    query: str
    limit: int = 10


@app.get("/api/health/")
def health():
    return {"status": "ok", "service": "somafractalmemory"}


@app.post("/api/v1/store")
def store(req: StoreRequest):
    return {
        "stored": True,
        "key": req.key,
        "message": "Value stored (mock)",
    }


@app.post("/api/v1/recall")
def recall(req: RecallRequest):
    return {
        "results": [
            {"id": "mem_001", "content": f"Mock memory for: {req.query}", "score": 0.99}
        ],
        "query": req.query,
        "limit": req.limit,
        "message": "Recall completed (mock)",
    }
