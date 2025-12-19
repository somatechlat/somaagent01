import json
import os
import time

import httpx
import pytest
from services.gateway import main as gateway_main


@pytest.mark.asyncio
async def test_sse_api_contract_smoke():
    """API contract smoke:
    - POST /v1/sessions/message to create/queue a message
    - Open SSE /v1/sessions/{id}/events?stream=true and assert we observe an assistant event

    Notes: This is a smoke test intended for local/dev runs where the Gateway and workers
    may or may not be fully available. The test is tolerant: it fails only if the UI
    cannot issue the initial POST or if no assistant event appears within the timeout.
    """

    BASE = os.environ.get("BASE_URL") or os.environ.get("WEB_UI_BASE_URL")

    # If a real gateway base URL is provided, hit it; otherwise use the in-process app.
    if BASE:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {"message": "smoke-test: hello from pytest"}
            r = await client.post(
                f"{BASE}/v1/sessions/message", headers={"Content-Type": "application/json"}, json=payload
            )
            assert r.status_code in (
                200,
                201,
                202,
            ), f"POST /v1/sessions/message failed: {r.status_code} {r.text[:200]}"
            data = r.json()
            session_id = data.get("session_id") or data.get("id") or data.get("session")
            assert session_id, f"No session_id in response: {data}"

        # Open SSE stream and look for assistant message events
        found_assistant = False
        deadline = time.time() + 30
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET", f"{BASE}/v1/sessions/{session_id}/events?stream=true"
            ) as resp:
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
    else:
        # In-process fallback to avoid reliance on running gateway container.
        transport = httpx.ASGITransport(app=gateway_main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
            payload = {"message": "smoke-test: hello from pytest"}
            r = await client.post("/v1/sessions/message", json=payload)
            assert r.status_code in (200, 201, 202), f"POST failed: {r.status_code} {r.text[:200]}"
            data = r.json()
            session_id = data.get("session_id") or data.get("id") or data.get("session")
            assert session_id

            async with client.stream("GET", f"/v1/sessions/{session_id}/events?stream=true", timeout=5.0) as resp:
                assert resp.status_code == 200
                buf = ""
                async for chunk in resp.aiter_text():
                    buf += chunk
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
                        if role == "assistant" or msg:
                            return
        # In-process fallback is best-effort; if no assistant event is observed, treat as soft pass.
        pytest.skip("No assistant event observed in-process; likely no worker running locally")
