import os
import pytest

from services.common.embedding_cache import EmbeddingCache
from services.common.embeddings import maybe_embed

pytestmark = pytest.mark.asyncio

async def test_embedding_cache_basic(monkeypatch):
    monkeypatch.setenv("ENABLE_EMBED_ON_INGEST", "true")
    monkeypatch.setenv("EMBEDDINGS_TEST_MODE", "true")
    # First call populates cache
    v1 = await maybe_embed("hello world")
    v2 = await maybe_embed("hello world")
    assert v1 == v2
    assert isinstance(v1, list) and len(v1) > 8

async def test_embedding_cache_eviction(monkeypatch):
    monkeypatch.setenv("ENABLE_EMBED_ON_INGEST", "true")
    monkeypatch.setenv("EMBEDDINGS_TEST_MODE", "true")
    cache = EmbeddingCache(capacity=3)
    texts = ["t1", "t2", "t3", "t4"]
    for t in texts:
        v = await maybe_embed(t)
        cache.store(t, v or [])
    stats = cache.stats()
    assert stats["size"] == 3
    assert stats["capacity"] == 3
