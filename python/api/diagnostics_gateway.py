from __future__ import annotations

import os
from urllib.parse import urlparse

from python.helpers.api import ApiHandler, Request, Response


class DiagnosticsGateway(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        ui_host = request.host or ""
        gw_base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016"))
        parsed = urlparse(gw_base)
        gw_host = f"{parsed.hostname}:{parsed.port or (80 if parsed.scheme=='http' else 443)}"
        equal = False
        try:
            equal = (gw_host == ui_host) or (
                parsed.hostname in {"127.0.0.1", "localhost"} and ui_host.endswith(f":{parsed.port or (80 if parsed.scheme=='http' else 443)}")
            )
        except Exception:
            equal = False

        return {
            "ui_use_gateway": os.getenv("UI_USE_GATEWAY", "false"),
            "ui_host": ui_host,
            "gateway_base": gw_base,
            "same_origin": bool(equal),
        }

