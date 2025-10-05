"""Canvas service scaffold for SomaAgent 01."""
from __future__ import annotations

import logging
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.common.session_repository import PostgresSessionStore

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Canvas Service")


def get_store() -> PostgresSessionStore:
    return PostgresSessionStore()


class CanvasEvent(BaseModel):
    session_id: str
    persona_id: str | None = None
    pane: str
    content: str
    metadata: dict[str, str] | None = None


@app.post("/v1/canvas/event")
async def append_canvas_event(
    payload: CanvasEvent,
    store: Annotated[PostgresSessionStore, Depends(get_store)],
) -> dict[str, str]:
    await store.append_event(
        payload.session_id,
        {
            "type": "canvas",
            "pane": payload.pane,
            "content": payload.content,
            "persona_id": payload.persona_id,
            "metadata": payload.metadata or {},
        },
    )
    return {"status": "stored"}


@app.get("/v1/canvas/{session_id}")
async def list_canvas_events(
    session_id: str,
    store: Annotated[PostgresSessionStore, Depends(get_store)],
) -> list[dict]:
    events = await store.list_events(session_id, limit=100)
    return [event for event in events if event.get("type") == "canvas"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8014")))
