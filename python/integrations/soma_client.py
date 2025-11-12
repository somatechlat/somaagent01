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

* ``SA01_SOMA_BASE_URL``: Base URL of the SomaBrain API.  Defaults to
    ``http://localhost:9696`` which matches the local development cluster.
* ``SOMA_API_KEY``: Optional API key.  When provided the client sends it in an
  ``Authorization: Bearer`` header (or a custom header if
  ``SOMA_AUTH_HEADER`` is supplied).
* ``SA01_SOMA_TENANT_ID``: Optional tenant identifier forwarded via
  ``X-Tenant-ID`` (or a custom header defined by ``SOMA_TENANT_HEADER``).
* ``SA01_SOMA_NAMESPACE``: Optional logical namespace value.  When set it is added
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
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)
from uuid import uuid4
from weakref import WeakKeyDictionary

import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics for SomaBrain client
SOMA_REQUESTS_TOTAL = Counter(
    "somabrain_requests_total",
    "Total SomaBrain HTTP requests",
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


def _sanitize_prior_base_url(raw_base_url: str) -> str:
    """Sanitize the provided base URL.

    - Ensures a non‑empty, well‑formed URL string
    - If the prior port 9595 is detected, preserve the original host and
      scheme but rewrite the port to 9696
    """
    candidate = (raw_base_url or "").strip()
    if not candidate:
        return "http://localhost:9696"

    normalized = candidate.rstrip("/")

    try:
        url = httpx.URL(normalized)
    except Exception:
        logger.warning("Invalid SA01_SOMA_BASE_URL %s; falling back to localhost:9696", candidate)
        return "http://localhost:9696"

    # Rewrite only the prior port 9595 to the current default (9696),
    # preserving original host and scheme.
    if url.port == 9595:
        try:
            override = url.copy_with(port=9696)
        except Exception:
            override = httpx.URL("http://localhost:9696")
        logger.warning(
            "Detected prior SomaBrain port on %s; redirecting to %s",
            normalized,
            override,
        )
        return str(override).rstrip("/")

    return normalized


def _default_base_url() -> str:
    """Return the base URL for SomaBrain.

    The environment variable ``SA01_SOMA_BASE_URL`` can be used to point to a custom
    endpoint. If it is not set we default to ``http://localhost:9696``. The
    function no longer performs any prior‑host sanitisation – that logic lives
    in ``_sanitize_prior_base_url`` and is only applied when an explicit URL
    is provided.
    """
    return os.getenv("SA01_SOMA_BASE_URL", "http://localhost:9696")


DEFAULT_BASE_URL = _default_base_url()
DEFAULT_TIMEOUT = float(os.environ.get("SOMA_TIMEOUT_SECONDS", "30"))
# IMPORTANT: Distinguish logical universe vs. memory namespace
# - SA01_SOMA_NAMESPACE conveys the universe/context (e.g. "somabrain_ns:public")
# - SA01_SOMA_MEMORY_NAMESPACE is the memory sub-namespace (e.g. "wm", "ltm").
#   If not provided, default to "wm" for working memory.
DEFAULT_UNIVERSE = os.environ.get("SA01_SOMA_NAMESPACE")
DEFAULT_NAMESPACE = os.environ.get("SA01_SOMA_MEMORY_NAMESPACE", "wm")

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
        logger.debug(
            "SomaClient initializing",
            extra={
                "provided_base_url": base_url,
                "env_base_url": os.environ.get("SA01_SOMA_BASE_URL"),
            },
        )
        sanitized_base_url = _sanitize_prior_base_url(base_url)
        self.base_url = _normalize_base_url(sanitized_base_url)
        # Memory namespace (e.g. "wm"). Not the same as the logical universe.
        self.namespace = namespace
        # Universe/context identifier (e.g. "somabrain_ns:public")
        self.universe = DEFAULT_UNIVERSE
        self._tenant_id = tenant_id or os.environ.get("SA01_SOMA_TENANT_ID")
        self._api_key = api_key or os.environ.get("SOMA_API_KEY")
        verify_override = _boolean(os.environ.get("SOMA_VERIFY_SSL"))
        if verify_ssl is None and verify_override is not None:
            verify_ssl = verify_override

        # TLS settings (optional mTLS)
        ca_bundle = os.environ.get("SOMA_TLS_CA")
        client_cert = os.environ.get("SOMA_TLS_CERT")
        client_key = os.environ.get("SOMA_TLS_KEY")
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
        self._max_retries: int = int(os.environ.get("SOMA_MAX_RETRIES", "2"))
        self._retry_base_ms: int = int(os.environ.get("SOMA_RETRY_BASE_MS", "150"))

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
        last_exc: Exception | None = None
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
                last_exc = e
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
        only supports the prior surface we fall back to `/remember`.
        """

        payload_dict = dict(payload)
        metadata_dict = {}
        if isinstance(payload_dict.get("metadata"), Mapping):
            metadata_dict = dict(payload_dict["metadata"])  # type: ignore[assignment]
        derived_tenant = (
            tenant
            or payload_dict.get("tenant")
            or metadata_dict.get("tenant")
            or os.getenv("SA01_SOMA_TENANT_ID", "").strip()
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

        # Derive a stable key: prefer payload.id, then explicit/idempotency keys, else a short hash of the value
        candidate_key: Optional[str] = None
        if isinstance(payload_dict.get("id"), (str, int)):
            candidate_key = str(payload_dict.get("id"))
        elif isinstance(payload_dict.get("idempotency_key"), (str, int)):
            candidate_key = str(payload_dict.get("idempotency_key"))
        elif isinstance(metadata_dict.get("idempotency_key"), (str, int)):
            candidate_key = str(metadata_dict.get("idempotency_key"))
        elif isinstance(payload_dict.get("session_id"), (str, int)) and isinstance(
            payload_dict, Mapping
        ):
            # Combine session_id with value for stability if available
            try:
                blob = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
            except Exception:
                blob = repr(payload_dict).encode("utf-8")
            candidate_key = (
                str(payload_dict.get("session_id")) + ":" + hashlib.sha256(blob).hexdigest()[:16]
            )
        else:
            try:
                blob = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
            except Exception:
                blob = repr(payload_dict).encode("utf-8")
            candidate_key = hashlib.sha256(blob).hexdigest()[:24]

        body: Dict[str, Any] = {
            "value": payload_dict,
            "tenant": derived_tenant,
            "namespace": derived_namespace,
            "key": candidate_key,
        }

        # Ensure we do not send empty strings for key/tenant/namespace
        if not body["key"]:
            body.pop("key")
        if not body["tenant"]:
            body["tenant"] = "default"
        if not body["namespace"]:
            body["namespace"] = "default"

        # IMPORTANT: do NOT send coord to /memory/remember (spec does not accept it). We still use coord when falling back
        # to prior /remember (handled below).
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
            # Prefer new endpoint; if unavailable (404) we fall back below.
            # Additionally, tolerate certain 4xx responses (e.g. "memory pool unavailable")
            # by treating them as a signal to attempt the prior endpoint.
            try:
                response = await self._request(
                    "POST",
                    "/memory/remember",
                    json={k: v for k, v in body.items() if v is not None},
                    allow_404=True,
                )
            except SomaClientError as exc:
                msg = str(exc).lower()
                # Some deployments respond 400 with detail "memory pool unavailable"
                # while the prior /remember path continues to work. Fall back in that case.
                if "memory pool unavailable" in msg or " 400 " in msg:
                    response = None
                else:
                    raise
        if response is None:
            prior_payload: Dict[str, Any] = {"payload": dict(payload)}
            if coord:
                # Prior endpoint supports coord
                prior_payload["coord"] = coord
            if universe or self.universe:
                resolved_universe = universe or self.universe
                if resolved_universe:
                    prior_payload["universe"] = resolved_universe
                    prior_payload.setdefault("payload", {})
                    prior_payload["payload"]["universe"] = resolved_universe
            response = await self._request("POST", "/remember", json=prior_payload)
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
        """Recall memories for a query.

        Prefer the richer `/memory/recall` endpoint but tolerate the prior
        """

        body: Dict[str, Any] = {
            "tenant": tenant or os.getenv("SA01_SOMA_TENANT_ID", "").strip() or "default",
            "namespace": namespace or self.namespace or "default",
            "query": query,
            "top_k": top_k,
        }
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

        # Spec prefers a query parameter named "payload" which may be a JSON string/object; send compact JSON string first
        params_payload = None
        try:
            params_payload = json.dumps(
                {k: v for k, v in body.items() if v is not None}, separators=(",", ":")
            )
        except Exception:
            params_payload = None

        response = None
        if params_payload is not None:
            try:
                response = await self._request(
                    "POST",
                    "/memory/recall",
                    params={"payload": params_payload},
                    allow_404=True,
                )
            except SomaClientError:
                response = None

        if response is None:
            response = await self._request(
                "POST",
                "/memory/recall",
                json={k: v for k, v in body.items() if v is not None},
                allow_404=True,
            )
        if response is None:
            prior_body = {"query": query, "top_k": top_k}
            if universe or self.universe:
                prior_body["universe"] = universe or self.universe
            return await self._request("POST", "/recall", json=prior_body)
        return response

    async def recall_stream(
        self,
        payload: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Invoke the streaming recall endpoint."""
        params_payload = None
        try:
            params_payload = json.dumps(dict(payload), separators=(",", ":"))
        except Exception:
            params_payload = None

        response = None
        if params_payload is not None:
            try:
                response = await self._request(
                    "POST", "/memory/recall/stream", params={"payload": params_payload}
                )
            except SomaClientError:
                response = None
        if response is None:
            response = await self._request("POST", "/memory/recall/stream", json=dict(payload))
        return response

    async def recall_stream_events(
        self,
        payload: Mapping[str, Any],
        *,
        request_timeout: Optional[float] = None,
    ) -> AsyncIterator[Mapping[str, Any]]:
        """Yield events from the streaming recall endpoint as they arrive.

        Tries the spec-preferred query param (?payload=<json>) first, falling back to a JSON body
        if necessary. Yields decoded JSON event dicts for each "data:" line; stops on [DONE].
        """
        # Prepare headers with tracing and request id; default headers are already on the client
        request_headers: Dict[str, str] = {"X-Request-ID": str(uuid4())}
        try:
            inject(request_headers)
        except Exception:
            pass

        timeout_val = request_timeout if (request_timeout is not None) else DEFAULT_TIMEOUT

        # Build compact JSON params payload first
        params_payload = None
        try:
            params_payload = json.dumps(dict(payload), separators=(",", ":"))
        except Exception:
            params_payload = None

        async def _stream_with(
            *,
            use_params: bool,
        ) -> AsyncIterator[Mapping[str, Any]]:
            client = self._get_client()
            kwargs: Dict[str, Any] = {
                "headers": request_headers or None,
                "timeout": httpx.Timeout(timeout_val),
            }
            if use_params and params_payload is not None:
                kwargs["params"] = {"payload": params_payload}
            else:
                kwargs["json"] = dict(payload)
            async with client.stream("POST", "/memory/recall/stream", **kwargs) as resp:
                if resp.is_error:
                    # Surface upstream error text for diagnostics
                    try:
                        body = await resp.aread()
                        detail = body.decode("utf-8", errors="ignore")[:512]
                    except Exception:
                        detail = resp.reason_phrase or ""
                    raise SomaClientError(
                        f"SomaBrain recall stream error {resp.status_code}: {detail}"
                    )
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        evt = json.loads(data_str)
                    except Exception:
                        continue
                    yield evt

        tried_params = False
        if params_payload is not None:
            tried_params = True
            try:
                async for evt in _stream_with(use_params=True):
                    yield evt
                return
            except SomaClientError:
                pass

        async for evt in _stream_with(use_params=False):
            yield evt

    async def remember_batch(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Persist multiple memories in a single request."""
        return await self._request("POST", "/memory/remember/batch", json=dict(payload))

    async def get_recall_session(self, session_id: str) -> Mapping[str, Any]:
        return await self._request("GET", f"/memory/context/{session_id}")

    async def memory_metrics(self, *, tenant: str, namespace: str) -> Mapping[str, Any]:
        params = {"tenant": tenant, "namespace": namespace}
        return await self._request("GET", "/memory/metrics", params=params)

    async def rag_retrieve(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        # No longer supported by the live API; guard with a clear error to avoid accidental use
        raise SomaClientError("/rag/retrieve is not supported by the current SomaBrain API")

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


__all__ = [
    "SomaClient",
    "SomaClientError",
    "SomaMemoryRecord",
]
