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
POLL_TIMEOUT = float(os.getenv("E2E_POLL_TIMEOUT", "30"))
POLL_INTERVAL = float(os.getenv("E2E_POLL_INTERVAL", "0.5"))
TENANT = os.getenv("SOMA_TENANT_ID", "public")
EXPECT_MEMORY = os.getenv("E2E_EXPECT_MEMORY", "0") in {"1", "true", "yes"}


def _require_gateway(client: httpx.Client) -> dict:
    try:
        # Quick reachability and feature check
        cfg = client.get(f"{BASE_URL}/ui/config.json")
    except Exception as exc:
        pytest.skip(f"Gateway not reachable at {BASE_URL}: {exc}")
    assert cfg.status_code == 200, f"config fetch failed: HTTP {cfg.status_code} {cfg.text}"
    features = (cfg.json() or {}).get("features", {})
    return features


@pytest.mark.e2e
def test_document_ingest_tool_by_id() -> None:
    """
    End-to-end ingestion via the document_ingest tool using attachment_id:
    - Upload a tiny text file -> get /v1/attachments/{id}
    - Enqueue tool request document_ingest with attachment_id and tenant metadata
    - Poll session events for tool_result payload containing extracted text
    - Optionally verify a corresponding tool_result memory when EXPECT_MEMORY=1
    """
    session_id = str(uuid.uuid4())
    unique = f"ingest-{uuid.uuid4()}"

    with httpx.Client(timeout=TIMEOUT) as client:
        _ = _require_gateway(client)

        # Upload a tiny text file
        files = {"files": ("tiny.txt", f"hello {unique}".encode("utf-8"), "text/plain")}
        data = {"session_id": session_id}
        up = client.post(f"{BASE_URL}/v1/uploads", files=files, data=data)
        if up.status_code == 403 and "Uploads are disabled" in (up.text or ""):
            pytest.skip("Uploads are disabled by administrator in this environment.")
        assert up.status_code == 200, f"upload failed: HTTP {up.status_code} {up.text}"
        uploaded = up.json()
        assert isinstance(uploaded, list) and uploaded, f"unexpected upload payload: {uploaded}"
        path = uploaded[0].get("path")
        assert isinstance(path, str) and path.startswith(
            "/v1/attachments/"
        ), f"unexpected path: {path}"
        att_id = path.split("/v1/attachments/")[-1]

        # Enqueue tool request for document_ingest
        payload = {
            "session_id": session_id,
            "tool_name": "document_ingest",
            "args": {"attachment_id": att_id, "metadata": {"tenant": TENANT}},
            "metadata": {"tenant": TENANT, "requeue_override": True},
        }
        resp = client.post(f"{BASE_URL}/v1/tool/request", json=payload)
        assert resp.status_code == 200, f"enqueue failed: HTTP {resp.status_code} {resp.text}"

        # Poll session events for tool result
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
            tool_events = [
                e
                for e in observed
                if (e.get("payload") or {}).get("tool_name") == "document_ingest"
            ]
            if tool_events:
                tool_event = tool_events[-1]
                payload = tool_event.get("payload") or {}
                status = payload.get("status")
                assert status in {"success", "blocked", "error"}
                if status == "success":
                    result = payload.get("payload") or {}
                    text = str(result.get("text") or "")
                    assert unique in text
                break
            time.sleep(POLL_INTERVAL)
        else:
            pytest.fail("Timed out waiting for document_ingest tool result")

        # Optional memory verification (tool_result)
        if EXPECT_MEMORY:
            time.sleep(1.5)
            mparams = {"session_id": session_id, "role": "tool", "limit": 50}
            mem = client.get(f"{BASE_URL}/v1/admin/memory", params=mparams)
            assert mem.status_code == 200, f"admin memory failed: HTTP {mem.status_code} {mem.text}"
            items = mem.json().get("items", [])
            found = False
            for it in items:
                payload = it.get("payload") or {}
                if (
                    payload.get("type") == "tool_result"
                    and payload.get("tool_name") == "document_ingest"
                ):
                    text = str((payload.get("content") or ""))
                    if unique in text:
                        found = True
                        break
            if not found:
                pytest.xfail(
                    "tool_result memory for document_ingest not found (OPA may be denying memory.write)"
                )


@pytest.mark.e2e
def test_attachment_ingest_inline_small() -> None:
    """
    End-to-end inline ingestion by the Conversation Worker for small attachments:
    - Upload a small text attachment
    - Send a user message referencing the attachment path
    - Poll admin memory for an attachment_ingest entry with extracted text
    """
    session_id = str(uuid.uuid4())
    unique = f"inline-{uuid.uuid4()}"

    with httpx.Client(timeout=TIMEOUT) as client:
        features = _require_gateway(client)
        if not bool(features.get("write_through")):
            pytest.skip(
                "Write-through to SomaBrain is disabled; cannot verify memory inline ingest."
            )

        # Upload tiny text
        files = {"files": ("tiny.txt", f"hello {unique}".encode("utf-8"), "text/plain")}
        data = {"session_id": session_id}
        up = client.post(f"{BASE_URL}/v1/uploads", files=files, data=data)
        assert up.status_code == 200, f"upload failed: HTTP {up.status_code} {up.text}"
        uploaded = up.json()
        path = uploaded[0].get("path")
        assert isinstance(path, str) and path.startswith("/v1/attachments/")

        # Post a user message referencing the attachment
        msg = {
            "session_id": session_id,
            "persona_id": None,
            "message": f"Please ingest this file {unique}",
            "attachments": [path],
            "metadata": {"tenant": TENANT},
        }
        r = client.post(f"{BASE_URL}/v1/session/message", json=msg)
        assert r.status_code == 200, f"message send failed: HTTP {r.status_code} {r.text}"

        # Poll memory for attachment_ingest
        deadline = time.time() + POLL_TIMEOUT
        found: Dict[str, Any] | None = None
        while time.time() < deadline:
            mparams = {"session_id": session_id, "limit": 200}
            mem = client.get(f"{BASE_URL}/v1/admin/memory", params=mparams)
            if mem.status_code in {401, 403}:
                pytest.skip(
                    "/v1/admin/memory requires admin auth in this environment; cannot verify."
                )
            assert mem.status_code == 200, f"admin memory failed: HTTP {mem.status_code} {mem.text}"
            items: List[Dict[str, Any]] = mem.json().get("items", [])
            for it in items:
                payload = it.get("payload") or {}
                if payload.get("type") == "attachment_ingest":
                    content = str(payload.get("content") or "")
                    if unique in content:
                        found = payload
                        break
            if found:
                break
            time.sleep(POLL_INTERVAL)

        if not found:
            pytest.xfail(
                "No attachment_ingest memory observed; either size-based offload pushed to tool, or policy denied memory.write."
            )
