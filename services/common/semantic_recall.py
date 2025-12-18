from __future__ import annotations

import math
import threading
from typing import Any, Dict, List, Tuple

from src.core.config import cfg

# Metrics are mandatory; fail fast if prometheus_client is unavailable.
try:
    from prometheus_client import Counter, Gauge, Histogram
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "prometheus_client is required for semantic recall metrics but is not installed"
    ) from exc

# Define Prometheus metrics – these will raise if the import succeeded but the
# metric objects cannot be created for any reason, ensuring a hard failure.
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

_LOCK = threading.RLock()


class SemanticRecallIndex:
    """In-memory vector index for semantic recall.
    
    This is a PROTOTYPE implementation using naive cosine similarity and FIFO eviction.
    Production systems should use persistent vector stores (e.g., pgvector, Pinecone).
    
    Enable with: SA01_SEMANTIC_RECALL_PROTOTYPE=true (development only)
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
    """Get global semantic recall index.
    
    Raises:
        RuntimeError: If prototype is not explicitly enabled via feature flag
    """
    global _GLOBAL_INDEX
    
    # Security: Require explicit opt-in for prototype code
    prototype_enabled = cfg.env("SA01_SEMANTIC_RECALL_PROTOTYPE", "false").lower() in {"true", "1", "yes", "on"}
    if not prototype_enabled:
        raise RuntimeError(
            "Semantic recall prototype is not enabled. "
            "Set SA01_SEMANTIC_RECALL_PROTOTYPE=true to use in-memory index, "
            "or implement persistent vector store for production."
        )
    
    if _GLOBAL_INDEX is None:
        _GLOBAL_INDEX = SemanticRecallIndex()
    return _GLOBAL_INDEX
