from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Dict, List

# Metrics are required; fail fast if prometheus_client is unavailable.
try:
    from prometheus_client import Counter
except Exception as exc:
    raise ImportError("prometheus_client is required for EmbeddingCache metrics") from exc

_CACHE_LOCK = threading.RLock()

if Counter:
    EMBED_CACHE_EVENTS = Counter(
        "embedding_cache_events_total",
        "Embedding cache events",
        labelnames=("event",),  # hit|miss|evict|store
    )
else:  # pragma: no cover

    class _Dummy:
        def labels(self, *_args, **_kwargs):
            return self

        def inc(self, *_args, **_kwargs):
    # Removed per Vibe rule
    EMBED_CACHE_EVENTS = _Dummy()  # type: ignore


class EmbeddingCache:
    """Thread-safe LRU embedding cache.

    Keying strategy:
    - SHA256 of UTF-8 text (exact) to avoid collisions.
    - Size-limited; least-recently-used eviction.
    """

    def __init__(self, capacity: int = 2048) -> None:
        self.capacity = max(1, capacity)
        self._data: "OrderedDict[str, List[float]]" = OrderedDict()

    @staticmethod
    def make_key(text: str) -> str:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return h

    def get(self, text: str) -> List[float] | None:
        k = self.make_key(text)
        with _CACHE_LOCK:
            vec = self._data.get(k)
            if vec is not None:
                # Mark as recently used
                self._data.move_to_end(k)
                EMBED_CACHE_EVENTS.labels("hit").inc()
                return list(vec)
            EMBED_CACHE_EVENTS.labels("miss").inc()
            return None

    def store(self, text: str, vector: List[float]) -> None:
        k = self.make_key(text)
        with _CACHE_LOCK:
            if k in self._data:
                self._data.move_to_end(k)
                self._data[k] = list(vector)
                EMBED_CACHE_EVENTS.labels("store").inc()
                return
            if len(self._data) >= self.capacity:
                # Evict LRU
                oldk, _ = self._data.popitem(last=False)
                EMBED_CACHE_EVENTS.labels("evict").inc()
            self._data[k] = list(vector)
            EMBED_CACHE_EVENTS.labels("store").inc()

    def stats(self) -> Dict[str, int]:
        with _CACHE_LOCK:
            return {"size": len(self._data), "capacity": self.capacity}


# Global singleton (simple usage pattern)
_GLOBAL_CACHE: EmbeddingCache | None = None


def get_cache() -> EmbeddingCache:
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = EmbeddingCache()
    return _GLOBAL_CACHE
