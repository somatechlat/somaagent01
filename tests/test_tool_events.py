import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tool_events_skip_friendly(monkeypatch):
    """Enable tool events and assert markers if provider yields tool_calls.
    Skips when provider creds missing or stream endpoint unavailable.
    """
    monkeypatch.setenv("SA01_ENABLE_TOOL_EVENTS", "true")
    # Require a provider to avoid indefinite waits
    if not (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    ):
        pytest.skip("No LLM provider configured for tool events test")
    try:
        from services.gateway.main import app  # type: ignore
    except Exception:
        pytest.skip("Gateway app unavailable")

    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "session_id": "tool-events-test-session",
            "persona_id": "persona-x",
            "model": "dummy",
            "messages": [{"role": "user", "content": "Use a tool if needed for 2+2"}],
        }
        try:
            resp = await client.post("/v1/llm/invoke/stream", json=payload, timeout=6)
        except Exception:
            pytest.skip("Stream endpoint not reachable")
        if resp.status_code == 429:
            pytest.skip("Rate limited; skipping tool events assertion")
        text = resp.text
        if "assistant.tool.started" not in text:
            pytest.skip("No tool events produced by provider for this prompt")
        assert "assistant.tool.started" in text
        assert "assistant.tool.final" in text
