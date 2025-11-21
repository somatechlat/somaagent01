"""Minimal modular Gateway entrypoint.

All HTTP/WS routes are provided by the modular routers in services.gateway.routers.
Legacy monolith endpoints and large inline logic have been removed to comply with
VIBE rules (single source, no legacy duplicates).
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from services.gateway.routers import build_router

app = FastAPI(title="SomaAgent Gateway")
app.include_router(build_router())


def main() -> None:
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
