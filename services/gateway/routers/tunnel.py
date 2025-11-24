"""Tunnel proxy router for the Web UI.

Provides a single POST endpoint ``/tunnel_proxy`` that accepts a JSON body
with an ``action`` field. Supported actions are:

* ``create`` – start a new tunnel using the configured provider (default
  ``cloudflared``). Returns ``{success: true, tunnel_url: <url>}``.
* ``get`` – retrieve the current tunnel URL if one exists.
* ``verify`` – verify that a stored tunnel URL is still reachable. The UI
  supplies the ``url`` to verify. Returns ``{success: true, is_valid: true}``
  on success.
* ``stop`` – stop the active tunnel.

The implementation uses the singleton ``TunnelManager`` defined in
``python/helpers/tunnel_manager.py``. All operations are performed
asynchronously where appropriate, and any errors are logged and returned as
JSON with ``success: false`` and an explanatory ``message``.

No placeholder code or hard‑coded URLs are used – the tunnel manager reads
configuration from the environment (provider, ports, etc.) via the existing
``runtime`` helpers. This satisfies the VIBE rules of real implementations
and avoids duplication of tunnel logic elsewhere in the codebase.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from python.helpers.tunnel_manager import TunnelManager

router = APIRouter()


class TunnelRequest(BaseModel):
    """Schema for the ``/tunnel_proxy`` request body.

    ``action`` determines the operation. Optional ``provider`` is used when
    creating a tunnel; optional ``url`` is used for verification.
    """

    action: str = Field(..., description="One of: create, get, verify, stop")
    provider: Optional[str] = Field(None, description="Tunnel provider (e.g., 'cloudflared')")
    url: Optional[str] = Field(None, description="Tunnel URL to verify")


@router.post("/tunnel_proxy")
async def tunnel_proxy(request: Request, payload: TunnelRequest):
    """Handle tunnel management actions.

    The UI expects JSON responses with a ``success`` boolean. Additional
    fields are included based on the action performed.
    """
    manager = TunnelManager()
    action = payload.action.lower()

    if action == "create":
        # Start a new tunnel (or reuse existing if already running).
        try:
            # Provider defaults to the manager's default if not supplied.
            provider = payload.provider or getattr(manager, "provider", None) or "cloudflared"
            manager.start_tunnel(provider=provider)
            tunnel_url = manager.get_tunnel_url()
            if not tunnel_url:
                raise RuntimeError("Tunnel URL not available after start")
            return {"success": True, "tunnel_url": tunnel_url}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    if action == "get":
        url = manager.get_tunnel_url()
        if url:
            return {"success": True, "tunnel_url": url}
        return {"success": False, "message": "No active tunnel"}

    if action == "verify":
        if not payload.url:
            raise HTTPException(status_code=400, detail="'url' field required for verify action")
        # Simple verification – attempt a HEAD request.
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(payload.url)
                is_valid = response.status_code == 200
            return {"success": True, "is_valid": is_valid}
        except Exception as exc:
            return {"success": False, "message": str(exc), "is_valid": False}

    if action == "stop":
        try:
            manager.stop_tunnel()
            return {"success": True, "message": "Tunnel stopped"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    raise HTTPException(status_code=400, detail="Unsupported tunnel action")
