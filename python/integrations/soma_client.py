"""HTTP client for interacting with the SomaBrain cognitive memory service.

This module provides a thin asynchronous wrapper around the SomaBrain REST API
endpoints that Agent Zero needs in order to offload long-term memory
operations.  It focuses on the high-level primitives used throughout the
codebase – creating memories, recalling them, deleting memories by coordinate
and exporting the current memory state.

The implementation is intentionally defensive.  The SomaBrain deployment used
in development environments can differ slightly in the exact headers it
expects, so the client reads configuration from environment variables with
sensible defaults and exposes helpers for common headers and payload shapes.

Environment variables:

* ``SOMA_BASE_URL``: Base URL of the SomaBrain API.  Defaults to
    ``http://localhost:9696`` which matches the local development cluster.
* ``SOMA_API_KEY``: Optional API key.  When provided the client sends it in an
  ``Authorization: Bearer`` header (or a custom header if
  ``SOMA_AUTH_HEADER`` is supplied).
* ``SOMA_TENANT_ID``: Optional tenant identifier forwarded via
  ``X-Tenant-ID`` (or a custom header defined by ``SOMA_TENANT_HEADER``).
* ``SOMA_NAMESPACE``: Optional logical namespace value.  When set it is added
  to outgoing request bodies under the ``universe`` key so that requests are
  automatically segmented per Agent Zero memory sub-directory.
* ``SOMA_TIMEOUT_SECONDS``: Optional request timeout (float seconds).  Defaults
  to 30 seconds which is generous enough for bulk exports.
* ``SOMA_VERIFY_SSL``: Toggle TLS certificate verification (``true``/``false``).

The client keeps a single ``httpx.AsyncClient`` instance per process to reuse
connections.  Callers should obtain the singleton through ``SomaClient.get()``
instead of instantiating the class directly.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

import httpx


logger = logging.getLogger(__name__)


def _sanitize_legacy_base_url(raw_base_url: str) -> str:
    """Sanitize the provided base URL.

    The function now only ensures a non‑empty, well‑formed URL and rewrites
    the legacy port ``9595`` to the current default ``9696``. All references
    to the old ``somafractalmemory`` host markers have been removed.
    """
    candidate = (raw_base_url or "").strip()
    if not candidate:
        return "http://localhost:9696"

    normalized = candidate.rstrip("/")

    try:
        url = httpx.URL(normalized)
    except Exception:
        logger.warning("Invalid SOMA_BASE_URL %s; falling back to localhost:9696", candidate)
        return "http://localhost:9696"

    port = url.port
    scheme = url.scheme or "http"

    # Rewrite only the legacy port 9595 to the current default.
    if port == 9595:
        override = httpx.URL(f"{scheme}://localhost:9696")
        logger.warning(
            "Detected legacy SomaBrain endpoint %s; redirecting to %s",
            normalized,
            override,
        )
        return str(override)

    return normalized


def _default_base_url() -> str:
    """Return the base URL for SomaBrain.

    The environment variable ``SOMA_BASE_URL`` can be used to point to a custom
    endpoint. If it is not set we default to ``http://localhost:9696``. The
    function no longer performs any legacy‑host sanitisation – that logic lives
    in ``_sanitize_legacy_base_url`` and is only applied when an explicit URL
    is provided.
    """
    return os.getenv("SOMA_BASE_URL", "http://localhost:9696")


DEFAULT_BASE_URL = _default_base_url()
DEFAULT_TIMEOUT = float(os.environ.get("SOMA_TIMEOUT_SECONDS", "30"))
DEFAULT_NAMESPACE = os.environ.get("SOMA_NAMESPACE")

TENANT_HEADER = os.environ.get("SOMA_TENANT_HEADER", "X-Tenant-ID")
AUTH_HEADER = os.environ.get("SOMA_AUTH_HEADER", "Authorization")


def _truthy_env(var_name: str) -> bool:
    value = os.environ.get(var_name)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _running_inside_container() -> bool:
    if _truthy_env("SOMA_FORCE_CONTAINER"):
        return True
    if _truthy_env("SOMA_DISABLE_CONTAINER_CHECK"):
        return False

    if os.path.exists("/.dockerenv"):
        return True

    try:
        with open("/proc/self/cgroup", "r", encoding="utf-8", errors="ignore") as stream:
            contents = stream.read()
        if any(token in contents for token in ("docker", "kubepods", "containerd")):
            return True
    except FileNotFoundError:
        pass

    return False


def _normalize_base_url(raw_base_url: str) -> str:
    base_url = raw_base_url.rstrip("/")

    try:
        url = httpx.URL(base_url)
    except Exception:
        return base_url

    host = url.host
    if host in {"localhost", "127.0.0.1"} and _running_inside_container():
        override_host = os.environ.get("SOMA_CONTAINER_HOST_ALIAS", "host.docker.internal")
        if override_host:
            candidate = url.copy_with(host=override_host)
            adapted = str(candidate).rstrip("/")
            if adapted != base_url:
                logger.debug(
                    "SomaClient remapped base URL from %s to %s to reach host SomaBrain from container",
                    base_url,
                    adapted,
                )
            return adapted

    return base_url


class SomaClientError(RuntimeError):
    """Raised when the SomaBrain service returns an unexpected error."""


def _boolean(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    return value.lower() in {"1", "true", "yes"}


@dataclass(slots=True)
class SomaMemoryRecord:
    """Represents a memory item returned by SomaBrain."""

    identifier: str
    payload: Mapping[str, Any]
    score: Optional[float] = None
    coordinate: Optional[List[float]] = None
    retriever: Optional[str] = None


class SomaClient:
    """Singleton HTTP client for SomaBrain endpoints."""

    _instance: "SomaClient | None" = None

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        namespace: Optional[str] = DEFAULT_NAMESPACE,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: Optional[bool] = None,
    ) -> None:
        print(
            "[SomaClient.__init__] initializing",
            {
                "provided_base_url": base_url,
                "env_base_url": os.environ.get("SOMA_BASE_URL"),
            },
        )
        sanitized_base_url = _sanitize_legacy_base_url(base_url)
        self.base_url = _normalize_base_url(sanitized_base_url)
        self.namespace = namespace
        self._tenant_id = tenant_id or os.environ.get("SOMA_TENANT_ID")
        self._api_key = api_key or os.environ.get("SOMA_API_KEY")
        verify_override = _boolean(os.environ.get("SOMA_VERIFY_SSL"))
        if verify_ssl is None and verify_override is not None:
            verify_ssl = verify_override

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=self._build_default_headers(),
            verify=verify_ssl if verify_ssl is not None else True,
        )
        self._lock = asyncio.Lock()

    @classmethod
    def get(cls) -> "SomaClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def close(self) -> None:
        await self._client.aclose()

    def _build_default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self._api_key:
            headers[AUTH_HEADER] = f"Bearer {self._api_key}" if AUTH_HEADER.lower() == "authorization" else self._api_key
        if self._tenant_id:
            headers[TENANT_HEADER] = self._tenant_id
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        allow_404: bool = False,
    ) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        request_headers: Dict[str, str] = {}
        if headers:
            request_headers.update(headers)

        print(
            "[SomaClient] preparing",
            {
                "method": method,
                "path": url,
                "base_url": self.base_url,
                "env_base_url": os.environ.get("SOMA_BASE_URL"),
                "headers": request_headers or None,
            },
        )

        async with self._lock:
            response = await self._client.request(method, url, json=json, headers=request_headers or None)

        print(
            "[SomaClient] response",
            {
                "method": method,
                "path": url,
                "status_code": response.status_code,
            },
        )

        if allow_404 and response.status_code == 404:
            return None

        if response.status_code >= 400:
            detail: Optional[str]
            try:
                detail = response.json().get("detail")  # type: ignore[assignment]
            except Exception:
                detail = response.text or None
            raise SomaClientError(
                f"SomaBrain request {method} {url} failed: {response.status_code} {detail or response.text}"
            )
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    # ------------------------------------------------------------------
    # High-level endpoints
    # ------------------------------------------------------------------

    async def remember(
        self,
        payload: Mapping[str, Any],
        *,
        coord: Optional[str] = None,
        universe: Optional[str] = None,
    ) -> Mapping[str, Any]:
        body: Dict[str, Any] = {"payload": dict(payload)}
        if coord:
            body["coord"] = coord
        if universe or self.namespace:
            resolved_universe = universe or self.namespace
            body["universe"] = resolved_universe
            body.setdefault("payload", {})
            body["payload"]["universe"] = resolved_universe
        return await self._request("POST", "/remember", json=body)

    async def recall(
        self,
        query: str,
        *,
        top_k: int = 3,
        universe: Optional[str] = None,
    ) -> Mapping[str, Any]:
        body: Dict[str, Any] = {"query": query, "top_k": top_k}
        if universe or self.namespace:
            body["universe"] = universe or self.namespace
        return await self._request("POST", "/recall", json=body)

    async def delete(self, coordinate: Iterable[float]) -> Mapping[str, Any]:
        body = {"coordinate": list(coordinate)}
        return await self._request("POST", "/delete", json=body)

    async def migrate_export(
        self,
        *,
        include_wm: bool = True,
        wm_limit: int = 128,
    ) -> Mapping[str, Any]:
        body = {"include_wm": include_wm, "wm_limit": wm_limit}
        return await self._request("POST", "/migrate/export", json=body)

    async def migrate_import(
        self,
        manifest: Mapping[str, Any],
        memories: Iterable[Mapping[str, Any]],
        *,
        wm: Optional[Iterable[Mapping[str, Any]]] = None,
        replace: bool = False,
    ) -> Mapping[str, Any]:
        body: MutableMapping[str, Any] = {
            "manifest": dict(manifest),
            "memories": [dict(memory) for memory in memories],
            "replace": replace,
        }
        if wm is not None:
            body["wm"] = [dict(entry) for entry in wm]
        return await self._request("POST", "/migrate/import", json=body)

    async def health(self) -> Mapping[str, Any]:
        return await self._request("GET", "/health")


__all__ = [
    "SomaClient",
    "SomaClientError",
    "SomaMemoryRecord",
]
