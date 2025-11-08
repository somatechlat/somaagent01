from __future__ import annotations

import json
import os
import uuid

import httpx
import pytest

GATEWAY_BASE = os.getenv("GATEWAY_BASE", "http://localhost:21016")


@pytest.mark.asyncio
async def test_rate_limit_blocks_when_enabled(monkeypatch):
    if os.getenv("GATEWAY_RATE_LIMIT_ENABLED", "false").lower() not in {"true", "1", "yes", "on"}:
        pytest.skip("rate limit disabled")
    window = int(os.getenv("GATEWAY_RATE_LIMIT_WINDOW_SECONDS", "10"))
    max_req = int(os.getenv("GATEWAY_RATE_LIMIT_MAX_REQUESTS", "5"))
    url = f"{GATEWAY_BASE}/v1/runtime-config"
    blocked = False
    async with httpx.AsyncClient(timeout=5.0) as client:
        for _ in range(max_req + 2):
            r = await client.get(url)
            if r.status_code == 429:
                blocked = True
                break
    assert blocked, "expected 429 when rate limit enabled"


@pytest.mark.asyncio
async def test_sequence_metadata_present_if_enabled():
    if os.getenv("SA01_ENABLE_SEQUENCE", "true").lower() not in {"true", "1", "yes", "on"}:
        pytest.skip("sequence disabled")
    # Use internal streaming endpoint to generate deltas
    url = f"{GATEWAY_BASE}/v1/llm/invoke/stream?mode=canonical"
    token = os.getenv("GATEWAY_INTERNAL_TOKEN")
    if not token:
        pytest.skip("internal token not set")
    body = {
        "role": "dialogue",
        "session_id": str(uuid.uuid4()),
        "persona_id": None,
        "tenant": "public",
        "messages": [{"role": "user", "content": "Test sequence field."}],
        "overrides": {"model": os.getenv("TEST_STREAM_MODEL", "gpt-4o-mini"), "temperature": 0.0},
    }
    saw_sequence = False
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", url, json=body, headers={"X-Internal-Token": token}
            ) as rstream:
                if rstream.status_code != 200:
                    pytest.skip("stream endpoint not available")
                async for line in rstream.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    raw = line[len("data: ") :].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        obj = json.loads(raw)
                    except Exception:
                        continue
                    md = obj.get("metadata") or {}
                    if md.get("sequence") is not None:
                        saw_sequence = True
                        break
    except Exception:
        pytest.skip("gateway not reachable for stream test")
    assert saw_sequence, "expected sequence metadata on streamed events"
