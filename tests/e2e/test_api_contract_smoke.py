import asyncio
import json
import os
import time

import pytest
import httpx


@pytest.mark.asyncio
async def test_sse_api_contract_smoke():
    """API contract smoke:
    - POST /v1/session/message to create/queue a message
    - Open SSE /v1/session/{id}/events and assert we observe an assistant event

    Notes: This is a smoke test intended for local/dev runs where the Gateway and workers
    may or may not be fully available. The test is tolerant: it fails only if the UI
    cannot issue the initial POST or if no assistant event appears within the timeout.
    """

    BASE = os.environ.get("BASE_URL") or os.environ.get("WEB_UI_BASE_URL") or "http://127.0.0.1:21016"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Post a message (use the lightweight message shape used by scripts/e2e_quick.py)
        payload = {"message": "smoke-test: hello from pytest"}
        r = await client.post(f"{BASE}/v1/session/message", headers={"Content-Type": "application/json"}, json=payload)
        assert r.status_code in (200, 201, 202), f"POST /v1/session/message failed: {r.status_code} {r.text[:200]}"
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        session_id = data.get("session_id") or data.get("id") or data.get("session")
        assert session_id, f"No session_id in response: {data}"

    # Open SSE stream and look for assistant message events
    found_assistant = False
    deadline = time.time() + 30
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", f"{BASE}/v1/session/{session_id}/events") as resp:
            assert resp.status_code == 200, f"SSE open failed: {resp.status_code}"
            buf = ""
            async for chunk in resp.aiter_text():
                buf += chunk
                # SSE events are separated by a blank line
                while "\n\n" in buf:
                    part, buf = buf.split("\n\n", 1)
                    line = part.strip()
                    if not line.startswith("data:"):
                        continue
                    body = line[5:].strip()
                    try:
                        ev = json.loads(body)
                    except Exception:
                        continue
                    role = (ev.get("role") or "").lower()
                    msg = ev.get("message") or ev.get("chunk") or ""
                    if role == "assistant" or (msg and len(msg) > 0 and role == ""):
                        found_assistant = True
                        break
                if found_assistant or time.time() > deadline:
                    break

    assert found_assistant, "Did not observe an assistant event via SSE within 30s"
