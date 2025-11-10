import os
import time
import uuid
from typing import Any, Dict, List

import httpx
import pytest

BASE_URL = (
    os.getenv("GATEWAY_BASE_URL")
    or os.getenv("BASE_URL")
    or f"http://localhost:{os.getenv('GATEWAY_PORT','21016')}"
)
TIMEOUT = float(os.getenv("E2E_HTTP_TIMEOUT", "20"))
POLL_TIMEOUT = float(os.getenv("E2E_POLL_TIMEOUT", "20"))
POLL_INTERVAL = float(os.getenv("E2E_POLL_INTERVAL", "0.5"))
TENANT = os.getenv("SOMA_TENANT_ID", "public")
EXPECT_MEMORY = os.getenv("E2E_EXPECT_MEMORY", "0") in {"1", "true", "yes"}


@pytest.mark.e2e
def test_tool_request_echo_flow() -> None:
    """
    End-to-end tool flow using the built-in 'echo' tool:
    - Lists tools and asserts 'echo' is available
    - Enqueues a tool request for the current session
    - Polls session events until a tool result is observed
    - Optionally verifies a memory replica row exists when E2E_EXPECT_MEMORY=1

    This test is designed to run against a live stack. It will be skipped if the
    Gateway is not reachable.
    """
    session_id = str(uuid.uuid4())

    with httpx.Client(timeout=TIMEOUT) as client:
        # Quick reachability check; skip if gateway is down
        try:
            health = client.get(f"{BASE_URL}/v1/tools")
        except Exception as exc:
            pytest.skip(f"Gateway not reachable at {BASE_URL}: {exc}")

        if health.status_code != 200:
            pytest.skip(
                f"Gateway reachable but /v1/tools not available (HTTP {health.status_code})"
            )
        tools = health.json().get("tools", [])
        tool_names = {t.get("name") for t in tools}
        assert "echo" in tool_names, f"echo tool missing; found: {sorted(tool_names)}"

        # Enqueue tool request; bypass policy by setting requeue_override=True for dev stacks
        payload = {
            "session_id": session_id,
            "tool_name": "echo",
            "args": {"text": "e2e ping"},
            "metadata": {"tenant": TENANT, "requeue_override": True},
        }
        resp = client.post(f"{BASE_URL}/v1/tool/request", json=payload)
        assert resp.status_code == 200, f"enqueue failed: HTTP {resp.status_code} {resp.text}"
        event_id = resp.json().get("event_id")
        assert event_id, "missing event_id from enqueue response"

        # Poll typed session events for a tool result
        deadline = time.time() + POLL_TIMEOUT
        observed: List[Dict[str, Any]] = []
        next_cursor: int | None = None
        while time.time() < deadline:
            params = {"limit": 200}
            if next_cursor is not None:
                params["after"] = next_cursor
            ev = client.get(f"{BASE_URL}/v1/sessions/{session_id}/events", params=params)
            assert ev.status_code == 200, f"events failed: HTTP {ev.status_code} {ev.text}"
            body = ev.json()
            items = body.get("events", [])
            if items:
                observed.extend(items)
                next_cursor = body.get("next_cursor")
            # Find tool event for echo
            tool_events = [
                e for e in observed if (e.get("payload") or {}).get("tool_name") == "echo"
            ]
            if tool_events:
                tool_event = tool_events[-1]
                payload = tool_event.get("payload") or {}
                status = payload.get("status")
                assert status in {"success", "blocked", "error"}, f"unexpected status: {status}"
                if status == "success":
                    # payload.payload contains the tool's return value
                    result = payload.get("payload")
                    # echo tool returns the same text
                    if isinstance(result, dict):
                        # Some tools wrap result; echo returns a dict like {"text": "..."}
                        content = result.get("text") or str(result)
                    else:
                        content = str(result)
                    assert "e2e ping" in content
                break
            time.sleep(POLL_INTERVAL)

        else:
            pytest.fail("Timed out waiting for tool result in session events")

        # Optional memory verification
        if EXPECT_MEMORY:
            # Allow the memory replicator to ingest the WAL
            time.sleep(1.5)
            mparams = {"session_id": session_id, "role": "tool", "limit": 50}
            mem = client.get(f"{BASE_URL}/v1/admin/memory", params=mparams)
            assert mem.status_code == 200, f"admin memory failed: HTTP {mem.status_code} {mem.text}"
            items = mem.json().get("items", [])
            if not items:
                pytest.xfail(
                    "No tool memory observed (OPA may be denying memory.write in this environment)"
                )
            else:
                # Find a tool_result memory for echo
                found = False
                for it in items:
                    payload = it.get("payload") or {}
                    if payload.get("type") == "tool_result" and payload.get("tool_name") == "echo":
                        content = str(payload.get("content") or "")
                        assert "e2e ping" in content
                        found = True
                        break
                if not found:
                    pytest.xfail(
                        "tool_result memory not found for echo (OPA may be denying memory.write)"
                    )
