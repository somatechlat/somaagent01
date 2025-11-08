import os

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ui_settings_sections_uploads_roundtrip(monkeypatch):
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping integration test")

    # Ensure gateway uses test Postgres
    monkeypatch.setenv("POSTGRES_DSN", dsn)

    client = TestClient(app)

    # Fetch current sections to get baseline shape
    resp = client.get("/v1/ui/settings/sections")
    assert resp.status_code == 200
    data = resp.json().get("settings", {})
    assert isinstance(data, dict)
    assert any(
        sec.get("id") == "uploads" for sec in data.get("sections", [])
    ), "uploads section present"

    # Build a payload with updated uploads settings
    uploads_updates = {
        "uploads_enabled": True,
        "uploads_max_mb": 8,
        "uploads_max_files": 3,
        "uploads_allowed_mime": "text/plain,application/pdf",
        "uploads_denied_mime": "application/x-msdownload",
        # uploads_dir is read-only; ensure server ignores changes
        "uploads_inline_max_mb": 4,
        "uploads_allow_external_ref": False,
        "uploads_external_ref_allowlist": "example.com,files.example.org",
        "uploads_dedup_sha256": True,
        "uploads_quarantine_policy": "store_and_block",
        "uploads_download_token_ttl_seconds": 0,
        "uploads_ttl_days": 5,
        "uploads_janitor_interval_seconds": 1200,
    }

    sections = data.get("sections", [])
    # Replace or append uploads section with the updates
    new_sections = []
    for sec in sections:
        if sec.get("id") == "uploads":
            fields = []
            for f in sec.get("fields", []):
                fid = f.get("id")
                if fid in uploads_updates:
                    f = {**f, "value": uploads_updates[fid]}
                fields.append(f)
            new_sections.append({**sec, "fields": fields})
        else:
            new_sections.append(sec)

    # Persist via POST
    resp = client.post("/v1/ui/settings/sections", json={"sections": new_sections})
    assert resp.status_code == 200

    # Re-fetch and verify our values are reflected
    resp2 = client.get("/v1/ui/settings/sections")
    assert resp2.status_code == 200
    data2 = resp2.json().get("settings", {})
    uploads = next(sec for sec in data2.get("sections", []) if sec.get("id") == "uploads")
    vals = {f["id"]: f.get("value") for f in uploads.get("fields", [])}
    for k, v in uploads_updates.items():
        assert vals.get(k) == v, f"expected {k}={v}, got {vals.get(k)}"
