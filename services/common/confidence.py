"""Confidence score computation for LLM generations.

Implements the normalized scalar calculation defined in SRS-CONF-2025-12-16.
No token logprobs are persisted; only the scalar is exposed to callers.
"""

from __future__ import annotations

import math
import statistics
from typing import Iterable, List, Optional


def _clean_logprobs(logprobs: Iterable[float | None]) -> List[float]:
    """Filter out invalid logprob entries."""
    cleaned: List[float] = []
    for lp in logprobs:
        if lp is None:
            continue
        try:
            val = float(lp)
        except (TypeError, ValueError):
            continue
        if math.isnan(val) or math.isinf(val):
            continue
        cleaned.append(val)
    return cleaned


def calculate_confidence(logprobs: Iterable[float | None], aggregation: str = "average") -> Optional[float]:
    """Calculate normalized confidence scalar in [0,1].

    Args:
        logprobs: Iterable of token log-probabilities (natural log).
        aggregation: One of {"average","min","percentile_90"}.

    Returns:
        float in [0,1] or None if insufficient data.
    """
    cleaned = _clean_logprobs(logprobs)
    if not cleaned:
        return None

    mode = aggregation.lower()
    if mode == "min":
        m = min(cleaned)
    elif mode in ("percentile_90", "p90", "p10_tail"):
        # Conservative: 10th percentile (lower tail)
        sorted_vals = sorted(cleaned)
        idx = max(0, int(len(sorted_vals) * 0.1) - 1)
        m = sorted_vals[idx]
    else:  # default average
        m = statistics.fmean(cleaned)

    conf = math.exp(m)
    # Clamp to [0,1]
    if conf < 0.0:
        conf = 0.0
    if conf > 1.0:
        conf = 1.0
    return conf
