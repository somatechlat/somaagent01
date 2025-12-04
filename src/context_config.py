"""Configuration helper for the Context Builder pipeline.

All values are read from environment variables so that the behaviour can be
controlled without code changes – a requirement for production deployments.
The class provides sensible defaults and validates numeric values, raising a
clear ``ValueError`` if an environment variable cannot be coerced.

This file follows the VIBE coding rules:
* No stubs or placeholders – every attribute has a concrete implementation.
* No magic numbers scattered throughout the code – defaults are defined in one
  place.
* Real error handling – invalid env vars are reported loudly.
"""

from __future__ import annotations

import os
from typing import Any


def _parse_int(name: str, default: int) -> int:
    """Parse an environment variable as ``int`` with a fallback.

    A ``ValueError`` is logged and the default is returned if parsing fails.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception as exc:  # pragma: no cover – defensive
        # In production we would log; keeping it simple to avoid extra imports.
        raise ValueError(f"Environment variable {name!r} must be an integer, got {raw!r}") from exc


def _parse_float(name: str, default: float) -> float:
    """Parse an environment variable as ``float`` with a fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception as exc:  # pragma: no cover – defensive
        raise ValueError(f"Environment variable {name!r} must be a float, got {raw!r}") from exc


class ContextBuilderConfig:
    """Centralised configuration for the context‑building pipeline.

    The attributes correspond to the knobs described in the design document:

    * ``max_tokens`` – absolute hard limit for the final prompt.
    * ``model_max_tokens`` – per‑request limit supplied by the caller.
    * ``recall_topk`` – how many candidate documents to retrieve from
      Somabrain before scoring.
    * ``use_optimal_budget`` – toggle between greedy and knapsack budgeting.
    * ``w_similarity``, ``w_salience``, ``w_recency`` – weighting factors for
      the composite score.
    * ``opa_url`` – HTTP endpoint for policy evaluation.
    * ``somabrain_base_url`` – base URL for the Somabrain service.
    * ``http_timeout_seconds`` – request timeout for external calls.
    * ``http_retries`` – number of retry attempts on transient failures.
    """

    # Token limits -----------------------------------------------------------
    max_tokens: int = _parse_int("SOMA_CONTEXT_MAX_TOKENS", 2000)
    # ``model_max_tokens`` is supplied per request; the default here mirrors the
    # historic value used throughout the codebase.
    default_model_max_tokens: int = _parse_int("SOMA_MODEL_MAX_TOKENS", 4000)

    # Retrieval settings ------------------------------------------------------
    recall_topk: int = _parse_int("SOMA_CONTEXT_RECALL_TOPK", 200)
    use_optimal_budget: bool = os.getenv("SOMA_CONTEXT_USE_OPTIMAL_BUDGET", "0") == "1"

    # Scoring weights --------------------------------------------------------
    w_similarity: float = _parse_float("SOMA_WEIGHT_SIMILARITY", 0.5)
    w_salience: float = _parse_float("SOMA_WEIGHT_SALIENCE", 0.3)
    w_recency: float = _parse_float("SOMA_WEIGHT_RECENCY", 0.2)

    # External services -------------------------------------------------------
    opa_url: str = os.getenv("OPA_URL", "http://opa:8181/v1/data/context/allow")
    somabrain_base_url: str = os.getenv(
        "SOMA_BASE_URL",
        "http://somabrain:8000",
    )
    somabrain_api_key: str = os.getenv("SOMA_API_KEY", "")

    # HTTP client behaviour ---------------------------------------------------
    http_timeout_seconds: float = _parse_float("SOMA_HTTP_TIMEOUT", 5.0)
    http_retries: int = _parse_int("SOMA_HTTP_RETRIES", 3)

    def __init__(self) -> None:
        # The class is deliberately lightweight; all values are read at
        # import time so that a single instance can be shared safely.
        pass

    # Helper properties ------------------------------------------------------
    @property
    def effective_model_max_tokens(self) -> int:
        """Return the model token limit that should be used for a request.

        Callers may override the default via the ``ContextRequest`` object;
        this property provides the fallback.
        """
        return self.default_model_max_tokens

    def __repr__(self) -> str:  # pragma: no cover – debugging aid
        fields = (
            f"max_tokens={self.max_tokens}",
            f"default_model_max_tokens={self.default_model_max_tokens}",
            f"recall_topk={self.recall_topk}",
            f"use_optimal_budget={self.use_optimal_budget}",
            f"w_similarity={self.w_similarity}",
            f"w_salience={self.w_salience}",
            f"w_recency={self.w_recency}",
            f"opa_url={self.opa_url}",
            f"somabrain_base_url={self.somabrain_base_url}",
            f"http_timeout_seconds={self.http_timeout_seconds}",
            f"http_retries={self.http_retries}",
        )
        return f"ContextBuilderConfig({', '.join(fields)})"
