import os
import pytest

from services.common.embeddings import maybe_embed


pytestmark = pytest.mark.asyncio


async def test_maybe_embed_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("ENABLE_EMBED_ON_INGEST", "false")
    assert await maybe_embed("hello") is None


async def test_maybe_embed_enabled_missing_key_raises(monkeypatch):
    monkeypatch.setenv("ENABLE_EMBED_ON_INGEST", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        await maybe_embed("hello")
