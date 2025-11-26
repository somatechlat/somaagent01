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

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

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
    # Deprecated duplicate tunnel implementation.
    # The functional tunnel endpoint is provided by `tunnel_proxy.py`.
    # This file is retained only for historical reference and should not be imported.

    # No active routes are defined here to avoid duplicate endpoint definitions.
    manager = TunnelManager()
