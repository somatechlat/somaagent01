"""web_search — SearxNG meta-search (SOMA-ARCH-TOOLS-001 §5.10).

A0's search_engine hardcodes ``http://localhost:55510/search``. Soma resolves
``SEARXNG_URL`` through the operator settings chain
(``require_service_url``); a missing setting fails closed naming
``SEARXNG_URL``. The base host is never taken from the model (SSRF).

Call: ``GET {SEARXNG_URL}/search?q=...&format=json`` via httpx. Results are
``results[].title/url/content`` — top k (default 8, max 20), digest truncated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from django.core.exceptions import ImproperlyConfigured

from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    tool_error,
)

DEFAULT_K = 8
MAX_K = 20
DIGEST_MAX_CHARS = 300
REQUEST_TIMEOUT_S = 15.0
# Engine names SearxNG accepts on the query string (not hosts/URLs). Private
# CAPTCHA engines (DDG/startpage/brave) are left out of the default set.
DEFAULT_ENGINES = "google,bing,wikipedia,mojeek"


def web_search_enabled() -> bool:
    """Operator switch: Settings · search.enabled (WEB_SEARCH_ENABLED)."""
    from admin.core.helpers.settings import get_settings

    model = get_settings()
    raw = getattr(model, "web_search_enabled", True)
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw)


def require_searxng_base() -> str:
    """Resolve SEARXNG_URL through the settings chain, or refuse.

    No localhost, no invented host. Failure names the setting so an
    operator knows exactly what to configure (VIBE Rule 91 / TOOLS-001
    §5.10.6).
    """
    from admin.core.helpers.service_urls import require_service_url

    try:
        base = str(require_service_url("SEARXNG_URL")).strip()
    except ImproperlyConfigured as exc:
        raise tool_error(
            "SEARXNG_URL is not configured. web_search refuses to guess a "
            "SearxNG host (TOOLS-001 §5.10.6). Set SEARXNG_URL through the "
            f"administration settings. Cause: {exc}"
        ) from exc
    if not base:
        raise tool_error(
            "SEARXNG_URL is not configured. web_search refuses to guess a "
            "SearxNG host (TOOLS-001 §5.10.6). Set SEARXNG_URL through the "
            "administration settings."
        )
    return base.rstrip("/")


def parse_searxng_results(
    payload: Any,
    *,
    k: int = DEFAULT_K,
    digest_max: int = DIGEST_MAX_CHARS,
) -> List[Dict[str, str]]:
    """Parse SearxNG JSON into top-k ``{title, url, content}`` hits.

    SearxNG ``format=json`` returns ``{"results": [{title, url, content}, …]}``.
    Missing url drops the hit; content is truncated to ``digest_max``.
    """
    if not isinstance(payload, dict):
        return []
    raw = payload.get("results")
    if not isinstance(raw, list):
        return []
    limit = max(1, min(int(k), MAX_K))
    hits: List[Dict[str, str]] = []
    for item in raw:
        if len(hits) >= limit:
            break
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or item.get("snippet") or "").strip()
        if digest_max > 0 and len(content) > digest_max:
            content = content[:digest_max]
        hits.append({"title": title, "url": url, "content": content})
    return hits


class WebSearchTool(SomaAssistantTool):
    """Search the web via the operator-configured SearxNG instance."""

    name = "web_search"
    description = (
        "Search the web through the operator-configured SearxNG instance. "
        "Pass a query and optional k (top hits, default 8, max 20). Returns "
        "title/url/content digests. Requires SEARXNG_URL and AgentIQ egress; "
        "never uses a model-supplied host."
    )
    tier = 2
    needs_workroot = False
    needs_egress = True

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text",
                },
                "k": {
                    "type": "integer",
                    "description": "Max results (default 8, max 20).",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[Any] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        data = args or {}
        query = str(data.get("query") or "").strip()
        if not query:
            raise tool_error("query is required")
        try:
            k = int(data.get("k") if data.get("k") is not None else DEFAULT_K)
        except (TypeError, ValueError):
            k = DEFAULT_K
        k = max(1, min(k, MAX_K))

        if not web_search_enabled():
            raise tool_error(
                "web_search is disabled (WEB_SEARCH_ENABLED / Settings · search "
                "· enabled). Enable it in administration settings to search."
            )

        base = require_searxng_base()
        # SSRF: only the configured base host. Query params carry the
        # user text; the model never supplies a URL.
        endpoint = f"{base}/search"
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
                response = await client.get(
                    endpoint,
                    params={
                        "q": query,
                        "format": "json",
                        "engines": DEFAULT_ENGINES,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise tool_error(
                f"web_search failed talking to configured SearxNG: {exc}"
            ) from exc
        except ValueError as exc:
            raise tool_error(
                f"web_search got a non-JSON body from SearxNG: {exc}"
            ) from exc

        results = parse_searxng_results(payload, k=k)
        return {
            "query": query,
            "k": k,
            "count": len(results),
            "results": results,
        }


WEB_SEARCH_ASSISTANT_TOOLS: List[SomaAssistantTool] = [
    WebSearchTool(),
]
