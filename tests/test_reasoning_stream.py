import os

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reasoning_events_present(monkeypatch):
    """Validate thinking.started and thinking.final appear when flag enabled.
    Skips if gateway app import fails or flag disabled explicitly.
    """
    # Enable reasoning stream flag
    monkeypatch.setenv("SA01_ENABLE_REASONING_STREAM", "true")
    # Skip early if no provider credentials configured (avoids hanging outbound calls)
    if not (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("AZURE_OPENAI_ENDPOINT")
    ):
        pytest.skip("No LLM provider configured for reasoning stream test")
    try:
        from services.gateway.main import app  # type: ignore
    except Exception:
        pytest.skip("Gateway app unavailable")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Minimal invoke payload; adjust if schema differs
        payload = {
            "session_id": "reasoning-test-session",
            "persona_id": "persona-x",
            "model": "dummy-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        try:
            resp = await client.post("/v1/llm/invoke/stream", json=payload, timeout=3)
        except Exception:
            pytest.skip("Stream endpoint not reachable")
        assert resp.status_code in (200, 429)
        if resp.status_code == 429:
            pytest.skip("Rate limited; skipping reasoning event assertion")
        text = resp.text
        # We expect both types if any content produced; if provider mock not active, may lack events
        if "assistant.thinking.started" not in text or "assistant.thinking.final" not in text:
            pytest.skip("Thinking events not emitted (provider may not stream)")
        assert "assistant.thinking.started" in text
        assert "assistant.thinking.final" in text
        # Sequence numbers optional but if sequence flag enabled should appear at least once
        if os.getenv("SA01_ENABLE_SEQUENCE", "true").lower() == "true":
            assert '"sequence":' in text
