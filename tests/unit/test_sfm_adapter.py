"""SFM adapter wire-format tests — ARCHITECTURE-INVARIANTS §5.

Pins the exact JSON body ``SFMAdapter.remember()`` posts to
``POST /memories``, because the failure it guards against is silent:

    Putting ``embedding`` inside ``payload`` is accepted by SFM (the dict is
    free-form) and then DISCARDED — the store falls back to its hash embedder
    and ranks the record x0.25. No 4xx, no error, just recall returning noise.

So these tests assert the field PLACEMENT against the real request schema
(somafractalmemory/api/schemas.py:22 MemoryStoreRequest):

    coord: str
    payload: dict[str, Any]          # a dict, never a str
    memory_type: Literal["episodic", "semantic", "belief"]
    embedding: list[float] | None    # FIRST-CLASS, top level
    tenant_id: str | None

No network, no DB, no secrets: the HTTP client is replaced with an
httpx.MockTransport that captures the request.

Run:
    pytest tests/unit/test_sfm_adapter.py -v
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from services.common.adapters.sfm_adapter import SFMAdapter, _SFM_MEMORY_TYPE
from services.common.memory_contract import MemoryWrite


class _Capture:
    """Records the last request the adapter issued."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict[str, Any]] = []
        self.status_code = 200

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            self.bodies.append(json.loads(request.content.decode("utf-8")))
            return httpx.Response(
                self.status_code,
                json={"coord": "1.0,2.0,3.0", "memory_type": "episodic"},
            )

        return httpx.MockTransport(handler)


@pytest.fixture
def capture() -> _Capture:
    return _Capture()


@pytest.fixture
def adapter(capture: _Capture) -> SFMAdapter:
    return SFMAdapter("http://sfm.test", token="test-token")


@pytest.fixture
def write() -> MemoryWrite:
    return MemoryWrite(
        text="the agent remembered the deployment window",
        kind="episodic",
        tenant_id="tenant-001",
        session_id="session-001",
        coord="0.1,0.2,0.3",
        embedding=[0.0, 0.0, 1.0, 0.0],
        salience=0.9,
        source="agent-chat",
    )


# ---------------------------------------------------------------------------
# The regression that shipped: embedding placement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embedding_is_a_top_level_field(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite
) -> None:
    """``embedding`` must sit next to ``coord``/``payload``, not inside ``payload``."""

    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )
    await adapter.remember(write)

    assert len(capture.bodies) == 1
    body = capture.bodies[0]

    assert "embedding" in body, (
        "embedding missing from the request body — SFM will hash-embed and "
        "rank the record x0.25"
    )
    assert body["embedding"] == write.embedding

    # And critically: NOT nested where SFM silently ignores it.
    assert "embedding" not in body["payload"], (
        "embedding must not be nested in payload — SFM's free-form payload "
        "dict accepts it and then discards it"
    )


@pytest.mark.asyncio
async def test_payload_is_a_dict_not_a_string(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite
) -> None:
    """SFM's ``payload`` is ``dict[str, Any]``; a string is a 422."""

    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )
    await adapter.remember(write)

    payload = capture.bodies[0]["payload"]
    assert isinstance(payload, dict)
    assert payload["text"] == write.text


@pytest.mark.asyncio
async def test_request_matches_memory_store_request_shape(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite
) -> None:
    """Top-level keys are exactly MemoryStoreRequest's fields — nothing else."""

    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )
    await adapter.remember(write)

    body = capture.bodies[0]
    assert set(body) == {"coord", "payload", "memory_type", "embedding", "tenant_id"}
    assert body["coord"] == write.coord
    assert body["tenant_id"] == write.tenant_id
    assert body["memory_type"] == "episodic"


@pytest.mark.asyncio
async def test_metadata_rides_inside_payload(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite
) -> None:
    """Fields with no SFM column live in ``payload`` — and nothing is lost."""

    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )
    await adapter.remember(write)

    payload = capture.bodies[0]["payload"]
    for key in ("text", "kind", "source", "salience", "created_at", "session_id"):
        assert key in payload, f"payload lost {key!r}"
    assert payload["source"] == write.source
    assert payload["salience"] == write.salience
    assert payload["session_id"] == write.session_id


# ---------------------------------------------------------------------------
# memory_type mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["episodic", "semantic", "belief"])
@pytest.mark.asyncio
async def test_every_contract_kind_is_accepted_verbatim(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite, kind: str
) -> None:
    """All three contract kinds pass through — the schema has them all."""

    write.kind = kind  # type: ignore[assignment]
    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )
    await adapter.remember(write)

    assert capture.bodies[0]["memory_type"] == kind
    assert _SFM_MEMORY_TYPE[kind] == kind


# ---------------------------------------------------------------------------
# Fail-closed / never-raise contract
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remember_never_raises_on_http_error(
    adapter: SFMAdapter, capture: _Capture, write: MemoryWrite
) -> None:
    """A failed store produces ``MemoryAck(ok=False)`` — it does not throw."""

    capture.status_code = 500
    adapter._client = httpx.AsyncClient(
        base_url="http://sfm.test", transport=capture.transport()
    )

    ack = await adapter.remember(write)

    assert ack.ok is False
    assert ack.store == "somafractalmemory"
    assert ack.coord == write.coord
    assert ack.error


@pytest.mark.asyncio
async def test_missing_url_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """No URL in settings and no env → MemoryConfigurationError, never a localhost guess."""

    import os

    from config import settings as django_settings
    from services.common.memory_contract import MemoryConfigurationError

    # settings is the authority (get_memory_setting), so both layers must be
    # empty for this to prove fail-closed rather than prove the setting is read.
    for key in ("SOMAFRACTALMEMORY_URL", "SFM_URL"):
        monkeypatch.setattr(django_settings, key, None, raising=False)
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(MemoryConfigurationError):
        SFMAdapter(None)
