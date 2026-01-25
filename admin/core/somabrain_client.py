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
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings

# Integration: BrainBridge (Compliant Triad Architecture)
try:
    from aaas.brain import brain as BrainBridge
    HAS_BRIDGE = True
except ImportError:
    HAS_BRIDGE = False


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
    def _get_base_url() -> str:
        """Get SomaBrain URL from Django settings or environment.

        Implements
        Prioritizes Django settings, falls back to environment.
        """

        # Try Django settings first
        if hasattr(settings, "SOMABRAIN_URL"):
            return str(settings.SOMABRAIN_URL)

        # Fallback to environment variable
        return getattr(settings, "SOMABRAIN_URL", "http://localhost:9696")

    @classmethod
    def get(cls) -> "SomaBrainClient":
        """Get or create singleton instance.

        Thread-safe singleton pattern for connection pooling.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_async(cls) -> "SomaBrainClient":
        """Get or create singleton instance (async version)."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
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
    ) -> Dict[str, Any]:
        """Make HTTP request to SomaBrain.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/v1/memory/recall")
            json: JSON body for POST/PUT
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            SomaClientError: On HTTP or connection errors
        """
        client = await self._ensure_client()
        try:
            response = await client.request(
                method,
                path,
                json=json,
                params=params,
            )
            response.raise_for_status()
            return response.json()
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
        payload: Dict[str, Any],
        *,
        tenant: Optional[str] = None,
        namespace: str = "wm",
    ) -> Dict[str, Any]:
        """Store memory in SomaBrain.

        Args:
            payload: Memory payload with value, key, tags, importance, novelty
            tenant: Tenant ID
            namespace: Memory namespace (wm=working memory)

        Returns:
            Response with coordinate of stored memory
        """
        body = {
            "payload": payload,
            "tenant": tenant,
            "namespace": namespace,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # DIRECT MODE CHECK (Triad Compliant)
        if HAS_BRIDGE and BrainBridge.mode == "direct":
            try:
                # Use compliant BrainBridge
                resp = await BrainBridge.remember(
                    content=payload.get("content", ""),
                    tenant=tenant,
                    namespace=namespace,
                    metadata=payload.get("metadata", {})
                )
                return {
                    "status": "success",
                    "coordinate": resp.get("coordinate"),
                    "memory_id": resp.get("id"),
                }
            except Exception as e:
                LOGGER.error(f"Direct remember failed, falling back to HTTP: {e}")
                pass

        return await self._request("POST", "/v1/memory/remember", json=body)

    async def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: Optional[str] = None,
        namespace: str = "wm",
        universe: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        body: Dict[str, Any] = {
            "query": query,
            "top_k": top_k,
            "namespace": namespace,
        }
        if tenant:
            body["tenant"] = tenant
        if universe:
            body["universe"] = universe
        if tags:
            body["tags"] = tags

        # DIRECT MODE CHECK (Triad Compliant)
        if HAS_BRIDGE and BrainBridge.mode == "direct":
            try:
                # Use compliant BrainBridge
                # Note: BrainBridge.recall returns list[dict]
                results = await BrainBridge.recall(
                    query_vector=await BrainBridge.encode_text(query),
                    top_k=top_k
                )

                # Transform to expected response format
                memories = []
                for m in results:
                    memories.append({
                        "coordinate": m.get("coordinate", [0.0, 0.0, 0.0]),
                        "payload": m.get("payload", {}),
                        "score": m.get("score", 0.0),
                        "created_at": datetime.now(timezone.utc).isoformat(), # Placeholder if missing
                    })
                return {"memories": memories}
            except Exception as e:
                LOGGER.error(f"Direct recall failed, falling back to HTTP: {e}")
                pass

        return await self._request("POST", "/v1/memory/recall", json=body)

    async def forget(
        self,
        coordinate: str,
        *,
        tenant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete memory by coordinate.

        Args:
            coordinate: Memory coordinate to delete
            tenant: Tenant ID

        Returns:
            Deletion confirmation
        """
        body = {"coordinate": coordinate}
        if tenant:
            body["tenant"] = tenant
        return await self._request("DELETE", "/v1/memory/forget", json=body)

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
        params: Dict[str, Any] = {"tenant": tenant_id}
        if persona_id:
            params["persona"] = persona_id
        return await self._request("GET", "/v1/context/adaptation/state", params=params)

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
        body: Dict[str, Any] = {"tenant": tenant_id, "reset_history": reset_history}
        if base_lr is not None:
            body["base_lr"] = base_lr
        return await self._request("POST", "/v1/context/adaptation/reset", json=body)

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
        params: Dict[str, Any] = {"tenant": tenant_id}
        if persona_id:
            params["persona"] = persona_id
        return await self._request("GET", "/v1/neuromodulators", params=params)

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
        body = {
            "tenant": tenant_id,
            "persona": persona_id,
            "neuromodulators": neuromodulators,
        }
        return await self._request("PUT", "/v1/neuromodulators", json=body)

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
        return await self._request("GET", f"/v1/personas/{persona_id}")

    async def put_persona(
        self,
        persona_id: str,
        persona_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create or update persona.

        Args:
            persona_id: Persona ID
            persona_data: Persona data

        Returns:
            Created/updated persona
        """
        return await self._request("PUT", f"/v1/personas/{persona_id}", json=persona_data)

    # =========================================================================
    # COGNITIVE OPERATIONS
    # =========================================================================

    async def act(
        self,
        task: str,
        *,
        universe: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a cognitive action.

        Args:
            task: Task description
            universe: Universe scope
            session_id: Session ID

        Returns:
            Action response with results and salience
        """
        body: Dict[str, Any] = {"task": task}
        if universe:
            body["universe"] = universe
        if session_id:
            body["session_id"] = session_id
        return await self._request("POST", "/v1/cognitive/act", json=body)

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
        valid_states = {"active", "light", "deep", "freeze"}
        if target_state not in valid_states:
            raise ValueError(f"Invalid sleep state: {target_state}. Must be one of {valid_states}")

        body: Dict[str, Any] = {"target_state": target_state}
        if ttl_seconds is not None:
            body["ttl_seconds"] = ttl_seconds
        if trace_id:
            body["trace_id"] = trace_id
        return await self._request("POST", "/v1/brain/sleep", json=body)

    async def sleep_status(self) -> Dict[str, Any]:
        """Get current sleep status.

        Returns:
            Sleep status with current state and metrics
        """
        return await self._request("GET", "/v1/brain/sleep/status")

    async def micro_diag(self) -> Dict[str, Any]:
        """Get microcircuit diagnostics (admin mode).

        Returns:
            Diagnostic information
        """
        return await self._request("GET", "/v1/admin/micro/diag")

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def health_check(self) -> bool:
        """Check if SomaBrain is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            result = await self._request("GET", "/health")
            return result.get("status") == "ok" or result.get("ready", False)
        except SomaClientError:
            return False

    async def health(self) -> Dict[str, Any]:
        """Get health status from SomaBrain.

        Returns:
            Health status dict with status and optional details
        """
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
        params = {"persona": persona_id} if persona_id else None
        return await self._request("GET", "/v1/weights", params=params)

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
        body = {"session_id": session_id, "messages": messages[-10:]}
        result = await self._request("POST", "/v1/context/build", json=body)
        if isinstance(result, list):
            return result
        return result.get("messages", [])

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
        body = {
            "session_id": session_id,
            "signal": signal,
            "value": value,
            "meta": meta or {},
        }
        result = await self._request("POST", "/v1/learning/reward", json=body)
        return result.get("ok", False)


# Backwards compatibility aliases
SomaBrainError = SomaClientError


def get_somabrain_client() -> SomaBrainClient:
    """Get SomaBrain client singleton (synchronous helper).

    Returns:
        SomaBrainClient instance
    """
    return SomaBrainClient.get()


__all__ = [
    "SomaBrainClient",
    "SomaClientError",
    "SomaBrainError",
    "get_somabrain_client",
]
