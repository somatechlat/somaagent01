from __future__ import annotations

import math
import threading
from typing import Any, Dict, List, Tuple

try:  # optional metrics
    from prometheus_client import Counter, Gauge, Histogram
except Exception:  # pragma: no cover
    Counter = Histogram = Gauge = None  # type: ignore

if Counter and Histogram and Gauge:
    SEMANTIC_RECALL_REQUESTS = Counter(
        "semantic_recall_requests_total",
        "Semantic recall requests",
        labelnames=("result",),  # ok|disabled|error
    )
    SEMANTIC_RECALL_LATENCY = Histogram(
        "semantic_recall_request_seconds",
        "Latency of semantic recall operations",
    )
    SEMANTIC_RECALL_INDEX_SIZE = Gauge(
        "semantic_recall_index_size",
        "Current in-memory semantic recall index size",
    )
else:  # pragma: no cover

    class _Dummy:
        def labels(self, *_a, **_k):
            return self

        def inc(self, *_a, **_k):
            pass

        def set(self, *_a, **_k):
            pass

        def time(self):
            class _Ctx:
                def __enter__(self):
                    return None

                def __exit__(self, *exc):
                    return False

            return _Ctx()

        def observe(self, *_a, **_k):
            pass

    SEMANTIC_RECALL_REQUESTS = SEMANTIC_RECALL_LATENCY = SEMANTIC_RECALL_INDEX_SIZE = _Dummy()  # type: ignore

_LOCK = threading.RLock()


class SemanticRecallIndex:
    """In-memory vector index for semantic recall (prototype).

    Stores (vector, metadata) tuples and performs naive cosine similarity.
    This is a prototype; later phases should persist embeddings and move to an ANN structure.
    """

    def __init__(self, max_items: int = 10000) -> None:
        self.max_items = max_items
        self._items: List[Tuple[List[float], Dict[str, Any]]] = []

    def _cosine(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        num = sum(x * y for x, y in zip(a, b, strict=False))
        da = math.sqrt(sum(x * x for x in a))
        db = math.sqrt(sum(y * y for y in b))
        if da == 0 or db == 0:
            return 0.0
        return num / (da * db)

    def add(self, vector: List[float], metadata: Dict[str, Any]) -> None:
        if not isinstance(vector, list) or not vector:
            return
        with _LOCK:
            if len(self._items) >= self.max_items:
                # FIFO eviction for prototype simplicity
                self._items.pop(0)
            self._items.append((list(vector), dict(metadata)))
            SEMANTIC_RECALL_INDEX_SIZE.set(len(self._items))

    def recall(
        self, query_vec: List[float], k: int = 5, min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if not query_vec:
            return []
        with _LOCK:
            scored: List[Tuple[float, Dict[str, Any]]] = []
            for vec, meta in self._items:
                score = self._cosine(query_vec, vec)
                if score >= min_score:
                    scored.append((score, meta))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: List[Dict[str, Any]] = []
        for score, meta in scored[:k]:
            m = dict(meta)
            m["_score"] = round(score, 6)
            out.append(m)
        return out


# Global accessor (prototype scope)
_GLOBAL_INDEX: SemanticRecallIndex | None = None


def get_index() -> SemanticRecallIndex:
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is None:
        _GLOBAL_INDEX = SemanticRecallIndex()
    return _GLOBAL_INDEX
