"""SomaBrain Client - Chat / cognitive operations

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
from typing import Any, Dict, List, Mapping, Optional

from admin.core.somabrain_memory import _SomaBrainMemoryClient


class _SomaBrainChatClient(_SomaBrainMemoryClient):
    """Chat, cognitive, lifecycle, and policy operations for the SomaBrain client."""

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
        return await self._request("GET", f"/personas/{persona_id}")

    async def delete_persona(self, persona_id: str) -> Dict[str, Any]:
        """Delete persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            Deletion confirmation
        """
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
        return await self._request("GET", "/brain/sleep/status")

    async def micro_diag(self) -> Dict[str, Any]:
        """Get microcircuit diagnostics (admin mode).

        Returns:
            Diagnostic information
        """
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
        return await self._request("POST", f"/cognitive/params/{agent_id}", json=params)

    async def trigger_sleep_cycle(self, agent_id: str) -> Dict[str, Any]:
        """Trigger sleep cycle for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Sleep cycle confirmation
        """
        return await self.brain_sleep_mode("deep", trace_id=agent_id)

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
        return await self._request("GET", "/constitution/version")

    async def constitution_validate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Validate a constitution document."""
        return await self._request("POST", "/constitution/validate", json=dict(payload))

    async def constitution_load(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Load a constitution document."""
        return await self._request("POST", "/constitution/load", json=dict(payload))

    async def update_opa_policy(self) -> Dict[str, Any]:
        """Regenerate OPA policy from current constitution."""
        return await self._request("POST", "/opa/policy/update")

    async def opa_policy(self) -> Dict[str, Any]:
        """Get current OPA policy."""
        return await self._request("GET", "/opa/policy")

    async def context_feedback(self, **kwargs: Any) -> Dict[str, Any]:
        """Send contextual feedback to SomaBrain for learning.

        Returns:
            Feedback response dict.
        """
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
        body = {
            "session_id": session_id,
            "signal": signal,
            "value": value,
            "meta": meta or {},
        }
        result = await self._request("POST", "/learning/reward", json=body)
        return result.get("ok", False)
