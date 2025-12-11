import pytest

from services.common.embeddings import maybe_embed
from src.core.config import cfg, reload_config

pytestmark = pytest.mark.asyncio


async def test_maybe_embed_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("SA01_ENABLE_EMBEDDINGS_INGEST", "false")
    
    # Force reload config and clear cache
    from src.core.config.loader import _cached_config
    _cached_config = None
    
    # Directly set the feature flag in config
    from src.core.config.registry import get_config_registry
    registry = get_config_registry()
    config = registry._current_config
    if config:
        config.feature_flags['embeddings_ingest'] = False
    
    assert await maybe_embed("hello") is None


async def test_maybe_embed_enabled_missing_key_raises(monkeypatch):
    monkeypatch.setenv("SA01_ENABLE_EMBEDDINGS_INGEST", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Force reload config and clear cache
    from src.core.config.loader import _cached_config
    _cached_config = None
    
    # Directly set the feature flag in config
    from src.core.config.registry import get_config_registry
    registry = get_config_registry()
    config = registry._current_config
    if config:
        config.feature_flags['embeddings_ingest'] = True
    
    with pytest.raises(RuntimeError):
        await maybe_embed("hello")
