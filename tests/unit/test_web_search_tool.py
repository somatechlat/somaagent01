"""web_search — configured SearxNG only (TOOLS-001 §5.10).

Missing SEARXNG_URL fails closed naming the setting; JSON parse is pure;
the tool is on the network choke; httpx is mocked (never a live call).
"""

from __future__ import annotations

import pytest

from admin.core.tool_calling import _NETWORK_TOOLS
from services.tool_executor.assistant_tools.web_search import (
    DEFAULT_K,
    MAX_K,
    WebSearchTool,
    parse_searxng_results,
    require_searxng_base,
)
from services.tool_executor.tools import AVAILABLE_TOOLS, ToolExecutionError


class _FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=None,
                response=None,
            )

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Async context manager that records the search request and returns a canned body."""

    def __init__(self, payload, *, status_code: int = 200):
        self._payload = payload
        self._status_code = status_code
        self.calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None, **kwargs):
        self.calls.append({"url": url, "params": params})
        return _FakeResponse(self._payload, status_code=self._status_code)


# ---------------------------------------------------------------------------
# Settings: missing SEARXNG_URL refuses
# ---------------------------------------------------------------------------


def test_require_searxng_base_missing_refuses(monkeypatch):
    import admin.core.helpers.service_urls as service_urls
    from django.core.exceptions import ImproperlyConfigured

    def _refuse(name):
        assert name == "SEARXNG_URL"
        raise ImproperlyConfigured("SEARXNG_URL is not configured")

    monkeypatch.setattr(service_urls, "require_service_url", _refuse)
    with pytest.raises(ToolExecutionError) as exc:
        require_searxng_base()
    assert "SEARXNG_URL" in str(exc.value)


@pytest.mark.asyncio
async def test_run_missing_url_fails_closed(monkeypatch):
    import admin.core.helpers.service_urls as service_urls
    from django.core.exceptions import ImproperlyConfigured

    def _refuse(name):
        raise ImproperlyConfigured("SEARXNG_URL is not configured")

    monkeypatch.setattr(service_urls, "require_service_url", _refuse)
    with pytest.raises(ToolExecutionError) as exc:
        await WebSearchTool().run({"query": "soma"})
    assert "SEARXNG_URL" in str(exc.value)


def test_require_searxng_base_strips_trailing_slash(monkeypatch):
    import admin.core.helpers.service_urls as service_urls

    monkeypatch.setattr(
        service_urls, "require_service_url", lambda name: "https://searx.example/"
    )
    assert require_searxng_base() == "https://searx.example"


# ---------------------------------------------------------------------------
# Parse SearxNG JSON
# ---------------------------------------------------------------------------


def test_parse_searxng_results_top_k_and_fields():
    payload = {
        "results": [
            {"title": f"Hit {i}", "url": f"https://ex.test/{i}", "content": "c" * 400}
            for i in range(30)
        ]
    }
    hits = parse_searxng_results(payload, k=DEFAULT_K)
    assert len(hits) == DEFAULT_K
    assert hits[0]["title"] == "Hit 0"
    assert hits[0]["url"] == "https://ex.test/0"
    assert len(hits[0]["content"]) == 300  # digest truncated


def test_parse_searxng_results_k_capped_at_max():
    payload = {"results": [{"title": str(i), "url": f"https://e/{i}", "content": ""} for i in range(50)]}
    hits = parse_searxng_results(payload, k=999)
    assert len(hits) == MAX_K


def test_parse_searxng_results_drops_missing_url_and_non_dicts():
    payload = {
        "results": [
            {"title": "no-url", "content": "x"},
            "not-a-dict",
            {"title": "ok", "url": "https://ok.test", "content": "body"},
        ]
    }
    hits = parse_searxng_results(payload, k=10)
    assert hits == [{"title": "ok", "url": "https://ok.test", "content": "body"}]


def test_parse_searxng_results_empty_or_malformed():
    assert parse_searxng_results(None) == []
    assert parse_searxng_results({}) == []
    assert parse_searxng_results({"results": "nope"}) == []
    assert parse_searxng_results({"results": []}) == []


def test_parse_searxng_results_snippet_fallback():
    payload = {"results": [{"title": "t", "url": "https://s", "snippet": "from snippet"}]}
    hits = parse_searxng_results(payload)
    assert hits[0]["content"] == "from snippet"


# ---------------------------------------------------------------------------
# Network choke + registration
# ---------------------------------------------------------------------------


def test_web_search_on_network_tools():
    assert "web_search" in _NETWORK_TOOLS
    assert "http_fetch" in _NETWORK_TOOLS


def test_web_search_registered_with_egress_flag():
    tool = AVAILABLE_TOOLS.get("web_search")
    assert tool is not None
    assert isinstance(tool, WebSearchTool)
    assert tool.tier == 2
    assert tool.needs_egress is True
    assert tool.needs_workroot is False
    schema = tool.input_schema()
    assert schema["required"] == ["query"]


def test_default_kit_includes_web_search():
    from services.tool_executor.default_tools import (
        DEFAULT_AGENT_TOOLS,
        DEFAULT_TOOL_DESCRIPTIONS,
    )

    assert "web_search" in DEFAULT_AGENT_TOOLS
    assert "web_search" in DEFAULT_TOOL_DESCRIPTIONS


def test_capsule_policy_seeds_web_search_approval():
    import inspect

    from admin.core.models import core as core_models

    src = inspect.getsource(core_models.Capsule.save)
    assert "web_search" in src


# ---------------------------------------------------------------------------
# Happy path with mocked httpx — only configured host is contacted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_calls_only_configured_base(monkeypatch):
    import services.tool_executor.assistant_tools.web_search as mod

    monkeypatch.setattr(mod, "require_searxng_base", lambda: "https://searx.ops")
    fake = _FakeAsyncClient(
        {
            "results": [
                {"title": "A", "url": "https://a.test", "content": "alpha"},
                {"title": "B", "url": "https://b.test", "content": "beta"},
            ]
        }
    )
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda **kw: fake)

    out = await WebSearchTool().run({"query": "soma agent", "k": 2})
    assert out["count"] == 2
    assert out["results"][0]["url"] == "https://a.test"
    assert fake.calls[0]["url"] == "https://searx.ops/search"
    assert fake.calls[0]["params"] == {"q": "soma agent", "format": "json"}


@pytest.mark.asyncio
async def test_run_rejects_empty_query():
    with pytest.raises(ToolExecutionError) as exc:
        await WebSearchTool().run({"query": "  "})
    assert "query" in str(exc.value)
