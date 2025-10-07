"""Serve the existing Agent Zero web UI with FastAPI.

This allows the legacy layout to run alongside the new SomaAgent 01 services
without relying on the old Flask stack.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 UI")

webui_path = Path(__file__).resolve().parent.parent.parent / "webui"
if not webui_path.exists():
    raise RuntimeError(f"webui directory not found at {webui_path}")

app.mount("/", StaticFiles(directory=str(webui_path), html=True), name="webui")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
