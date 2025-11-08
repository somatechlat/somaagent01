import os
import uuid

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chunked_upload_end_to_end(monkeypatch, tmp_path):
    dsn = os.getenv("TEST_POSTGRES_DSN") or os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN not set for integration")

    monkeypatch.setenv("POSTGRES_DSN", dsn)
    client = TestClient(app)

    session_id = str(uuid.uuid4())
    content = b"A" * (1024 * 1024 * 2 + 123)  # >2MB triggers chunk path easily
    filename = "large_test.bin"

    # INIT
    init_resp = client.post(
        "/v1/uploads/init",
        json={
            "filename": filename,
            "size": len(content),
            "mime": "application/octet-stream",
            "session_id": session_id,
        },
    )
    assert init_resp.status_code == 200, init_resp.text
    init_data = init_resp.json()
    upload_id = init_data["upload_id"]
    chunk_size = init_data["chunk_size"]
    assert upload_id and chunk_size

    # CHUNKS
    offset = 0
    while offset < len(content):
        end = min(offset + chunk_size, len(content))
        chunk = content[offset:end]
        files = {"chunk": (filename + ".part", chunk, "application/octet-stream")}
        data = {"offset": str(offset), "session_id": session_id}
        c_resp = client.post(f"/v1/uploads/{upload_id}/chunk", data=data, files=files)
        assert c_resp.status_code == 200, c_resp.text
        c_json = c_resp.json()
        assert c_json["bytes_received"] == end, "bytes_received should advance"
        offset = end

    # FINALIZE
    fin_resp = client.post(f"/v1/uploads/{upload_id}/finalize", json={"session_id": session_id})
    assert fin_resp.status_code == 200, fin_resp.text
    descriptor = fin_resp.json()
    assert descriptor["filename"] == filename
    assert descriptor["size"] == len(content)
    assert descriptor["mode"] == "chunked"
    assert descriptor["sha256"], "sha256 computed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_single_upload_progress(monkeypatch):
    dsn = os.getenv("TEST_POSTGRES_DSN") or os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN not set for integration")

    monkeypatch.setenv("POSTGRES_DSN", dsn)
    client = TestClient(app)
    session_id = str(uuid.uuid4())
    small = b"hello world" * 1000
    files = [("files", ("small.txt", small, "text/plain"))]
    resp = client.post("/v1/uploads", data={"session_id": session_id}, files=files)
    assert resp.status_code == 200, resp.text
    arr = resp.json()
    assert arr and arr[0]["filename"] == "small.txt"
    assert arr[0]["mode"] == "single" or "mode" not in arr[0]  # tolerant if normalization omitted
    assert arr[0]["path"].startswith("/v1/attachments/")
