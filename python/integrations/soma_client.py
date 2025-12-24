"""HTTP client for interacting with the SomaBrain cognitive memory service.

This module provides a thin asynchronous wrapper around the SomaBrain REST API
endpoints that Agent Zero needs in order to offload long-term memory
operations.  It focuses on the high-level primitives used throughout the
codebase – creating memories, recalling them, deleting memories by coordinate
and exporting the current memory state.

The implementation is intentionally defensive.  The SomaBrain deployment used
in development environments can differ slightly in the exact headers it
expects, so the client reads configuration via the canonical ``cfg`` facade
and exposes helpers for common headers and payload shapes.

Environment variables (all use SA01_ prefix per VIBE rules):

* ``SA01_SOMA_BASE_URL``: Base URL of the SomaBrain API (REQUIRED).
* ``SA01_SOMA_API_KEY``: Optional API key for Bearer authentication.
* ``SA01_TENANT_ID``: Optional tenant identifier forwarded via X-Tenant-ID.
* ``SA01_NAMESPACE``: Optional logical namespace for memory segmentation.
* ``SA01_MEMORY_NAMESPACE``: Memory namespace (default: "wm").
* ``SA01_SOMA_TIMEOUT_SECONDS``: Request timeout in seconds (default: 30).
* ``SA01_VERIFY_SSL``: Toggle TLS certificate verification (true/false).
* ``SA01_TLS_CA``: Path to CA bundle for TLS verification.
* ``SA01_TLS_CERT``: Path to client certificate for mTLS.
* ``SA01_TLS_KEY``: Path to client key for mTLS.
* ``SA01_SOMA_MAX_RETRIES``: Maximum retry attempts (default: 2).
* ``SA01_SOMA_RETRY_BASE_MS``: Base retry delay in milliseconds (default: 150).

The client keeps a single ``httpx.AsyncClient`` instance per process to reuse
connections.  Callers should obtain the singleton through ``SomaClient.get()``
instead of instantiating the class directly.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence
from uuid import uuid4
from weakref import WeakKeyDictionary

import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject

# Use the idempotent wrappers from the observability package. They ensure
# that metric collectors are created only once, even if this module is
# imported multiple times.
from observability.metrics import Counter, Histogram

# Django settings for centralized configuration (VIBE compliant)
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
try:
    from django.conf import settings as django_settings
except Exception:
    django_settings = None  # Fallback for non-Django contexts

def _get_setting(name: str, default: str = "") -> str:
    """Get setting from Django settings or environment."""
    if django_settings:
        return str(getattr(django_settings, name, os.environ.get(name, default)))
    return os.environ.get(name, default)

logger = logging.getLogger(__name__)

# Prometheus metrics for SomaBrain client
# Avoid duplicate registration when imported multiple times.
# Prometheus metrics for the SomaBrain client – created via the wrapper
# ``Counter`` / ``Histogram`` which internally calls ``_ensure_metric``.
SOMA_REQUESTS_TOTAL = Counter(
    "somabrain_http_requests_total",
    "Total SomaBrain HTTP requests by method/path/status",
    labelnames=("method", "path", "status"),
)
SOMA_REQUEST_SECONDS = Histogram(
    "somabrain_request_seconds",
    "Latency of SomaBrain HTTP requests",
    labelnames=("method", "path", "status"),
)
MEMORY_WRITE_TOTAL = Counter(
    "somabrain_memory_write_total",
    "Count of memory writes via SomaBrain",
    labelnames=("result",),
)
MEMORY_WRITE_SECONDS = Histogram(
    "somabrain_memory_write_seconds",
    "Latency of memory writes via SomaBrain",
    labelnames=("result",),
)


def _sanitize_legacy_base_url(raw_base_url: str) -> str:
    """Sanitize the provided base URL.

    - Ensures a non‑empty, well‑formed URL string
    - If the legacy port 9595 is detected, preserve the original host and
      scheme but rewrite the port to 9696
    """
    candidate = (raw_base_url or "").strip()
    if not candidate:
        raise ValueError(
            "SA01_SOMA_BASE_URL is required. Set it to your SomaBrain service URL "
            "(e.g., http://somabrain:9696)"
        )

    normalized = candidate.rstrip("/")

    try:
        url = httpx.URL(normalized)
    except Exception as exc:
        raise ValueError(f"Invalid SOMA_BASE_URL '{candidate}': {exc}") from exc

    # Rewrite only the legacy port 9595 to the current default (9696),
    # preserving original host and scheme.
    if url.port == 9595:
        try:
            override = url.copy_with(port=9696)
            logger.warning(
                "Detected legacy SomaBrain port on %s; redirecting to %s",
                normalized,
                override,
            )
            return str(override).rstrip("/")
        except Exception as exc:
            raise ValueError(f"Cannot rewrite legacy port for '{normalized}': {exc}") from exc

    return normalized


def _default_base_url() -> str:
    """Return the base URL for SomaBrain on demand (no import-time side effects)."""
    url = os.environ.get("SA01_SOMA_BASE_URL")
    if not url:
        raise RuntimeError(
            "SA01_SOMA_BASE_URL must be set explicitly. No alternate sources allowed per VIBE rules."
        )
    return str(url).rstrip("/")


# Deliberately avoid computing the base URL at import time to keep tests/env
# setup lightweight. The value is resolved at runtime when a client is
# instantiated.
DEFAULT_BASE_URL: str | None = None
DEFAULT_TIMEOUT = float(os.environ.get("SA01_SOMA_TIMEOUT_SECONDS", "30") or "30")
DEFAULT_UNIVERSE = os.environ.get("SA01_NAMESPACE")
DEFAULT_NAMESPACE = os.environ.get("SA01_MEMORY_NAMESPACE", "wm") or "wm"

TENANT_HEADER = os.environ.get("SA01_TENANT_HEADER", "X-Tenant-ID") or "X-Tenant-ID"
AUTH_HEADER = os.environ.get("SA01_AUTH_HEADER", "Authorization") or "Authorization"


def _truthy_env(var_name: str) -> bool:
    value = os.environ.get(var_name)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _running_inside_container() -> bool:
    if _truthy_env("SA01_FORCE_CONTAINER"):
        return True
    if _truthy_env("SA01_DISABLE_CONTAINER_CHECK"):
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
        override_host = os.environ.get("SA01_CONTAINER_HOST_ALIAS")
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
        base_url: str | None = DEFAULT_BASE_URL,
        *,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        namespace: Optional[str] = DEFAULT_NAMESPACE,
        timeout: float = DEFAULT_TIMEOUT,
        verify_ssl: Optional[bool] = None,
    ) -> None:
        if not base_url:
            base_url = _default_base_url()
        logger.debug(
            "SomaClient initializing",
            extra={
                "provided_base_url": base_url,
                "env_base_url": os.environ.get("SA01_SOMA_BASE_URL"),
            },
        )
        sanitized_base_url = _sanitize_legacy_base_url(base_url)
        self.base_url = _normalize_base_url(sanitized_base_url)
        self.namespace = namespace
        self.universe = DEFAULT_UNIVERSE
        self._tenant_id = tenant_id or os.environ.get("SA01_TENANT_ID")
        self._api_key = api_key or os.environ.get("SA01_SOMA_API_KEY")
        verify_override = _boolean(os.environ.get("SA01_VERIFY_SSL"))
        if verify_ssl is None and verify_override is not None:
            verify_ssl = verify_override

        # TLS settings (optional mTLS)
        ca_bundle = os.environ.get("SA01_TLS_CA")
        client_cert = os.environ.get("SA01_TLS_CERT")
        client_key = os.environ.get("SA01_TLS_KEY")
        verify_value: bool | str = True
        if verify_ssl is not None:
            verify_value = verify_ssl
        if ca_bundle:
            verify_value = ca_bundle

        client_cert_param: str | tuple[str, str] | None = None
        if client_cert and client_key:
            client_cert_param = (client_cert, client_key)
        elif client_cert:
            client_cert_param = client_cert

        self._client_params = {
            "base_url": self.base_url,
            "timeout": httpx.Timeout(timeout),
            "headers": self._build_default_headers(),
            "verify": verify_value,
            **({"cert": client_cert_param} if client_cert_param else {}),
        }
        self._clients: WeakKeyDictionary[asyncio.AbstractEventLoop, httpx.AsyncClient] = (
            WeakKeyDictionary()
        )
        self._locks: WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = (
            WeakKeyDictionary()
        )

        # Simple circuit breaker state
        self._cb_failures: int = 0
        self._cb_open_until: float = 0.0
        self._CB_THRESHOLD: int = 3
        self._CB_COOLDOWN_SEC: float = 15.0

        # Retry configuration
        self._max_retries: int = int(os.environ.get("SA01_SOMA_MAX_RETRIES", "2") or "2")
        self._retry_base_ms: int = int(os.environ.get("SA01_SOMA_RETRY_BASE_MS", "150") or "150")

    @classmethod
    def get(cls) -> "SomaClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def close(self) -> None:
        for client in list(self._clients.values()):
            await client.aclose()
        self._clients.clear()
        self._locks.clear()

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    def _get_lock(self) -> asyncio.Lock:
        loop = self._get_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    def _get_client(self) -> httpx.AsyncClient:
        loop = self._get_loop()
        client = self._clients.get(loop)
        if client is None:
            client = httpx.AsyncClient(**self._client_params)
            self._clients[loop] = client
        return client

    def _build_default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self._api_key:
            headers[AUTH_HEADER] = (
                f"Bearer {self._api_key}"
                if AUTH_HEADER.lower() == "authorization"
                else self._api_key
            )
        if self._tenant_id:
            headers[TENANT_HEADER] = self._tenant_id
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        allow_404: bool = False,
    ) -> Any:
        # Short-circuit if breaker is open
        now = time.time()
        if self._cb_open_until and now < self._cb_open_until:
            raise SomaClientError(
                f"SomaBrain unavailable (circuit open for {int(self._cb_open_until - now)}s); please try again shortly"
            )

        url = path if path.startswith("/") else f"/{path}"
        request_headers: Dict[str, str] = {}
        if headers:
            request_headers.update(headers)

        # Ensure a request id and propagate trace context into headers
        request_headers.setdefault("X-Request-ID", str(uuid4()))
        try:
            inject(request_headers)
        except Exception:
            # Never fail on propagation
            pass

        logger.debug(
            "SomaClient request",
            extra={
                "method": method,
                "path": url,
                "base_url": self.base_url,
                "env_base_url": os.environ.get("SA01_SOMA_BASE_URL"),
                "params_present": bool(params),
            },
        )

        attempt = 0
        start_ts = time.perf_counter()
        status_label = "error"
        while True:
            try:
                async with self._get_lock():
                    response = await self._get_client().request(
                        method,
                        url,
                        json=json,
                        params=params,
                        headers=request_headers or None,
                    )
            except httpx.RequestError as e:
                # Network / transport-level failure: record failure and maybe retry
                self._cb_failures += 1
                if self._cb_failures >= self._CB_THRESHOLD:
                    self._cb_open_until = time.time() + self._CB_COOLDOWN_SEC
                if attempt < self._max_retries:
                    attempt += 1
                    backoff = (self._retry_base_ms * (2 ** (attempt - 1))) / 1000.0
                    backoff = backoff * (1.0 + (0.25 * (os.getpid() % 4)))  # simple jitter
                    await asyncio.sleep(backoff)
                    continue
                # No more retries
                duration = time.perf_counter() - start_ts
                SOMA_REQUESTS_TOTAL.labels(method, url, status_label).inc()
                SOMA_REQUEST_SECONDS.labels(method, url, status_label).observe(duration)
                raise SomaClientError(f"SomaBrain request {method} {url} failed: {str(e)}") from e

            # Response received
            status_label = str(response.status_code)
            logger.debug(
                "SomaClient response",
                extra={
                    "method": method,
                    "path": url,
                    "status_code": response.status_code,
                },
            )

            if allow_404 and response.status_code == 404:
                # success path; reset breaker and record metrics
                self._cb_failures = 0
                self._cb_open_until = 0.0
                duration = time.perf_counter() - start_ts
                SOMA_REQUESTS_TOTAL.labels(method, url, status_label).inc()
                SOMA_REQUEST_SECONDS.labels(method, url, status_label).observe(duration)
                return None

            # Retry on 5xx and 429 (Too Many Requests); honor Retry-After if present
            if (
                response.status_code >= 500 or response.status_code == 429
            ) and attempt < self._max_retries:
                attempt += 1
                # Baseline exponential backoff with jitter
                backoff = (self._retry_base_ms * (2 ** (attempt - 1))) / 1000.0
                backoff = backoff * (1.0 + (0.25 * (os.getpid() % 4)))
                # If server provided Retry-After, prefer it when longer
                ra = response.headers.get("retry-after")
                if ra:
                    try:
                        # Retry-After can be seconds or HTTP-date; try seconds first
                        ra_s = float(ra)
                    except ValueError:
                        # Parse HTTP-date to seconds delta (simple/lenient)
                        try:
                            import email.utils as _eutils
                            import time as _time

                            ts = _eutils.parsedate_to_datetime(ra)
                            if ts is not None:
                                delta = ts.timestamp() - _time.time()
                                ra_s = max(0.0, float(delta))
                            else:
                                ra_s = 0.0
                        except Exception:
                            ra_s = 0.0
                    if ra_s and ra_s > backoff:
                        backoff = min(ra_s, 120.0)  # cap to a sane upper bound
                await asyncio.sleep(backoff)
                continue

            break

        if response.status_code >= 400:
            detail: Optional[str]
            try:
                detail = response.json().get("detail")  # type: ignore[assignment]
            except Exception:
                detail = response.text or None
            # 5xx considered failure for breaker purposes
            if response.status_code >= 500:
                self._cb_failures += 1
                if self._cb_failures >= self._CB_THRESHOLD:
                    self._cb_open_until = time.time() + self._CB_COOLDOWN_SEC
            duration = time.perf_counter() - start_ts
            SOMA_REQUESTS_TOTAL.labels(method, url, status_label).inc()
            SOMA_REQUEST_SECONDS.labels(method, url, status_label).observe(duration)
            raise SomaClientError(
                f"SomaBrain request {method} {url} failed: {response.status_code} {detail or response.text}"
            )
        # success path; reset breaker
        self._cb_failures = 0
        self._cb_open_until = 0.0
        duration = time.perf_counter() - start_ts
        SOMA_REQUESTS_TOTAL.labels(method, url, status_label).inc()
        SOMA_REQUEST_SECONDS.labels(method, url, status_label).observe(duration)
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
        tenant: Optional[str] = None,
        namespace: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Sequence[str]] = None,
        policy_tags: Optional[Sequence[str]] = None,
        importance: Optional[float] = None,
        novelty: Optional[float] = None,
        trace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Store a memory item via SomaBrain.

        The new `/memory/remember` endpoint is attempted first; if the server
        only supports the legacy surface we fall back to `/remember`.
        """

        payload_dict = dict(payload)
        metadata_dict = {}
        if isinstance(payload_dict.get("metadata"), Mapping):
            metadata_dict = dict(payload_dict["metadata"])  # type: ignore[assignment]
        derived_tenant = (
            tenant
            or payload_dict.get("tenant")
            or metadata_dict.get("tenant")
            or (os.environ.get("SA01_TENANT_ID", "") or "").strip()
            or "default"
        )
        # Determine the memory namespace. Prefer explicit arg or payload field; fall back to client default ("wm").
        derived_namespace = (
            namespace
            or payload_dict.get("namespace")
            or metadata_dict.get("namespace")
            or self.namespace
            or "wm"
        )

        # Determine the logical universe. Prefer explicit arg, then metadata.universe_id, then client default.
        derived_universe = universe or metadata_dict.get("universe_id") or self.universe

        body: Dict[str, Any] = {
            "value": payload_dict,
            "tenant": derived_tenant,
            "namespace": derived_namespace,
            "key": payload_dict.get("id"),
        }

        # Ensure we do not send empty strings for key/tenant/namespace
        if not body["key"]:
            body.pop("key")
        if not body["tenant"]:
            body["tenant"] = "default"
        if not body["namespace"]:
            body["namespace"] = "default"

        if coord:
            body["coord"] = coord
        if derived_universe:
            body["universe"] = derived_universe
            body["value"].setdefault("universe", derived_universe)
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if tags:
            body["tags"] = list(tags)
        if policy_tags:
            body["policy_tags"] = list(policy_tags)
        if importance is not None:
            body["importance"] = importance
        if novelty is not None:
            body["novelty"] = novelty
        if trace_id:
            body["trace_id"] = trace_id

        tracer = trace.get_tracer(__name__)
        start_ts = time.perf_counter()
        with tracer.start_as_current_span("somabrain.remember"):
            response = await self._request(
                "POST",
                "/memory/remember",
                json={k: v for k, v in body.items() if v is not None},
            )
        duration = time.perf_counter() - start_ts
        MEMORY_WRITE_TOTAL.labels("ok").inc()
        MEMORY_WRITE_SECONDS.labels("ok").observe(duration)
        return response

    async def recall(
        self,
        query: str,
        *,
        top_k: int = 3,
        universe: Optional[str] = None,
        tenant: Optional[str] = None,
        namespace: Optional[str] = None,
        layer: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        min_score: Optional[float] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        scoring_mode: Optional[str] = None,
        pin_results: Optional[bool] = None,
        chunk_size: Optional[int] = None,
        chunk_index: Optional[int] = None,
    ) -> Mapping[str, Any]:
        """Recall memories for a query."""

        body: Dict[str, Any] = {
            "tenant": tenant or (os.environ.get("SA01_TENANT_ID", "") or "").strip() or "default",
            "namespace": namespace or self.namespace or "default",
            "query": query,
            "top_k": top_k,
        }
        # Use explicit universe when provided.
        if universe or self.universe:
            body["universe"] = universe or self.universe
        if layer:
            body["layer"] = layer
        if tags:
            body["tags"] = list(tags)
        if min_score is not None:
            body["min_score"] = float(min_score)
        if session_id:
            body["session_id"] = session_id
        if conversation_id:
            body["conversation_id"] = conversation_id
        if scoring_mode:
            body["scoring_mode"] = scoring_mode
        if pin_results is not None:
            body["pin_results"] = bool(pin_results)
        if chunk_size is not None:
            body["chunk_size"] = int(chunk_size)
        if chunk_index is not None:
            body["chunk_index"] = int(chunk_index)

        return await self._request(
            "POST",
            "/memory/recall",
            json={k: v for k, v in body.items() if v is not None},
        )

    async def recall_stream(
        self,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Invoke the streaming recall endpoint."""
        return await self._request("POST", "/memory/recall/stream", json=dict(payload))

    async def remember_batch(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Persist multiple memories in a single request."""
        return await self._request("POST", "/memory/remember/batch", json=dict(payload))

    async def get_recall_session(self, session_id: str) -> Mapping[str, Any]:
        return await self._request("GET", f"/memory/context/{session_id}")

    async def memory_metrics(self, *, tenant: str, namespace: str) -> Mapping[str, Any]:
        params = {"tenant": tenant, "namespace": namespace}
        return await self._request("GET", "/memory/metrics", params=params)

    async def rag_retrieve(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/rag/retrieve", json=dict(payload))

    async def context_evaluate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/context/evaluate", json=dict(payload))

    async def context_feedback(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/context/feedback", json=dict(payload))

    async def adaptation_state(self, tenant_id: Optional[str] = None) -> Mapping[str, Any]:
        params = {"tenant_id": tenant_id} if tenant_id else None
        return await self._request("GET", "/context/adaptation/state", params=params)

    async def put_persona(
        self,
        persona_id: str,
        payload: Mapping[str, Any],
        *,
        etag: Optional[str] = None,
    ) -> Any:
        headers = {"If-Match": etag} if etag else None
        return await self._request(
            "PUT", f"/persona/{persona_id}", json=dict(payload), headers=headers
        )

    async def get_persona(self, persona_id: str) -> Mapping[str, Any]:
        return await self._request("GET", f"/persona/{persona_id}")

    async def delete_persona(self, persona_id: str) -> Any:
        return await self._request("DELETE", f"/persona/{persona_id}")

    async def link(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/link", json=dict(payload))

    async def plan_suggest(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/plan/suggest", json=dict(payload))

    async def recall_delete(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/recall/delete", json=dict(payload))

    async def constitution_version(self) -> Mapping[str, Any]:
        return await self._request("GET", "/constitution/version")

    async def constitution_validate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/constitution/validate", json=dict(payload))

    async def constitution_load(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return await self._request("POST", "/constitution/load", json=dict(payload))

    async def opa_policy(self) -> Mapping[str, Any]:
        return await self._request("GET", "/opa/policy")

    async def update_opa_policy(self) -> Mapping[str, Any]:
        return await self._request("POST", "/opa/policy")

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

    # ------------------------------------------------------------------
    # Neuromodulation endpoints (verified from SomaBrain OpenAPI spec)
    # ------------------------------------------------------------------

    async def get_neuromodulators(
        self,
        *,
        tenant_id: Optional[str] = None,
        persona_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Get current neuromodulator state from SomaBrain.
        
        Args:
            tenant_id: Optional tenant identifier.
            persona_id: Optional persona identifier.

        Returns:
            NeuromodStateModel with dopamine, serotonin, noradrenaline, acetylcholine
        """
        # SomaBrain API: GET /neuromodulators?tenant_id=...&persona_id=...
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        if persona_id:
            params["persona_id"] = persona_id
        return await self._request("GET", "/neuromodulators", params=params)

    async def update_neuromodulators(
        self,
        *,
        tenant_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        neuromodulators: Optional[Mapping[str, float]] = None,
    ) -> Mapping[str, Any]:
        """Update neuromodulator state in SomaBrain.

        Args:
            tenant_id: Optional tenant identifier.
            persona_id: Optional persona identifier.
            neuromodulators: Dict with dopamine, serotonin, noradrenaline, acetylcholine

        Returns:
            Updated NeuromodStateModel
        """
        # SomaBrain API: POST /neuromodulators with NeuromodStateModel body
        body: Dict[str, Any] = {}
        if neuromodulators:
            body.update(neuromodulators)
        if tenant_id:
            body["tenant_id"] = tenant_id
        if persona_id:
            body["persona_id"] = persona_id
        return await self._request("POST", "/neuromodulators", json=body)

    async def get_adaptation_state(
        self,
        *,
        tenant_id: Optional[str] = None,
        persona_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Get current adaptation state from SomaBrain.

        This wraps the /context/adaptation/state endpoint which returns
        retrieval weights, utility weights, history length, and learning rate.

        Args:
            tenant_id: Optional tenant filter
            persona_id: Optional persona filter

        Returns:
            AdaptationStateResponse with retrieval, utility, history_len, learning_rate
        """
        # SomaBrain API: GET /context/adaptation/state?tenant_id=X&persona_id=Y
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        if persona_id:
            params["persona_id"] = persona_id
        return await self._request("GET", "/context/adaptation/state", params=params)

    async def sleep_cycle(
        self,
        *,
        tenant_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        nrem: bool = True,
        rem: bool = True,
    ) -> Mapping[str, Any]:
        """Trigger a sleep cycle for memory consolidation.

        This wraps the /sleep/run endpoint which initiates NREM and/or REM
        sleep phases for memory consolidation and pruning.

        Args:
            tenant_id: Optional tenant identifier.
            persona_id: Optional persona identifier.
            duration_minutes: Optional duration in minutes.
            nrem: Whether to run NREM sleep phase (default True)
            rem: Whether to run REM sleep phase (default True)

        Returns:
            SleepRunResponse with ok and run_id
        """
        # SomaBrain API: POST /sleep/run with SleepRunRequest body
        body: Dict[str, Any] = {
            "nrem": nrem,
            "rem": rem,
        }
        if tenant_id:
            body["tenant_id"] = tenant_id
        if persona_id:
            body["persona_id"] = persona_id
        if duration_minutes:
            body["duration_minutes"] = duration_minutes
        return await self._request("POST", "/sleep/run", json=body)

    async def sleep_status(self) -> Mapping[str, Any]:
        """Get current sleep status from SomaBrain.

        Returns:
            SleepStatusResponse with enabled, interval_seconds, last
        """
        return await self._request("GET", "/sleep/status")

    # ------------------------------------------------------------------
    # New endpoints per SomaBrain integration spec
    # ------------------------------------------------------------------

    async def adaptation_reset(
        self,
        *,
        tenant_id: Optional[str] = None,
        base_lr: Optional[float] = None,
        reset_history: bool = True,
        retrieval_defaults: Optional[Mapping[str, float]] = None,
        utility_defaults: Optional[Mapping[str, float]] = None,
        gains: Optional[Mapping[str, float]] = None,
        constraints: Optional[Mapping[str, float]] = None,
    ) -> Mapping[str, Any]:
        """Reset adaptation engine to defaults for clean benchmarks.

        Args:
            tenant_id: Tenant identifier for per-tenant reset
            base_lr: Optional base learning rate override
            reset_history: Whether to clear feedback history (default True)
            retrieval_defaults: Optional retrieval weight defaults {alpha, beta, gamma, tau}
            utility_defaults: Optional utility weight defaults {lambda_, mu, nu}
            gains: Optional adaptation gains {alpha, gamma, lambda_, mu, nu}
            constraints: Optional adaptation constraints {*_min, *_max}

        Returns:
            {"ok": True, "tenant_id": str}

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
        """
        body: Dict[str, Any] = {"reset_history": reset_history}
        if tenant_id:
            body["tenant_id"] = tenant_id
        if base_lr is not None:
            body["base_lr"] = base_lr
        if retrieval_defaults:
            body["retrieval_defaults"] = dict(retrieval_defaults)
        if utility_defaults:
            body["utility_defaults"] = dict(utility_defaults)
        if gains:
            body["gains"] = dict(gains)
        if constraints:
            body["constraints"] = dict(constraints)
        return await self._request("POST", "/context/adaptation/reset", json=body)

    async def act(
        self,
        task: str,
        *,
        top_k: int = 3,
        universe: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Execute a cognitive action step with salience scoring.

        Args:
            task: The task/action description to execute
            top_k: Number of memory hits to consider (default 3)
            universe: Optional universe scope for memory operations
            session_id: Optional session ID for focus state tracking

        Returns:
            ActResponse with task, results (list of ActStepResult), plan, plan_universe

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
        """
        body: Dict[str, Any] = {"task": task, "top_k": top_k}
        if universe:
            body["universe"] = universe
        headers: Optional[Dict[str, str]] = None
        if session_id:
            headers = {"X-Session-ID": session_id}
        return await self._request("POST", "/act", json=body, headers=headers)

    async def brain_sleep_mode(
        self,
        target_state: str,
        *,
        ttl_seconds: Optional[int] = None,
        async_mode: bool = False,
        trace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Transition tenant sleep state via cognitive endpoint.

        Args:
            target_state: One of "active", "light", "deep", "freeze"
            ttl_seconds: Optional TTL after which state auto-reverts to active
            async_mode: If True, return immediately (non-blocking)
            trace_id: Optional trace identifier for observability

        Returns:
            Sleep transition response

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
            ValueError: If target_state is invalid
        """
        valid_states = {"active", "light", "deep", "freeze"}
        if target_state not in valid_states:
            raise ValueError(f"target_state must be one of {valid_states}, got '{target_state}'")
        body: Dict[str, Any] = {"target_state": target_state, "async_mode": async_mode}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if trace_id:
            body["trace_id"] = trace_id
        return await self._request("POST", "/api/brain/sleep_mode", json=body)

    async def util_sleep(
        self,
        target_state: str,
        *,
        ttl_seconds: Optional[int] = None,
        async_mode: bool = False,
        trace_id: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Transition tenant sleep state via utility endpoint.

        Args:
            target_state: One of "active", "light", "deep", "freeze"
            ttl_seconds: Optional TTL after which state auto-reverts to active
            async_mode: If True, return immediately (non-blocking)
            trace_id: Optional trace identifier for observability

        Returns:
            Sleep transition response

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
            ValueError: If target_state is invalid
        """
        valid_states = {"active", "light", "deep", "freeze"}
        if target_state not in valid_states:
            raise ValueError(f"target_state must be one of {valid_states}, got '{target_state}'")
        body: Dict[str, Any] = {"target_state": target_state, "async_mode": async_mode}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if trace_id:
            body["trace_id"] = trace_id
        return await self._request("POST", "/api/util/sleep", json=body)

    async def micro_diag(self) -> Mapping[str, Any]:
        """Get microcircuit diagnostics (admin mode).

        Returns:
            Diagnostic info with enabled, tenant, columns, namespace

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
        """
        return await self._request("GET", "/micro/diag")

    async def sleep_status_all(self) -> Mapping[str, Any]:
        """Get sleep status for all tenants (admin mode).

        Returns:
            {"enabled": bool, "interval_seconds": int, "tenants": {tid: {nrem, rem}}}

        Raises:
            SomaClientError: On HTTP 4xx/5xx or network failure
        """
        return await self._request("GET", "/sleep/status/all")


__all__ = [
    "SomaClient",
    "SomaClientError",
    "SomaMemoryRecord",
]
