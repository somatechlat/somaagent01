"""SomaBrain Client - Django

Production-grade HTTP client for SomaBrain memory service.
100% Django patterns - No FastAPI, No SQLAlchemy.


- Rule 1: NO BULLSHIT - Real implementation, no mocks
- Rule 4: REAL IMPLEMENTATIONS ONLY
- Rule 8: Django/Ninja ONLY
- Rule 13: CENTRALIZED SETTINGS
- Rule 32: HYBRID CONFIGURATION STANDARD
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, cast, Dict, List, Mapping, Optional

import httpx
from django.conf import settings

from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker

# Integration: BrainBridge (Compliant Triad Architecture)
from aaas.brain import brain as BrainBridge
HAS_BRIDGE = True


LOGGER = logging.getLogger(__name__)


class SomaClientError(Exception):
    """Exception raised for SomaBrain client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the instance."""

        super().__init__(message)
        self.status_code = status_code


class SomaMemoryRecord:
    """Lightweight record for SomaBrain memory retrieval results."""

    def __init__(
        self,
        identifier: str,
        payload: Dict[str, Any],
        score: Optional[float] = None,
        coordinate: Optional[List[float]] = None,
        retriever: Optional[str] = None,
    ) -> None:
        """Initialize the instance."""

        self.identifier = identifier
        self.payload = payload
        self.score = score
        self.coordinate = coordinate
        self.retriever = retriever


class SomaBrainClient:
    """Production SomaBrain HTTP client.

    Thread-safe singleton pattern for connection pooling.
    Uses Django settings for configuration (
    """

    _instance: Optional["SomaBrainClient"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
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

        Implements
        Prioritizes Django settings, falls back to environment.
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
    def get(cls) -> "SomaBrainClient":
        """Get or create singleton instance.

        Thread-safe singleton pattern for connection pooling.
        Always returns an instance; public methods are no-ops when disabled.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_async(cls) -> "SomaBrainClient":
        """Get or create singleton instance (async version).

        Always returns an instance; public methods are no-ops when disabled.
        """
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def _ensure_client(self) -> Optional[httpx.AsyncClient]:
        """Ensure HTTP client is initialized."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; no client instantiated")
            return None
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
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
            path: API path (e.g., "/v1/memory/recall")
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
            LOGGER.debug("SomaBrain disabled; skipping _request %s", path)
            return {}

        breaker = get_circuit_breaker("somabrain_http", failure_threshold=5, reset_timeout=30)

        async def _do_request() -> Dict[str, Any]:
            client = await self._ensure_client()
            request_headers = headers or {}
            response = await client.request(method, path, json=json, params=params, headers=request_headers)
            response.raise_for_status()
            return response.json()

        try:
            return cast(Dict[str, Any], await breaker.call(_do_request))
        except CircuitBreakerError as e:
            LOGGER.error("SomaBrain circuit breaker OPEN", extra={"path": path, "error": str(e)})
            raise SomaClientError(
                f"SomaBrain unavailable (circuit open): {e}", status_code=503
            ) from e
        except httpx.HTTPStatusError as e:
            LOGGER.error(
                "SomaBrain HTTP error",
                extra={"path": path, "status": e.response.status_code},
            )
            raise SomaClientError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            LOGGER.error("SomaBrain connection error", extra={"path": path, "error": str(e)})
            raise SomaClientError(f"Connection error: {e}") from e

    # =========================================================================
    # MEMORY OPERATIONS
    # =========================================================================

    async def remember(
        self,
        payload: Optional[Dict[str, Any]] = None,
        *,
        tenant: Optional[str] = None,
        namespace: str = "wm",
        content: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        coord: Optional[str] = None,
        universe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store memory in SomaBrain.

        Args:
            payload: Memory payload with value, key, tags, importance, novelty
            tenant: Tenant ID
            namespace: Memory namespace (wm=working memory)

        Returns:
            Response with coordinate of stored memory

        VIBE Rule 1: NO BULLSHIT - Real API call to somabrain /memory/remember
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping remember")
            return {}

        effective_tenant = tenant_id or tenant or "default"
        payload = payload or {}
        if content is not None:
            payload = {
                **payload,
                "content": content,
                "user_id": user_id,
                "memory_type": memory_type,
                "metadata": metadata,
            }
        # Format for SomaBrain API: key, value (not payload)
        body = {
            "key": payload.get("key")
            or f"mem_{hashlib.md5(str(payload).encode()).hexdigest()[:16]}",
            "value": payload,
            "tenant": effective_tenant,
            "namespace": namespace,
        }

        # DIRECT MODE CHECK (Triad Compliant)
        if HAS_BRIDGE and BrainBridge is not None and BrainBridge.mode == "direct":
            try:
                # Use compliant BrainBridge
                resp = await BrainBridge.remember(
                    content=payload.get("content", ""),
                    tenant=tenant or "default",
                    namespace=namespace,
                    metadata=payload.get("metadata", {}),
                )
                return {
                    "status": "success",
                    "coordinate": resp.get("coordinate"),
                    "memory_id": resp.get("id"),
                }
            except Exception as e:
                LOGGER.error('Direct remember failed, falling back to HTTP: %s', e)
                pass

        if coord is not None:
            body["coord"] = coord
        if universe is not None:
            body["universe"] = universe
        return await self._request("POST", "/memory/remember", json=body)

    async def delete(
        self,
        coordinate: Any,
        *,
        tenant: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete memory by coordinate (alias for forget)."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping delete")
            return {}
        coord_str = coordinate if isinstance(coordinate, str) else json.dumps(coordinate)
        return await self.forget(coordinate=coord_str, tenant=tenant, tenant_id=tenant_id)

    async def migrate_export(
        self,
        include_wm: bool = False,
        wm_limit: int = 128,
    ) -> Dict[str, Any]:
        """Export memories for migration."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping migrate_export")
            return {}
        return await self._request(
            "GET",
            "/admin/migrate/export",
            params={"include_wm": str(include_wm), "wm_limit": wm_limit},
        )

    async def migrate_import(
        self,
        manifest: Dict[str, Any],
        memories: List[Dict[str, Any]],
        wm: Optional[List[Dict[str, Any]]] = None,
        replace: bool = False,
    ) -> Dict[str, Any]:
        """Import memories from migration."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping migrate_import")
            return {}
        body = {
            "manifest": manifest,
            "memories": memories,
            "wm": wm or [],
            "replace": replace,
        }
        return await self._request("POST", "/admin/migrate/import", json=body)

    async def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: Optional[str] = None,
        namespace: str = "wm",
        universe: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        limit: Optional[int] = None,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall memories from SomaBrain.

        Args:
            query: Search query
            top_k: Maximum results to return
            tenant: Tenant ID filter
            namespace: Memory namespace
            universe: Universe scope
            tags: Tag filters

        Returns:
            Response with memory results
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping recall")
            return []

        effective_tenant = tenant_id or tenant
        effective_limit = limit or top_k
        body: Dict[str, Any] = {
            "query": query,
            "top_k": effective_limit,
            "namespace": namespace,
        }
        if effective_tenant:
            body["tenant"] = effective_tenant
        if universe:
            body["universe"] = universe
        if tags:
            body["tags"] = tags
        if memory_type:
            body["memory_type"] = memory_type

        # DIRECT MODE CHECK (Triad Compliant)
        if HAS_BRIDGE and BrainBridge is not None and getattr(BrainBridge, "mode", None) == "direct":
            try:
                # Use compliant BrainBridge
                results = await BrainBridge.recall(query=query, top_k=top_k)

                # Transform to expected response format
                memories: List[Dict[str, Any]] = []
                for m in results:
                    memories.append(
                        {
                            "coordinate": m.get("coordinate", [0.0, 0.0, 0.0]),
                            "payload": m.get("payload", {}),
                            "score": m.get("score", 0.0),
                            "created_at": datetime.now(
                                timezone.utc
                            ).isoformat(),  # if missing
                        }
                    )
                return memories
            except Exception as e:
                LOGGER.error('Direct recall failed, falling back to HTTP: %s', e)
                pass

        result = await self._request("POST", "/memory/recall", json=body)
        if isinstance(result, list):
            return result
        return result.get("memories", [])

    async def forget(
        self,
        coordinate: Optional[str] = None,
        *,
        tenant: Optional[str] = None,
        memory_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete memory by coordinate.

        Args:
            coordinate: Memory coordinate to delete
            tenant: Tenant ID

        Returns:
            Deletion confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping forget")
            return {}

        effective_coordinate = coordinate if coordinate else memory_id
        effective_tenant = tenant_id or tenant
        body = {"coordinate": effective_coordinate}
        if effective_tenant:
            body["tenant"] = effective_tenant
        return await self._request("DELETE", "/memory/forget", json=body)

    # =========================================================================
    # CONTEXT OPERATIONS
    # =========================================================================

    async def context_evaluate(
        self,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate context for a conversation turn.

        Args:
            request: Context evaluation request with query, session_id, etc.

        Returns:
            Context evaluation response with memories and scores
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping context_evaluate")
            return {}
        return await self._request("POST", "/v1/context/evaluate", json=request)

    async def get_adaptation_state(
        self,
        tenant_id: str,
        persona_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get current adaptation state.

        Args:
            tenant_id: Tenant ID
            persona_id: Optional persona filter

        Returns:
            Adaptation state with weights, history, learning rate
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_adaptation_state")
            return {}
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
        """Reset adaptation state to defaults.

        Args:
            tenant_id: Tenant ID
            base_lr: Base learning rate override
            reset_history: Whether to clear feedback history

        Returns:
            Reset confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping adaptation_reset")
            return {}
        body: Dict[str, Any] = {"tenant": tenant_id, "reset_history": reset_history}
        if base_lr is not None:
            body["base_lr"] = base_lr
        return await self._request("POST", "/context/adaptation/reset", json=body)

    # =========================================================================
    # NEUROMODULATOR OPERATIONS
    # =========================================================================

    async def get_neuromodulators(
        self,
        tenant_id: str,
        persona_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get current neuromodulator state.

        Args:
            tenant_id: Tenant ID
            persona_id: Persona filter

        Returns:
            Neuromodulator levels (dopamine, serotonin, etc.)
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_neuromodulators")
            return {}
        params: Dict[str, Any] = {"tenant": tenant_id}
        if persona_id:
            params["persona"] = persona_id
        return await self._request("GET", "/neuromodulators", params=params)

    async def update_neuromodulators(
        self,
        tenant_id: str,
        persona_id: str,
        neuromodulators: Dict[str, float],
    ) -> Dict[str, Any]:
        """Update neuromodulator levels.

        Args:
            tenant_id: Tenant ID
            persona_id: Persona ID
            neuromodulators: New neuromodulator levels

        Returns:
            Update confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping update_neuromodulators")
            return {}
        body = {
            "tenant": tenant_id,
            "persona": persona_id,
            "neuromodulators": neuromodulators,
        }
        return await self._request("PUT", "/neuromodulators", json=body)

    # =========================================================================
    # PERSONA OPERATIONS
    # =========================================================================

    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """Get persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            Persona data
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_persona")
            return {}
        return await self._request("GET", f"/personas/{persona_id}")

    async def delete_persona(self, persona_id: str) -> Dict[str, Any]:
        """Delete persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            Deletion confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping delete_persona")
            return {}
        return await self._request("DELETE", f"/personas/{persona_id}")

    async def put_persona(
        self,
        persona_id: str,
        persona_data: Dict[str, Any],
        etag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update persona.

        Args:
            persona_id: Persona ID
            persona_data: Persona data
            etag: Optional ETag for optimistic concurrency

        Returns:
            Created/updated persona
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping put_persona")
            return {}
        req_headers = {"If-Match": etag} if etag else None
        return await self._request("PUT", f"/personas/{persona_id}", json=persona_data, headers=req_headers)

    # =========================================================================
    # COGNITIVE OPERATIONS
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
        """Execute a cognitive action.

        Args:
            task: Task description
            agent_id: Agent identifier
            input_text: Input text for the action
            context: Additional context
            mode: Execution mode (FULL, MINIMAL, LITE, ADMIN)
            universe: Universe scope
            session_id: Session ID

        Returns:
            Action response with results and salience
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping act")
            return {}
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

    # =========================================================================
    # SLEEP/LIFECYCLE OPERATIONS
    # =========================================================================

    async def brain_sleep_mode(
        self,
        target_state: str,
        *,
        ttl_seconds: Optional[int] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transition brain to sleep state.

        Args:
            target_state: One of "active", "light", "deep", "freeze"
            ttl_seconds: TTL for auto-revert
            trace_id: Trace ID for logging

        Returns:
            Transition confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping brain_sleep_mode")
            return {}
        valid_states = {"active", "light", "deep", "freeze"}
        if target_state not in valid_states:
            raise ValueError(f"Invalid sleep state: {target_state}. Must be one of {valid_states}")

        body: Dict[str, Any] = {"target_state": target_state}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if trace_id:
            body["trace_id"] = trace_id
        return await self._request("POST", "/brain/sleep", json=body)

    async def sleep_status(self) -> Dict[str, Any]:
        """Get current sleep status.

        Returns:
            Sleep status with current state and metrics
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping sleep_status")
            return {}
        return await self._request("GET", "/brain/sleep/status")

    async def micro_diag(self) -> Dict[str, Any]:
        """Get microcircuit diagnostics (admin mode).

        Returns:
            Diagnostic information
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping micro_diag")
            return {}
        return await self._request("GET", "/admin/micro/diag")

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def get_cognitive_state(self, agent_id: str) -> Dict[str, Any]:
        """Get cognitive state for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Cognitive state dict
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_cognitive_state")
            return {}
        return await self.get_adaptation_state(tenant_id=agent_id)

    async def update_cognitive_params(
        self, agent_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update cognitive parameters for an agent.

        Args:
            agent_id: Agent identifier
            params: Parameters to update

        Returns:
            Update confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping update_cognitive_params")
            return {}
        return await self._request("POST", f"/cognitive/params/{agent_id}", json=params)

    async def trigger_sleep_cycle(self, agent_id: str) -> Dict[str, Any]:
        """Trigger sleep cycle for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Sleep cycle confirmation
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping trigger_sleep_cycle")
            return {}
        return await self.brain_sleep_mode("deep", trace_id=agent_id)

    async def health_check(self) -> bool:
        """Check if SomaBrain is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping health_check")
            return False
        try:
            result = await self._request("GET", "/health")
            return result.get("status") == "ok" or result.get("ready", False)
        except SomaClientError:
            return False

    async def get_recent(
        self,
        *,
        tenant_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent memories.

        Args:
            tenant_id: Tenant ID filter
            limit: Maximum results to return

        Returns:
            List of recent memory records
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_recent")
            return []
        params: Dict[str, Any] = {"limit": limit}
        if tenant_id:
            params["tenant"] = tenant_id
        result = await self._request("GET", "/memory/recent", params=params)
        if isinstance(result, list):
            return result
        return result.get("memories", [])

    async def get_pending_count(
        self,
        *,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Get count of pending memories.

        Args:
            tenant_id: Tenant ID filter

        Returns:
            Number of pending memories
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_pending_count")
            return 0
        params: Dict[str, Any] = {}
        if tenant_id:
            params["tenant"] = tenant_id
        result = await self._request("GET", "/memory/pending", params=params)
        return result.get("count", 0)

    async def health(self) -> Dict[str, Any]:
        """Get health status from SomaBrain.

        Returns:
            Health status dict with status and optional details
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping health")
            return {"status": "disabled"}
        try:
            return await self._request("GET", "/health")
        except SomaClientError as e:
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # LEARNING OPERATIONS
    # =========================================================================

    async def get_weights(
        self,
        persona_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get current model/provider weights.

        Args:
            persona_id: Optional persona filter

        Returns:
            Weight configuration
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping get_weights")
            return {}
        params = {"persona": persona_id} if persona_id else None
        return await self._request("GET", "/weights", params=params)

    async def build_context(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build contextual augmentation for conversation.

        Args:
            session_id: Session ID
            messages: Recent messages (last 10 recommended)

        Returns:
            Additional context messages to prepend/append
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping build_context")
            return []
        body = {"session_id": session_id, "messages": messages[-10:]}
        result = await self._request("POST", "/context/build", json=body)
        if isinstance(result, list):
            return result
        return result.get("messages", [])

    # =========================================================================
    # CONSTITUTION / OPA OPERATIONS
    # =========================================================================

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop for sync contexts."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.new_event_loop()

    async def constitution_version(self) -> Dict[str, Any]:
        """Get current constitution version."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping constitution_version")
            return {}
        return await self._request("GET", "/constitution/version")

    async def constitution_validate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Validate a constitution document."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping constitution_validate")
            return {}
        return await self._request("POST", "/constitution/validate", json=dict(payload))

    async def constitution_load(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Load a constitution document."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping constitution_load")
            return {}
        return await self._request("POST", "/constitution/load", json=dict(payload))

    async def update_opa_policy(self) -> Dict[str, Any]:
        """Regenerate OPA policy from current constitution."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping update_opa_policy")
            return {}
        return await self._request("POST", "/opa/policy/update")

    async def opa_policy(self) -> Dict[str, Any]:
        """Get current OPA policy."""
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping opa_policy")
            return {}
        return await self._request("GET", "/opa/policy")

    async def context_feedback(self, **kwargs: Any) -> Dict[str, Any]:
        """Send contextual feedback to SomaBrain for learning.

        Returns:
            Feedback response dict.
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping context_feedback")
            return {}
        return await self._request("POST", "/context/feedback", json=dict(kwargs))

    async def publish_reward(
        self,
        session_id: str,
        signal: str,
        value: float,
        meta: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Publish reward/feedback signal.

        Args:
            session_id: Session ID
            signal: Signal type
            value: Reward value
            meta: Additional metadata

        Returns:
            True if published successfully
        """
        if not self._base_url:
            LOGGER.debug("SomaBrain disabled; skipping publish_reward")
            return False
        body = {
            "session_id": session_id,
            "signal": signal,
            "value": value,
            "meta": meta or {},
        }
        result = await self._request("POST", "/learning/reward", json=body)
        return result.get("ok", False)


# Backwards compatibility aliases
SomaBrainError = SomaClientError


def get_somabrain_client() -> SomaBrainClient:
    """Get SomaBrain client singleton (synchronous helper).

    Returns:
        SomaBrainClient instance (public methods are no-ops when disabled).
    """
    return SomaBrainClient.get()


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaMemoryRecord",
    "get_somabrain_client",
]
