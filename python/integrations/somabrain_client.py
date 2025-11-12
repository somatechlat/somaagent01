"""SomaBrain client wrapper.

Provides thin helper functions that wrap the Somabrain HTTP API used by the
gateway and extensions. The implementation is deliberately minimal – it only
covers the capabilities required for the current roadmap phases. Additional
endpoints can be added later without breaking existing imports.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
from prometheus_client import Counter, Histogram

from services.common import runtime_config as cfg

# Re‑use the generic error class from the existing Soma client for consistency.
# Import the full async SomaClient for backward‑compatible singleton access.
from python.integrations.soma_client import (
    SomaClient as _SomaClient,
    SomaClientError,
    SomaMemoryRecord,
)

# Base URL for the Somabrain service – configurable via env var.


def _base_url() -> str:
    try:
        raw = cfg.soma_base_url()
    except Exception:
        raw = None
    return (raw or "http://host.docker.internal:9696").rstrip("/")


_REQUEST_TIMEOUT_SECONDS = float(cfg.env("SA01_SOMABRAIN_TIMEOUT_SECONDS", "10") or "10")

_CLIENT_REQUESTS_TOTAL = Counter(
    "somabrain_client_http_requests_total",
    "Somabrain client HTTP requests",
    labelnames=("method", "path", "result"),
)
_CLIENT_REQUEST_LATENCY_SECONDS = Histogram(
    "somabrain_client_http_request_seconds",
    "Somabrain client HTTP request latency",
    labelnames=("method", "path"),
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)

# ---------------------------------------------------------------------------
# Helper functions – each performs a single HTTP call and raises ``SomaClientError``
# on non‑2xx responses. The functions return JSON‑decoded Python objects.
# ---------------------------------------------------------------------------


def _record_metrics(method: str, path: str, result: str, duration: float) -> None:
    try:
        _CLIENT_REQUESTS_TOTAL.labels(method=method, path=path, result=result).inc()
        _CLIENT_REQUEST_LATENCY_SECONDS.labels(method=method, path=path).observe(duration)
    except Exception:
        pass


def _request(
    method: str,
    path: str,
    *,
    json: Any | None = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Any:
    """Internal HTTP helper.

    Args:
        method: ``"GET"``, ``"POST"`` etc.
        path: Path relative to ``_BASE_URL`` (e.g. ``"/v1/weights"``).
        json: Optional JSON payload for POST/PUT.

    Returns:
        The decoded JSON response.
    """
    url = f"{_base_url()}/{path.lstrip('/')}"
    start = time.perf_counter()
    try:
        resp = httpx.request(method, url, json=json, params=params, timeout=timeout or _REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        _record_metrics(method, path, str(resp.status_code), time.perf_counter() - start)
        return data
    except httpx.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", "error")
        _record_metrics(method, path, str(status), time.perf_counter() - start)
        raise SomaClientError(str(exc)) from exc


async def _arequest(
    method: str,
    path: str,
    *,
    json: Any | None = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Any:
    url = f"{_base_url()}/{path.lstrip('/')}"
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout or _REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.request(method, url, json=json, params=params)
        resp.raise_for_status()
        data = resp.json()
        _record_metrics(method, path, str(resp.status_code), time.perf_counter() - start)
        return data
    except httpx.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", "error")
        _record_metrics(method, path, str(status), time.perf_counter() - start)
        raise SomaClientError(str(exc)) from exc


def get_weights() -> Dict[str, Any]:
    """Retrieve the current ``RetrievalWeights`` from Somabrain.

    The endpoint is assumed to be ``GET /v1/weights`` – this mirrors the
    ``RetrievalWeights.all()`` call used in the roadmap.
    """
    return _request("GET", "/v1/weights")


async def get_weights_async(persona_id: Optional[str] = None) -> Dict[str, Any]:
    params = {"persona": persona_id} if persona_id else None
    return await _arequest("GET", "/v1/weights", params=params)


def update_weights(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update learning weights.

    Args:
        payload: JSON payload describing the weight updates.
    """
    return _request("POST", "/v1/weights/update", json=payload)


async def update_weights_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _arequest("POST", "/v1/weights/update", json=payload)


def build_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ask Somabrain to build a prompt context.

    The ``data`` dict contains whatever the caller wishes to pass (e.g. the
    current datetime, temperature ``τ`` etc.). The Somabrain service is expected
    to return a dict with a ``"context"`` key.
    """
    return _request("POST", "/v1/context/build", json=data)


async def build_context_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _arequest("POST", "/v1/context/build", json=payload)


def get_tenant_flag(tenant_id: str, flag: str) -> bool:
    """Fetch a feature‑flag value for a specific tenant.

    Implements a thin wrapper around ``GET /v1/flags/{tenant_id}/{flag}``.
    """
    result = _request("GET", f"/v1/flags/{tenant_id}/{flag}")
    return bool(result.get("enabled"))


async def get_tenant_flag_async(tenant_id: str, flag: str) -> bool:
    result = await _arequest("GET", f"/v1/flags/{tenant_id}/{flag}")
    return bool(result.get("enabled"))


async def publish_reward_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _arequest("POST", "/v1/learning/reward", json=payload)


def get_persona(persona_id: str) -> Dict[str, Any]:
    """Fetch a persona record from Somabrain.

    Args:
        persona_id: Identifier of the persona to retrieve.

    Returns:
        Persona JSON document (dict). Raises ``SomaClientError`` on failure.
    """

    if not persona_id:
        raise SomaClientError("persona_id is required")
    return _request("GET", f"/persona/{persona_id}")


def put_persona(persona_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a persona record in Somabrain."""

    if not persona_id:
        raise SomaClientError("persona_id is required")
    body = dict(payload)
    body.setdefault("id", persona_id)
    return _request("PUT", f"/persona/{persona_id}", json=body)


# Provide a lightweight alias for backward compatibility. Existing code
# expects ``SomaBrainClient.get()`` to return a ``SomaClient`` singleton.
# The async ``SomaClient`` already implements ``get()``, so we expose the same
# class under the historic name.

SomaBrainClient = _SomaClient  # type: ignore
SomaClient = _SomaClient

__all__ = [
    "SomaClientError",
    "SomaBrainClient",
    "SomaClient",
    "SomaMemoryRecord",
    "get_weights",
    "get_weights_async",
    "update_weights",
    "update_weights_async",
    "build_context",
    "build_context_async",
    "get_tenant_flag",
    "get_tenant_flag_async",
    "publish_reward_async",
    "get_persona",
    "put_persona",
]
