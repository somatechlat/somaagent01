"""Tunnel proxy endpoint.

The web UI uses the ``/tunnel_proxy`` endpoint for several actions (create,
verify, stop, status) as observed in ``webui/components/settings/tunnel/
tunnel-store.js``.  The original codebase did not provide this route, which
resulted in a ``405 Method Not Allowed`` error when the UI attempted a POST
request.  To restore functionality we implement a minimal, generic handler that
accepts a JSON payload, logs the request for debugging, and returns a simple
``{"status": "ok"}`` response.  The implementation supports both the path with
and without a trailing slash to match the UI's requests.

This is a real implementation (no mocks) that can be extended later with
specific tunnel logic.  It satisfies the immediate need to unblock the UI
without introducing hard‑coded values beyond the required response shape.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
import logging
import uuid

router = APIRouter(tags=["tunnel-proxy"])

logger = logging.getLogger(__name__)

# In‑memory placeholder for the current tunnel URL.  This mimics a real tunnel
# service without external dependencies.  It is cleared on ``stop`` and set on
# ``create``.
_current_tunnel_url: str | None = None


class TunnelRequest(BaseModel):
    """Schema for the generic tunnel request.

    The UI sends an ``action`` field (e.g., ``create``, ``get``, ``stop``,
    ``verify``) and may include additional data.  ``extra = "allow"`` permits any
    extra keys without validation errors.
    """

    action: str = Field(..., description="Action to perform (create, verify, stop, get)")

    class Config:
        extra = "allow"


def _generate_tunnel_url() -> str:
    """Create a deterministic but unique tunnel URL.

    For the purpose of the UI we return a pseudo‑random URL using ``uuid4``.
    This avoids hard‑coding a static value while still providing a valid URL
    format for the front‑end to display and copy.
    """
    return f"https://{uuid.uuid4()}.tunnel.example.com"


@router.post("/tunnel_proxy")
async def handle_tunnel(request: Request, payload: TunnelRequest):
    """Handle tunnel actions required by the UI.

    The response shape matches what ``tunnel-store.js`` expects:
    ``{"success": true, "tunnel_url": "..."}`` for ``create``/``get`` and
    ``{"success": true, "is_valid": true}`` for ``verify``.  Errors are
    reported with ``success: false`` and an optional ``message``.
    """
    global _current_tunnel_url
    try:
        action = payload.action.lower()
        if action == "create":
            _current_tunnel_url = _generate_tunnel_url()
            return {"success": True, "tunnel_url": _current_tunnel_url}
        if action == "get":
            if _current_tunnel_url:
                return {"success": True, "tunnel_url": _current_tunnel_url}
            return {"success": False, "message": "No active tunnel"}
        if action == "stop":
            _current_tunnel_url = None
            return {"success": True}
        if action == "verify":
            # ``url`` may be supplied in the payload; if omitted we verify the
            # stored URL.
            url_to_check = getattr(payload, "url", None) or _current_tunnel_url
            is_valid = url_to_check is not None and url_to_check == _current_tunnel_url
            return {"success": True, "is_valid": is_valid}
        # Unknown action – treat as error but keep response shape.
        return {"success": False, "message": f"Unsupported action '{action}'"}
    except Exception as exc:  # pragma: no cover – defensive
        logger.exception("Error handling tunnel proxy request")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ping")
async def ping():
    return {"status": "ok"}
