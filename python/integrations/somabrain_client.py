"""SomaBrain client wrapper.

Provides thin helper functions that wrap the Somabrain HTTP API used by the
gateway and extensions. The implementation is deliberately minimal – it only
covers the capabilities required for the current roadmap phases. Additional
endpoints can be added later without breaking existing imports.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import httpx

# Re‑use the generic error class from the existing Soma client for consistency.
# Import the full async SomaClient for backward‑compatible singleton access.
from python.integrations.soma_client import (
    SomaClient as _SomaClient,
    SomaClientError,
    SomaMemoryRecord,
)

# Base URL for the Somabrain service – configurable via env var.
_BASE_URL = os.getenv("SA01_SA01_SOMA_BASE_URL") or os.getenv("SA01_SOMA_BASE_URL", "http://host.docker.internal:9696")

# ---------------------------------------------------------------------------
# Helper functions – each performs a single HTTP call and raises ``SomaClientError``
# on non‑2xx responses. The functions return JSON‑decoded Python objects.
# ---------------------------------------------------------------------------


def _request(method: str, path: str, json: Any | None = None) -> Any:
    """Internal HTTP helper.

    Args:
        method: ``"GET"``, ``"POST"`` etc.
        path: Path relative to ``_BASE_URL`` (e.g. ``"/v1/weights"``).
        json: Optional JSON payload for POST/PUT.

    Returns:
        The decoded JSON response.
    """
    url = f"{_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    try:
        resp = httpx.request(method, url, json=json, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        raise SomaClientError(str(exc)) from exc


def get_weights() -> Dict[str, Any]:
    """Retrieve the current ``RetrievalWeights`` from Somabrain.

    The endpoint is assumed to be ``GET /v1/weights`` – this mirrors the
    ``RetrievalWeights.all()`` call used in the roadmap.
    """
    return _request("GET", "/v1/weights")


def update_weights(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update learning weights.

    Args:
        payload: JSON payload describing the weight updates.
    """
    return _request("POST", "/v1/weights/update", json=payload)


def build_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ask Somabrain to build a prompt context.

    The ``data`` dict contains whatever the caller wishes to pass (e.g. the
    current datetime, temperature ``τ`` etc.). The Somabrain service is expected
    to return a dict with a ``"context"`` key.
    """
    return _request("POST", "/v1/context/build", json=data)


def get_tenant_flag(tenant_id: str, flag: str) -> bool:
    """Fetch a feature‑flag value for a specific tenant.

    Implements a thin wrapper around ``GET /v1/flags/{tenant_id}/{flag}``.
    """
    result = _request("GET", f"/v1/flags/{tenant_id}/{flag}")
    return bool(result.get("enabled"))


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
    "update_weights",
    "build_context",
    "get_tenant_flag",
]
