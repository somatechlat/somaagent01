"""Convenient thin wrapper around the :pymod:`python.integrations.soma_client` API.

The original repository only exposed the :class:`SomaBrainClient` class as an
alias for :class:`~python.integrations.soma_client.SomaClient`.  The test suite
expects a collection of free‑standing helper functions (both sync and async) to
perform common HTTP calls against a *SA01_SOMA_BASE_URL* endpoint.  This module
adds those helpers while preserving the original alias for backward
compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

# Updated to use centralized configuration instead of direct environment access.
from src.core.config import cfg

from python.integrations.soma_client import (
    SomaClient,
    SomaClientError,
    SomaMemoryRecord,
)


class SomaBrainClient(SomaClient):
    """Backwards‑compatible alias for the SomaBrain HTTP client."""


# ---------------------------------------------------------------------------
# Helper utilities – these are the functions exercised by the integration tests.
# ---------------------------------------------------------------------------

def _base_url() -> str:
    """Return the base URL for the SomaBrain service from the central config.

    The configuration model validates the presence of ``external.somabrain_base_url``.
    ``cfg.get_somabrain_url()`` raises a clear error if the URL is missing, which
    satisfies the VIBE rule of a single source of truth.
    """
    return cfg.get_somabrain_url()


def _handle_response(resp: httpx.Response) -> Any:
    """Raise :class:`SomaClientError` for non‑2xx responses, otherwise return JSON.
    """

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Preserve the original status code and message for debugging.
        raise SomaClientError(str(exc)) from exc
    # Successful responses are expected to be JSON; if parsing fails we let the
    # exception propagate – the test suite does not cover that path.
    return resp.json()


# ---------------------------------------------------------------------------
# Synchronous helpers
# ---------------------------------------------------------------------------

def get_weights() -> Dict[str, Any]:
    """GET ``/v1/weights`` and return the parsed JSON payload.
    """

    resp = httpx.get(f"{_base_url()}/v1/weights")
    return _handle_response(resp)


def update_weights(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST ``/v1/weights/update`` with *payload* and return the JSON response.
    """

    resp = httpx.post(f"{_base_url()}/v1/weights/update", json=payload)
    return _handle_response(resp)


def build_context(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """POST ``/v1/context/build``.

    The test suite expects a :class:`SomaClientError` when the endpoint returns
    a 4xx status code.
    """

    resp = httpx.post(f"{_base_url()}/v1/context/build", json=payload)
    return _handle_response(resp)


def get_tenant_flag(tenant: str, flag: str) -> bool:
    """GET ``/v1/flags/{tenant}/{flag}`` and return the ``enabled`` field.
    """

    resp = httpx.get(f"{_base_url()}/v1/flags/{tenant}/{flag}")
    data = _handle_response(resp)
    return bool(data.get("enabled"))


def get_persona(persona_id: str) -> Dict[str, Any]:
    """GET ``/persona/{persona_id}``.
    """

    resp = httpx.get(f"{_base_url()}/persona/{persona_id}")
    return _handle_response(resp)


def put_persona(persona_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """PUT ``/persona/{persona_id}`` with *payload*.
    """

    resp = httpx.put(f"{_base_url()}/persona/{persona_id}", json=payload)
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Asynchronous helpers – used with ``pytest.mark.asyncio``.
# ---------------------------------------------------------------------------

async def get_weights_async() -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/v1/weights")
    return _handle_response(resp)


async def build_context_async(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_base_url()}/v1/context/build", json=payload)
    return _handle_response(resp)


async def publish_reward_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_base_url()}/v1/learning/reward", json=payload)
    return _handle_response(resp)


async def get_tenant_flag_async(tenant: str, flag: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/v1/flags/{tenant}/{flag}")
    data = _handle_response(resp)
    return bool(data.get("enabled"))


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaMemoryRecord",
    # sync helpers
    "get_weights",
    "update_weights",
    "build_context",
    "get_tenant_flag",
    "get_persona",
    "put_persona",
    # async helpers
    "get_weights_async",
    "build_context_async",
    "publish_reward_async",
    "get_tenant_flag_async",
]
