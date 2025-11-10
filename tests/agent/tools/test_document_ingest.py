import httpx
import pytest

from services.tool_executor.tools import IngestDocumentTool, ToolExecutionError


class FakeResponse:
    def __init__(
        self, status_code: int = 200, headers: dict | None = None, content: bytes = b""
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        # convenience for text-like responses
        try:
            self.text = content.decode("utf-8")
        except Exception:
            self.text = ""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]


class FakeClient:
    def __init__(self, response: FakeResponse, recorder: dict | None = None, *_, **__) -> None:
        self._response = response
        self._recorder = recorder if recorder is not None else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, headers: dict | None = None):
        if self._recorder is not None:
            self._recorder["url"] = url
            self._recorder["headers"] = dict(headers or {})
        return self._response


@pytest.mark.asyncio
async def test_document_ingest_success_text_plain(monkeypatch):
    # Prepare fake response with text/plain
    content = b"hello unit-test"
    headers = {
        "content-type": "text/plain",
        "content-disposition": 'attachment; filename="tiny.txt"',
    }
    fake_resp = FakeResponse(200, headers, content)

    # Patch httpx.AsyncClient to our fake
    recorder: dict = {}
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: FakeClient(fake_resp, recorder))

    # Ensure token and base url are set
    monkeypatch.setenv("SA01_AUTH_INTERNAL_TOKEN", "test-token")
    monkeypatch.setenv("WORKER_GATEWAY_BASE", "http://gw:8010")

    tool = IngestDocumentTool()
    result = await tool.run({"attachment_id": "att-123", "metadata": {"tenant": "public"}})

    assert result["attachment_id"] == "att-123"
    assert result["filename"] == "tiny.txt"
    assert result["mime"] == "text/plain"
    assert "hello unit-test" in result["text"]

    # Verify headers include tenant and token
    assert recorder["headers"].get("X-Internal-Token") == "test-token"
    assert recorder["headers"].get("X-Tenant-Id") == "public"
    assert recorder["url"].endswith("/internal/attachments/att-123/binary")


@pytest.mark.asyncio
async def test_document_ingest_octet_stream_by_extension(monkeypatch):
    content = b"just some markdown text"
    headers = {
        "content-type": "application/octet-stream",
        "content-disposition": 'attachment; filename="file.md"',
    }
    fake_resp = FakeResponse(200, headers, content)

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: FakeClient(fake_resp))
    monkeypatch.setenv("SA01_AUTH_INTERNAL_TOKEN", "test-token")

    tool = IngestDocumentTool()
    result = await tool.run({"attachment_id": "a1"})

    assert "markdown text" in result["text"].lower()
    assert result["filename"] == "file.md"
    assert result["mime"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_document_ingest_not_found_raises(monkeypatch):
    fake_resp = FakeResponse(404, {"content-type": "text/plain"}, b"not found")
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: FakeClient(fake_resp))
    monkeypatch.setenv("SA01_AUTH_INTERNAL_TOKEN", "test-token")

    tool = IngestDocumentTool()
    with pytest.raises(ToolExecutionError) as ei:
        await tool.run({"attachment_id": "missing"})
    assert "Attachment not found" in str(ei.value)


@pytest.mark.asyncio
async def test_document_ingest_missing_attachment_id(monkeypatch):
    tool = IngestDocumentTool()
    with pytest.raises(ToolExecutionError) as ei:
        await tool.run({})
    assert "attachment_id" in str(ei.value)


@pytest.mark.asyncio
async def test_document_ingest_missing_internal_token(monkeypatch):
    # Force empty token to trigger config error
    monkeypatch.setenv("SA01_AUTH_INTERNAL_TOKEN", "")
    tool = IngestDocumentTool()
    with pytest.raises(ToolExecutionError) as ei:
        await tool.run({"attachment_id": "x"})
    assert "Internal token not configured" in str(ei.value)
