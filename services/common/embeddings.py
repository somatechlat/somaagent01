from __future__ import annotations

import os
import math
from services.common.embedding_cache import get_cache
from abc import ABC, abstractmethod
from typing import List, Sequence

import httpx
from prometheus_client import Counter, Histogram


EMBED_REQUESTS = Counter(
    "embeddings_requests_total",
    "Embedding requests by provider and outcome",
    labelnames=("provider", "result"),
)

EMBED_LATENCY = Histogram(
    "embeddings_request_seconds",
    "Latency of embedding requests by provider",
    labelnames=("provider",),
)


class EmbeddingsProvider(ABC):
    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Return embeddings for a list of texts."""


class OpenAIEmbeddings(EmbeddingsProvider):
    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        from services.common import runtime_config as cfg
        self.api_key = api_key or cfg.env("OPENAI_API_KEY") or ""
        self.base_url = (base_url or cfg.env("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = (model or cfg.env("EMBEDDINGS_MODEL") or "text-embedding-3-small").strip()

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        provider = "openai"
        with EMBED_LATENCY.labels(provider).time():
            try:
                if not self.api_key:
                    raise RuntimeError("OPENAI_API_KEY not set")
                if not texts:
                    return []
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {"input": list(texts), "model": self.model}
                url = f"{self.base_url}/embeddings"
                from services.common import runtime_config as cfg
                async with httpx.AsyncClient(timeout=float(cfg.env("EMBEDDINGS_TIMEOUT", "15"))) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                vecs: List[List[float]] = []
                for item in (data.get("data") or []):
                    v = item.get("embedding")
                    if isinstance(v, list):
                        vecs.append([float(x) for x in v])
                EMBED_REQUESTS.labels(provider, "ok").inc()
                return vecs
            except Exception:
                EMBED_REQUESTS.labels(provider, "error").inc()
                raise


async def maybe_embed(text: str) -> list[float] | None:
    """Optionally compute an embedding for a single text.

    Behavior:
    - If ENABLE_EMBED_ON_INGEST is not enabled, returns None (feature disabled).
    - If enabled and text is empty/whitespace, returns None.
    - If enabled but provider is misconfigured (e.g., missing key), raises error (fail-fast).
    - Respects EMBEDDINGS_MAX_CHARS limit before sending to provider.
    """
    # Centralized feature toggle via runtime_config facade (C1 migration)
    from services.common import runtime_config as cfg
    use_feature = cfg.flag("embeddings_ingest")
    if not use_feature:
        return None
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        from services.common import runtime_config as cfg
        max_chars = int(cfg.env("EMBEDDINGS_MAX_CHARS", "2000"))
    except ValueError:
        max_chars = 2000
    clipped = text if len(text) <= max_chars else text[:max_chars]
    # Check cache first
    cache = get_cache()
    cached = cache.get(clipped)
    if cached is not None:
        return cached

    # Deterministic test-mode embedding path (no network)
    if cfg.env("EMBEDDINGS_TEST_MODE", "false").lower() in {"1", "true", "yes", "on"}:
        # Produce a stable pseudo-vector from hash chunks
        import hashlib
        h = hashlib.sha256(clipped.encode("utf-8")).digest()
        # Map bytes to floats [0,1)
        vec = [round(b / 255.0, 6) for b in h[:32]]
        cache.store(clipped, vec)
        EMBED_REQUESTS.labels("test", "ok").inc()
        return vec

    provider = OpenAIEmbeddings()
    vecs = await provider.embed([clipped])
    if vecs:
        cache.store(clipped, vecs[0])
        return vecs[0]
    return None
