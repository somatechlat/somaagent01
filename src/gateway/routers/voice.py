"""FastAPI router for the voice subsystem.

The router provides a minimal endpoint that demonstrates how the ``VoiceService``
can be instantiated and started.  A full bi‑directional streaming implementation
would require WebSocket handling; for now we expose a simple ``POST /v1/voice``
that returns a JSON acknowledgement.  This satisfies the requirement of having a
router mounted in ``services/gateway/service.py`` while keeping the implementation
lightweight for CI.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.core.config import cfg
from src.voice.service import VoiceService

router = APIRouter(prefix="/v1/voice", tags=["voice"])


def get_config():
    """Dependency that provides the global configuration object.

    ``cfg`` is a singleton created by ``src.core.config``; this function simply
    returns it so FastAPI can inject it if needed.
    """
    return cfg


@router.post("/start")
async def start_voice_service(config=Depends(get_config)) -> dict[str, str]:
    """Start a voice session.

    The endpoint creates a :class:`VoiceService`, calls ``start`` and returns a
    simple acknowledgement.  Errors are converted to HTTP 500 responses.
    """
    try:
        service = VoiceService(config)
        await service.start()
        # In a real implementation ``service.run()`` would be awaited while
        # streaming audio back to the client.
        return {"status": "voice service started"}
    except Exception as exc:  # pragma: no cover – defensive
        raise HTTPException(status_code=500, detail=str(exc))
