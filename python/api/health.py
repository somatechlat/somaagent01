from __future__ import annotations

import os
import json as _json
import httpx

from python.helpers import errors, git
from python.helpers.api import ApiHandler, Request, Response


class HealthCheck(ApiHandler):

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        """Return UI health plus Gateway/SomaBrain health aggregation.

        The Web UI polls this endpoint to drive the connection status. We proxy
        Gateway health (`/healthz`) so the UI can disable Send when the
        conversation path is unhealthy. This avoids CORS issues and keeps a
        single origin for the SPA.
        """
        gitinfo = None
        error = None
        try:
            gitinfo = git.get_git_info()
        except Exception as e:  # pragma: no cover (best-effort)
            error = errors.error_text(e)

        status = "ok"
        components: dict[str, dict[str, str]] = {}

        # Determine Gateway base (same logic as gateway_stream)
        base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")
        gw_url = f"{base}/healthz"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(gw_url)
                resp.raise_for_status()
                data = resp.json() if resp.content else {}
            status = (data.get("status") or "ok") if isinstance(data, dict) else "ok"
            components = (data.get("components") or {}) if isinstance(data, dict) else {}
        except Exception as exc:
            # Fallback to host.docker.internal:<GATEWAY_PORT> for dev
            try:
                host_alias = os.getenv("SOMA_CONTAINER_HOST_ALIAS", "host.docker.internal")
                gw_port = os.getenv("GATEWAY_PORT", "21016")
                alt = f"http://{host_alias}:{gw_port}/healthz"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(alt)
                    resp.raise_for_status()
                    data = resp.json() if resp.content else {}
                status = (data.get("status") or "ok") if isinstance(data, dict) else "ok"
                components = (data.get("components") or {}) if isinstance(data, dict) else {}
            except Exception:
                status = "down"
                components = {"gateway": {"status": "down", "detail": f"{type(exc).__name__}: {str(exc)}"}}

        # Return a combined payload (keep legacy fields for compatibility)
        return {
            "status": status,
            "components": components,
            "gitinfo": gitinfo,
            "error": error,
        }
