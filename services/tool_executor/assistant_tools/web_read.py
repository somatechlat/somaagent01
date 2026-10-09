"""web_read — fetch one public URL and return extracted text (TOOLS-001 §5.10).

Used after web_search: take a hit URL and pull readable content without a
full browser. SSRF: refuses private/link-local/metadata hosts. No cookies,
no auth headers from the model. Max body capped.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    tool_error,
)

MAX_CHARS = 12000
REQUEST_TIMEOUT_S = 20.0
MAX_BYTES = 2_000_000


def _is_public_http_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return False
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    # Literal IP hosts: refuse private / link-local / reserved.
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_global and not ip.is_link_local and not ip.is_reserved
    except ValueError:
        pass  # DNS name — resolved by the HTTP stack; still refuse obvious hosts
    if host.endswith(".internal") or host.endswith(".lan"):
        return False
    return True


def html_to_text(html: str) -> str:
    """Very small HTML → text (no external deps). Script/style stripped."""
    text = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>|</div>|</li>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


class WebReadTool(SomaAssistantTool):
    """Fetch a public HTTP(S) URL and return extracted plain text."""

    name = "web_read"
    description = (
        "Fetch one public web URL and return extracted plain text (for use "
        "after web_search). Refuses private/localhost URLs. Max ~12k chars. "
        "Approval-gated; requires AgentIQ egress."
    )
    tier = 2
    needs_workroot = False
    needs_egress = True

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Absolute http(s) URL from a search result or user",
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[Any] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        url = str((args or {}).get("url") or "").strip()
        if not url:
            raise tool_error("url is required")
        if not _is_public_http_url(url):
            raise tool_error(
                "web_read only fetches public http(s) URLs "
                "(private, link-local, and localhost are refused)"
            )

        ctype = ""
        try:
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT_S,
                follow_redirects=True,
                limits=httpx.Limits(max_redirects=5),
            ) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    ctype = response.headers.get("content-type", "")
                    if "html" not in ctype and "text/" not in ctype and ctype:
                        raise tool_error(
                            f"web_read only reads HTML/text (content-type={ctype})"
                        )
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        chunks.append(chunk)
                        total += len(chunk)
                        if total > MAX_BYTES:
                            break
                    raw = b"".join(chunks)[:MAX_BYTES]
        except httpx.HTTPError as exc:
            raise tool_error(f"web_read failed: {exc}") from exc

        text = raw.decode("utf-8", errors="replace")
        looks_html = "html" in ctype or text.lstrip()[:200].lower().startswith(
            ("<!doctype", "<html", "<head")
        )
        if looks_html:
            text = html_to_text(text)
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + f"\n…[truncated {len(text) - MAX_CHARS} chars]"
        if not text.strip():
            raise tool_error("web_read extracted empty text from the page")
        return {"url": url, "chars": len(text), "text": text}


WEB_READ_ASSISTANT_TOOLS: list[SomaAssistantTool] = [WebReadTool()]
