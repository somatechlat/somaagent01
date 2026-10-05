"""SomaBrain Client - Django

Production-grade HTTP client for SomaBrain cognitive service.

This client is the cognitive co-processor surface only. Memory
remember/recall/forget is NOT here — that is ``MemoryGateway`` →
``SomaBrainAdapter`` (T-1, one write path, one read path). Every route
below is verified against ``somabrain/api/v1.py`` mounts.

- Rule 1: NO BULLSHIT - Real implementation, no mocks
- Rule 4: REAL IMPLEMENTATIONS ONLY
- Rule 8: Django/Ninja ONLY
- Rule 13: CENTRALIZED SETTINGS
- Rule 32: HYBRID CONFIGURATION STANDARD
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, cast, Dict, List, Optional

import httpx
from django.conf import settings

from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker

LOGGER = logging.getLogger(__name__)


class SomaClientError(Exception):
    """Exception raised for SomaBrain client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the instance."""

        super().__init__(message)
        self.status_code = status_code


class SomaBrainClient:
    """Production SomaBrain HTTP client.

    Thread-safe singleton pattern for connection pooling.
    Uses Django settings for configuration.
    """

    _instance: Optional["SomaBrainClient"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 5.0,
    ) -> None:
        """Initialize SomaBrain client.

        Args:
            base_url: SomaBrain API base URL (defaults to settings)
            timeout: Request timeout in seconds
        """
        self._base_url = base_url or self._get_base_url()
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @staticmethod
    def _get_base_url() -> Optional[str]:
        """Get SomaBrain URL from Django settings or environment.

        Returns None when disabled (standalone mode).
        """

        # Try Django settings first
        if hasattr(settings, "SOMABRAIN_URL"):
            url = str(settings.SOMABRAIN_URL)
            if url:
                return url

        # Fallback to environment variable
        env_url = os.environ.get("SOMABRAIN_URL")
        if env_url:
            return env_url

        # Disabled in standalone mode
        return None

    @classmethod
    def get(cls) -> Optional["SomaBrainClient"]:
        """Get or create singleton instance.

        Returns None when SomaBrain is not configured (standalone mode).
        Callers must check the return value before use.
        """
        if cls._get_base_url() is None:
            return None
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_async(cls) -> Optional["SomaBrainClient"]:
        """Get or create singleton instance (async version).

        Returns None when SomaBrain is not configured (standalone mode).
        Callers must check the return value before use.
        """
        if cls._get_base_url() is None:
            return None
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def is_enabled(self) -> bool:
        """Return True when the client has a configured base URL."""
        return bool(self._base_url)

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if not self._base_url:
            raise SomaClientError("SomaBrain is not configured", status_code=503)
        if self._client is None or self._client.is_closed:
            from django.conf import settings as django_settings

            headers = {"Content-Type": "application/json"}
            token = getattr(django_settings, "SOMABRAIN_MEMORY_HTTP_TOKEN", None)
            # Fail closed. The previous code did `if token:` and simply omitted
            # the Authorization header when the secret was unset — so a
            # deployment that had forgotten to seed somabrain_memory_http_token
            # made unauthenticated calls to SomaBrain and got a 401 back that
            # named nothing. If the endpoint is configured, the credential that
            # authenticates to it is required (VIBE Rule 164).
            if not token:
                raise SomaClientError(
                    "SomaBrain is configured but the memory HTTP token is not. "
                    "Set secret/agent/credentials/somabrain_memory_http_token in Vault.",
                    status_code=503,
                )
            headers["Authorization"] = f"Bearer {token}"
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to SomaBrain.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            json: JSON body for POST/PUT
            params: Query parameters
            headers: Additional HTTP headers

        Returns:
            Response JSON as dict

        Raises:
            SomaClientError: On HTTP or connection errors
            CircuitBreakerError: If circuit breaker is OPEN
        """
        if not self._base_url:
            raise SomaClientError("SomaBrain is not configured", status_code=503)

        breaker = get_circuit_breaker("somabrain", failure_threshold=5, reset_timeout=30)

        async def _do_request() -> httpx.Response:
            """Execute request. Only 5xx/transport failures trip the breaker.

            4xx are client errors (bad path/payload) — they must not open the
            shared SomaBrain circuit and starve memory/recall.
            """
            client = await self._ensure_client()
            request_headers = headers or {}
            response = await client.request(
                method, path, json=json, params=params, headers=request_headers
            )
            if response.status_code >= 500:
                response.raise_for_status()
            return response

        try:
            response = cast(httpx.Response, await breaker.call(_do_request))
        except CircuitBreakerError as e:
            LOGGER.error("SomaBrain circuit breaker OPEN", extra={"path": path, "error": str(e)})
            raise SomaClientError(
                f"SomaBrain unavailable (circuit open): {e}", status_code=503
            ) from e
        except httpx.HTTPStatusError as e:
            LOGGER.error(
                "SomaBrain server error",
                extra={"path": path, "status": e.response.status_code},
            )
            raise SomaClientError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            LOGGER.error("SomaBrain connection error", extra={"path": path, "error": str(e)})
            raise SomaClientError(f"Connection error: {e}") from e

        if response.status_code >= 400:
            # 4xx — fail-closed to caller, but do not trip the breaker.
            LOGGER.warning(
                "SomaBrain client error (no circuit trip)",
                extra={"path": path, "status": response.status_code},
            )
            raise SomaClientError(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            )
        try:
            return cast(Dict[str, Any], response.json())
        except Exception:
            return {}

    # =========================================================================
    # CONTEXT OPERATIONS  — POST /context/*  (somabrain/api/endpoints/context.py)
    # =========================================================================

    async def context_evaluate(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate context for a conversation turn (POST /context/evaluate)."""
        return await self._request("POST", "/context/evaluate", json=request)

    async def context_feedback(self, **kwargs: Any) -> Dict[str, Any]:
        """Send contextual feedback to SomaBrain for learning (POST /context/feedback)."""
        return await self._request("POST", "/context/feedback", json=dict(kwargs))

    async def get_adaptation_state(
        self,
        tenant_id: str,
        persona_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get current adaptation state (GET /context/adaptation/state)."""
        params: Dict[str, Any] = {"tenant": tenant_id}
        if persona_id:
            params["persona"] = persona_id
        return await self._request("GET", "/context/adaptation/state", params=params)

    async def adaptation_reset(
        self,
        tenant_id: str,
        *,
        base_lr: Optional[float] = None,
        reset_history: bool = True,
    ) -> Dict[str, Any]:
        """Reset adaptation state to defaults (POST /context/adaptation/reset)."""
        body: Dict[str, Any] = {"tenant": tenant_id, "reset_history": reset_history}
        if base_lr is not None:
            body["base_lr"] = base_lr
        return await self._request("POST", "/context/adaptation/reset", json=body)

    # =========================================================================
    # NEUROMODULATOR OPERATIONS  — /neuromod/*  (somabrain/api/endpoints/neuromod.py)
    # =========================================================================

    async def get_neuromodulators(
        self,
        tenant_id: str,
        persona_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get current neuromodulator state (GET /neuromod/state)."""
        params: Dict[str, Any] = {"tenant": tenant_id}
        if persona_id:
            params["persona"] = persona_id
        return await self._request("GET", "/neuromod/state", params=params)

    async def update_neuromodulators(
        self,
        tenant_id: str,
        persona_id: str,
        neuromodulators: Dict[str, float],
    ) -> Dict[str, Any]:
        """Update neuromodulator levels (POST /neuromod/adjust)."""
        return await self._request(
            "POST",
            "/neuromod/adjust",
            json={
                "dopamine": neuromodulators.get("dopamine"),
                "serotonin": neuromodulators.get("serotonin"),
                "noradrenaline": neuromodulators.get("noradrenaline"),
                "acetylcholine": neuromodulators.get("acetylcholine"),
            },
        )

    # =========================================================================
    # PERSONA OPERATIONS  — /persona/*  (somabrain/api/endpoints/persona.py)
    # =========================================================================

    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """Get persona by ID (GET /persona/{pid})."""
        return await self._request("GET", f"/persona/{persona_id}")

    async def put_persona(
        self,
        persona_id: str,
        persona_data: Dict[str, Any],
        etag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update persona (PUT /persona/{pid})."""
        req_headers = {"If-Match": etag} if etag else None
        return await self._request(
            "PUT", f"/persona/{persona_id}", json=persona_data, headers=req_headers
        )

    # =========================================================================
    # COGNITIVE OPERATIONS  — /cognitive/*  (somabrain/api/endpoints/cognitive.py)
    # =========================================================================

    async def act(
        self,
        task: Optional[str] = None,
        *,
        agent_id: Optional[str] = None,
        input_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
        universe: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a cognitive action (POST /cognitive/act)."""
        body: Dict[str, Any] = {}
        if task is not None:
            body["task"] = task
        if agent_id is not None:
            body["agent_id"] = agent_id
        if input_text is not None:
            body["input_text"] = input_text
        if context is not None:
            body["context"] = context
        if mode is not None:
            body["mode"] = mode
        if universe:
            body["universe"] = universe
        if session_id:
            body["session_id"] = session_id
        return await self._request("POST", "/cognitive/act", json=body)

    async def plan_suggest(
        self,
        task_key: str,
        *,
        max_steps: Optional[int] = None,
        rel_types: Optional[List[str]] = None,
        universe: Optional[str] = None,
    ) -> List[str]:
        """Suggest a plan from the semantic graph around ``task_key``.

        POST /cognitive/plan/suggest
        PlanSuggestRequest  { task_key, max_steps, rel_types, universe }
        PlanSuggestResponse { plan: list[str] }

        The brain is gated on ``SOMABRAIN_USE_PLANNER`` (default False) and
        returns ``{"plan": []}`` when the flag is off. This client does not
        turn that flag on — enabling the planner is an operator choice.
        """
        body: Dict[str, Any] = {"task_key": task_key}
        if max_steps is not None:
            body["max_steps"] = max_steps
        if rel_types is not None:
            body["rel_types"] = rel_types
        if universe is not None:
            body["universe"] = universe
        result = await self._request("POST", "/cognitive/plan/suggest", json=body)
        if isinstance(result, dict):
            plan = result.get("plan", [])
            return list(plan) if isinstance(plan, list) else []
        return []

    async def set_personality(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """Set personality traits for the caller's tenant.

        POST /cognitive/personality
        PersonalityState { traits: dict[str, float] } — request AND response.
        """
        return await self._request("POST", "/cognitive/personality", json={"traits": traits})

    async def micro_diag(self) -> Dict[str, Any]:
        """Get microcircuit diagnostics (GET /cognitive/micro/diag)."""
        return await self._request("GET", "/cognitive/micro/diag")

    async def get_cognitive_state(self, agent_id: str) -> Dict[str, Any]:
        """Get cognitive state for an agent (adaptation state)."""
        return await self.get_adaptation_state(tenant_id=agent_id)

    # =========================================================================
    # THREAD OPERATIONS — /threads/  (somabrain/api/endpoints/thread.py)
    # Resumable task cursor. The cursor lives in the brain's Postgres and
    # survives agent restarts.
    # =========================================================================

    async def thread_create(self, tenant_id: str, options: List[str]) -> Dict[str, Any]:
        """Create or replace the tenant's task thread (POST /threads/thread)."""
        return await self._request(
            "POST",
            "/threads/thread",
            json={"tenant_id": tenant_id, "options": options},
        )

    async def thread_next(self, tenant_id: str) -> Optional[str]:
        """Return the next option and advance the cursor (GET /threads/thread/next).

        Returns None when the brain has no thread for this tenant.
        """
        try:
            result = await self._request(
                "GET", "/threads/thread/next", params={"tenant_id": tenant_id}
            )
        except SomaClientError as exc:
            if exc.status_code == 404:
                return None
            raise
        if isinstance(result, dict):
            option = result.get("option")
            return str(option) if option is not None else None
        return None

    async def thread_reset(self, tenant_id: str) -> Dict[str, Any]:
        """Reset the tenant's task thread cursor (PUT /threads/thread/reset)."""
        return await self._request(
            "PUT", "/threads/thread/reset", params={"tenant_id": tenant_id}
        )

    # =========================================================================
    # SLEEP/LIFECYCLE OPERATIONS  — /sleep/*  (somabrain/api/endpoints/sleep.py)
    # =========================================================================

    async def brain_sleep_mode(
        self,
        target_state: str,
        *,
        ttl_seconds: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transition brain to sleep state (POST /sleep/brain/mode)."""
        valid_states = {"active", "light", "deep", "freeze"}
        if target_state not in valid_states:
            raise ValueError(f"Invalid sleep state: {target_state}. Must be one of {valid_states}")

        body: Dict[str, Any] = {"target_state": target_state}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if trace_id:
            body["trace_id"] = trace_id
        return await self._request("POST", "/sleep/brain/mode", json=body)

    async def sleep_status(self) -> Dict[str, Any]:
        """Get current sleep status (GET /sleep/state)."""
        return await self._request("GET", "/sleep/state")

    async def trigger_sleep_cycle(self, agent_id: str) -> Dict[str, Any]:
        """Trigger sleep cycle for an agent."""
        return await self.brain_sleep_mode("deep", trace_id=agent_id)

    # =========================================================================
    # HEALTH  — /health  (somabrain/api/endpoints/health.py + config/urls.py)
    # =========================================================================

    async def health_check(self) -> bool:
        """Check if SomaBrain is healthy."""
        try:
            result = await self._request("GET", "/health")
            return result.get("status") == "ok" or result.get("ready", False)
        except SomaClientError:
            return False

    async def ping(self, timeout: float = 3.0) -> bool:
        """Cheap connector ping used by SomaBrainConnector health.

        Does not trip the circuit on 404 of optional resources; only
        transport failures count as down.
        """
        import asyncio as _asyncio

        try:
            await _asyncio.wait_for(self._request("GET", "/health"), timeout=timeout)
            return True
        except Exception as exc:  # noqa: BLE001 — ping is best-effort signal
            LOGGER.debug("SomaBrain connector ping failed: %s", exc)
            return False

    async def health(self) -> Dict[str, Any]:
        """Get health status from SomaBrain."""
        try:
            return await self._request("GET", "/health")
        except SomaClientError as e:
            return {"status": "error", "message": str(e)}


# Backwards compatibility aliases
SomaBrainError = SomaClientError


def get_somabrain_client() -> Optional[SomaBrainClient]:
    """Get SomaBrain client singleton (synchronous helper).

    Returns:
        SomaBrainClient instance when configured, or None in standalone mode.
        Callers must check the return value before use.
    """
    return SomaBrainClient.get()


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "get_somabrain_client",
]
