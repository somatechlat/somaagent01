import pytest

from services.common.embeddings import maybe_embed
from src.core.config import cfg

pytestmark = pytest.mark.asyncio


async def test_maybe_embed_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("SA01_ENABLE_EMBEDDINGS_INGEST", "false")
    # Reset runtime config so feature flags reflect env override
    cfg.init_runtime_config()
    assert await maybe_embed("hello") is None


async def test_maybe_embed_enabled_missing_key_raises(monkeypatch):
    monkeypatch.setenv("SA01_ENABLE_EMBEDDINGS_INGEST", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Reset runtime config to pick up flag change
    cfg.init_runtime_config()
    with pytest.raises(RuntimeError):
        await maybe_embed("hello")
