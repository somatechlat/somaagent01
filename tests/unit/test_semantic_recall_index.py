import os
import pytest

from services.common.semantic_recall import get_index
from services.common.embeddings import maybe_embed

pytestmark = pytest.mark.asyncio

async def test_semantic_recall_basic(monkeypatch):
    monkeypatch.setenv("ENABLE_EMBED_ON_INGEST", "true")
    monkeypatch.setenv("EMBEDDINGS_TEST_MODE", "true")
    monkeypatch.setenv("SA01_FEATURE_PROFILE", "max")  # ensure semantic_recall enabled by profile
    # Build index manually (feature gating tested separately)
    idx = get_index()
    # Clear any previous items
    idx._items.clear()  # type: ignore
    base_texts = ["alpha", "beta", "gamma", "alphabet", "betamax"]
    for t in base_texts:
        vec = await maybe_embed(t)
        assert vec is not None
        idx.add(vec, {"text": t})
    qvec = await maybe_embed("alpha")
    assert qvec is not None
    results = idx.recall(qvec, k=3)
    assert results
    # Expect 'alpha' or 'alphabet' near top
    top_texts = {r["text"] for r in results}
    assert "alpha" in top_texts

async def test_semantic_recall_endpoint_disabled(monkeypatch):
    from services.common.features import build_default_registry
    # Force profile minimal disabling semantic_recall
    monkeypatch.setenv("SA01_FEATURE_PROFILE", "minimal")
    reg = build_default_registry()
    assert not reg.is_enabled("semantic_recall")
