"""Integration tests for Gateway LLM invoke (requires local Gateway and internal token).

Usage (run locally, do NOT paste secrets into chat):

export SA01_AUTH_INTERNAL_TOKEN="<paste-locally>"
export SA01_GATEWAY_BASE_URL="http://127.0.0.1:21016"
python -m pytest -q tests/test_llm_integration.py

This test performs two checks:
 - POST /v1/llm/test to verify profile resolution, credentials presence and reachability
 - POST /v1/llm/invoke/stream and reads SSE chunks for up to 10s to verify streaming works

The test will skip if SA01_AUTH_INTERNAL_TOKEN is not set.
"""

from __future__ import annotations

import json
import os
import time
import uuid

import httpx
import pytest

GATEWAY_BASE = os.getenv("SA01_GATEWAY_BASE_URL", "http://127.0.0.1:21016")
SA01_AUTH_INTERNAL_TOKEN = os.getenv("SA01_AUTH_INTERNAL_TOKEN")


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Internal-Token": SA01_AUTH_INTERNAL_TOKEN,
    }


def test_llm_test_endpoint():
    """Call /v1/llm/test and assert the gateway reports credentials and reachability."""
    if not SA01_AUTH_INTERNAL_TOKEN:
        pytest.skip("SA01_AUTH_INTERNAL_TOKEN not set in environment; skipping integration test")

    url = f"{GATEWAY_BASE}/v1/llm/test"
    resp = httpx.post(url, json={"role": "dialogue"}, headers=_headers(), timeout=10.0)
    assert resp.status_code == 200, f"llm/test returned {resp.status_code}: {resp.text}"
    j = resp.json()
    # Basic sanity: provider and credentials_present should be present
    assert isinstance(j.get("provider"), str), j
    assert j.get("credentials_present") is True, f"credentials_present is false: {j}"


def test_llm_invoke_stream_smoke():
    """Perform a streaming invoke and collect at least one chunk within timeout."""
    if not SA01_AUTH_INTERNAL_TOKEN:
        pytest.skip("SA01_AUTH_INTERNAL_TOKEN not set in environment; skipping integration test")

    url = f"{GATEWAY_BASE}/v1/llm/invoke/stream"
    payload = {
        "role": "dialogue",
        "messages": [{"role": "user", "content": "Hello — say one sentence about yourself."}],
        "session_id": str(uuid.uuid4()),
        # Prefer the OpenAI-prefixed model string per your request
        "overrides": {"model": "openai/gpt-oss-120b"},
    }

    # Use a sync client and stream to avoid adding async test deps
    with httpx.Client(timeout=None) as client:
        with client.stream("POST", url, json=payload, headers=_headers()) as resp:
            assert (
                resp.status_code == 200
            ), f"invoke/stream returned {resp.status_code}: {resp.text}"
            received = []
            start = time.time()
            for raw in resp.iter_lines():
                if not raw:
                    continue
                # raw may be bytes or str
                line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    obj = json.loads(data_str)
                except Exception:
                    received.append({"raw": data_str})
                    continue
                received.append(obj)
                # stop early if we have at least one non-error chunk
                if received:
                    break
                if time.time() - start > 10:
                    break

            assert (
                len(received) > 0
            ), f"No stream chunks received within timeout; last status {resp.status_code}"
            first = received[0]
            if isinstance(first, dict) and first.get("error"):
                pytest.fail(f"Provider returned error chunk: {first}")
