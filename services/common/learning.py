"""Learning & context integration (Sprint L2).

Provides lightweight adapters to Somabrain endpoints for:
 - Fetching current model/provider weights (`get_weights`).
 - Building contextual augmentation for a conversation (`build_context`).
 - Publishing reward/feedback signals (`publish_reward`).

All network interactions are best-effort: failures degrade to empty structures
without raising so the main chat flow remains resilient.

Metrics emitted via Prometheus counters/histograms defined here to avoid
gateway tight coupling. The gateway or workers can import and call functions.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx
from prometheus_client import Counter, Histogram

from python.integrations.somabrain_client import SomaClientError
from src.core.config import cfg

LEARNING_REQUESTS_TOTAL = Counter(
    "learning_requests_total",
    "Learning & context request count",
    labelnames=("endpoint", "result"),
)
LEARNING_REQUEST_LATENCY_SECONDS = Histogram(
    "learning_request_latency_seconds",
    "Latency of learning/context requests",
    labelnames=("endpoint",),
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)
LEARNING_REWARD_TOTAL = Counter(
    "learning_reward_publish_total",
    "Published reward/feedback signals",
    labelnames=("result",),
)
async def get_weights(persona_id: Optional[str] = None) -> Dict[str, Any]:
    if not cfg.flag("learning_context"):
        return {}
    endpoint = "weights"
    t0 = time.perf_counter()
    try:
        # Direct HTTP call to Somabrain weights endpoint. Tests monkey‑patch
        # ``l.httpx.AsyncClient`` to provide a fake response, so we use the
        # ``httpx`` module imported above.
        # Use explicit timeout to accommodate test monkey‑patches that expect a
        # positional argument. The default timeout of 30 seconds mirrors the
        # previous behaviour of ``httpx.AsyncClient()`` (which uses a default
        # fixture that defines ``AsyncClient=lambda timeout: _Client()``.
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{cfg.soma_base_url()}/v1/weights"
            params = {"persona": persona_id} if persona_id else None
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        LEARNING_REQUESTS_TOTAL.labels(endpoint, "ok").inc()
        LEARNING_REQUEST_LATENCY_SECONDS.labels(endpoint).observe(time.perf_counter() - t0)
        return data if isinstance(data, dict) else {}
    except (SomaClientError, httpx.HTTPError) as exc:
        # Log the error clearly and return empty dict - no stub fallbacks allowed
        LEARNING_REQUESTS_TOTAL.labels(endpoint, "error").inc()
        LEARNING_REQUEST_LATENCY_SECONDS.labels(endpoint).observe(time.perf_counter() - t0)
        LOGGER.error("Learning service request failed", extra={"endpoint": endpoint, "error": str(exc)})
        return {}


async def build_context(session_id: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return additional contextual messages to prepend/append.

    Expects Somabrain to return a list of message objects with 'role' and 'content'.
    """
    if not cfg.flag("learning_context"):
        return []
    endpoint = "context"
    t0 = time.perf_counter()
    try:
        payload = {"session_id": session_id, "messages": messages[-10:]}
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{cfg.soma_base_url()}/v1/context/build"
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        LEARNING_REQUESTS_TOTAL.labels(endpoint, "ok").inc()
        LEARNING_REQUEST_LATENCY_SECONDS.labels(endpoint).observe(time.perf_counter() - t0)
        if isinstance(data, list):
            norm: List[Dict[str, Any]] = []
            for d in data:
                if isinstance(d, dict) and "role" in d and "content" in d:
                    norm.append({"role": d["role"], "content": str(d["content"])})
            return norm
        return []
    except (SomaClientError, httpx.HTTPError):
        LEARNING_REQUESTS_TOTAL.labels(endpoint, "error").inc()
        LEARNING_REQUEST_LATENCY_SECONDS.labels(endpoint).observe(time.perf_counter() - t0)
        return []


async def publish_reward(
    session_id: str, signal: str, value: float, meta: Optional[Dict[str, Any]] = None
) -> bool:
    if not cfg.flag("learning_context"):
        return False
    endpoint = "reward"
    try:
        payload = {"session_id": session_id, "signal": signal, "value": value, "meta": meta or {}}
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{cfg.soma_base_url()}/v1/learning/reward"
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        LEARNING_REWARD_TOTAL.labels("ok").inc()
        return True
    except SomaClientError:
        LEARNING_REWARD_TOTAL.labels("error").inc()
        return False
