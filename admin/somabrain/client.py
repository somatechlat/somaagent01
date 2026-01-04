"""SomaBrain HTTP Client.


Uses REAL endpoints from SomaBrain OpenAPI spec (localhost:9696).

Endpoints based on http://localhost:9696/api/openapi.json:
- POST /api/cognitive/act - Execute action
- POST /api/memory/recall - Recall memories
- POST /api/memory/remember/remember - Store memory
- GET /api/neuromod/state - Get neuromodulator state
- POST /api/neuromod/adjust - Adjust neuromodulators
- GET /api/sleep/state - Get sleep state
- POST /api/sleep/brain/mode - Set brain sleep mode
- GET /api/context/adaptation/state - Get adaptation state
- POST /api/context/adaptation/reset - Reset adaptation
- GET /api/health/health - Health check
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class SomaBrainError(Exception):
    """Exception for SomaBrain API errors."""

    pass


class SomaBrainClient:
    """Async HTTP client for SomaBrain API.

    REAL SomaBrain calls based on OpenAPI spec.
    No mock data - uses actual endpoints.
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        timeout: float = 30.0,
    ):
        """Initialize the instance."""

        self.base_url = base_url or getattr(settings, "SOMABRAIN_BASE_URL", "http://localhost:9696")
        self.api_key = api_key or getattr(settings, "SOMABRAIN_API_KEY", "")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # HEALTH
    # =========================================================================

    async def health_check(self) -> dict:
        """GET /api/health/ - Main health endpoint with component status."""
        client = await self._get_client()
        try:
            response = await client.get("/api/health/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain health check failed: {e}")
            raise SomaBrainError(f"Health check failed: {e}")

    # =========================================================================
    # COGNITIVE
    # =========================================================================

    async def act(
        self,
        task: str,
        top_k: int = 3,
        universe: str = None,
    ) -> dict:
        """POST /api/cognitive/act - Execute action/task.

        Returns:
            ActResponse with task, results, plan, plan_universe
        """
        client = await self._get_client()
        payload = {
            "task": task,
            "top_k": top_k,
        }
        if universe:
            payload["universe"] = universe

        try:
            response = await client.post("/api/cognitive/act", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain act failed: {e}")
            raise SomaBrainError(f"Act failed: {e}")

    async def plan_suggest(
        self,
        task_key: str,
        max_steps: int = None,
        rel_types: list = None,
        universe: str = None,
    ) -> dict:
        """POST /api/cognitive/plan/suggest - Suggest action plan."""
        client = await self._get_client()
        payload = {"task_key": task_key}
        if max_steps:
            payload["max_steps"] = max_steps
        if rel_types:
            payload["rel_types"] = rel_types
        if universe:
            payload["universe"] = universe

        try:
            response = await client.post("/api/cognitive/plan/suggest", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain plan_suggest failed: {e}")
            raise SomaBrainError(f"Plan suggest failed: {e}")

    async def set_personality(self, traits: dict) -> dict:
        """POST /api/cognitive/personality - Set personality traits."""
        client = await self._get_client()
        try:
            response = await client.post("/api/cognitive/personality", json={"traits": traits})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain set_personality failed: {e}")
            raise SomaBrainError(f"Set personality failed: {e}")

    # =========================================================================
    # MEMORY
    # =========================================================================

    async def remember(
        self,
        tenant: str,
        namespace: str,
        key: str,
        value: dict,
        meta: dict = None,
        importance: float = None,
        novelty: float = None,
        ttl_seconds: int = None,
    ) -> dict:
        """POST /api/memory/remember/remember - Store a memory.

        Returns:
            MemoryWriteResponse with ok, tenant, namespace, coordinate, etc.
        """
        client = await self._get_client()
        payload = {
            "tenant": tenant,
            "namespace": namespace,
            "key": key,
            "value": value,
        }
        if meta:
            payload["meta"] = meta
        if importance is not None:
            payload["importance"] = importance
        if novelty is not None:
            payload["novelty"] = novelty
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds

        try:
            response = await client.post("/api/memory/remember/remember", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain remember failed: {e}")
            raise SomaBrainError(f"Remember failed: {e}")

    async def remember_batch(
        self,
        tenant: str,
        namespace: str,
        items: list,
        universe: str = None,
    ) -> dict:
        """POST /api/memory/remember/remember/batch - Store multiple memories."""
        client = await self._get_client()
        payload = {
            "tenant": tenant,
            "namespace": namespace,
            "items": items,
        }
        if universe:
            payload["universe"] = universe

        try:
            response = await client.post("/api/memory/remember/remember/batch", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain remember_batch failed: {e}")
            raise SomaBrainError(f"Remember batch failed: {e}")

    async def recall(self, payload: dict) -> dict:
        """POST /api/memory/recall - Recall memories via retrieval pipeline."""
        client = await self._get_client()
        try:
            response = await client.post("/api/memory/recall", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain recall failed: {e}")
            raise SomaBrainError(f"Recall failed: {e}")

    async def memory_metrics(self, tenant: str = None, namespace: str = None) -> dict:
        """GET /api/memory/metrics - Get memory metrics."""
        client = await self._get_client()
        params = {}
        if tenant:
            params["tenant"] = tenant
        if namespace:
            params["namespace"] = namespace

        try:
            response = await client.get("/api/memory/metrics", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain memory_metrics failed: {e}")
            raise SomaBrainError(f"Memory metrics failed: {e}")

    # =========================================================================
    # NEUROMODULATORS
    # =========================================================================

    async def get_neuromod_state(self) -> dict:
        """GET /api/neuromod/state - Get neuromodulator state."""
        client = await self._get_client()
        try:
            response = await client.get("/api/neuromod/state")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_neuromod_state failed: {e}")
            raise SomaBrainError(f"Get neuromod state failed: {e}")

    async def adjust_neuromod(
        self,
        dopamine: float = None,
        serotonin: float = None,
        noradrenaline: float = None,
        acetylcholine: float = None,
    ) -> dict:
        """POST /api/neuromod/adjust - Adjust neuromodulator values."""
        client = await self._get_client()
        payload = {}
        if dopamine is not None:
            payload["dopamine"] = dopamine
        if serotonin is not None:
            payload["serotonin"] = serotonin
        if noradrenaline is not None:
            payload["noradrenaline"] = noradrenaline
        if acetylcholine is not None:
            payload["acetylcholine"] = acetylcholine

        try:
            response = await client.post("/api/neuromod/adjust", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain adjust_neuromod failed: {e}")
            raise SomaBrainError(f"Adjust neuromod failed: {e}")

    # =========================================================================
    # SLEEP
    # =========================================================================

    async def get_sleep_state(self) -> dict:
        """GET /api/sleep/state - Get current sleep state."""
        client = await self._get_client()
        try:
            response = await client.get("/api/sleep/state")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_sleep_state failed: {e}")
            raise SomaBrainError(f"Get sleep state failed: {e}")

    async def set_sleep_state(self, payload: dict) -> dict:
        """POST /api/sleep/state - Set sleep state (generic)."""
        client = await self._get_client()
        try:
            response = await client.post("/api/sleep/state", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain set_sleep_state failed: {e}")
            raise SomaBrainError(f"Set sleep state failed: {e}")

    async def brain_sleep_mode(self, payload: dict) -> dict:
        """POST /api/sleep/brain/mode - Cognitive-level sleep state transition."""
        client = await self._get_client()
        try:
            response = await client.post("/api/sleep/brain/mode", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain brain_sleep_mode failed: {e}")
            raise SomaBrainError(f"Brain sleep mode failed: {e}")

    async def sleep_transition(self, payload: dict) -> dict:
        """POST /api/sleep/transition - Transition based on trigger."""
        client = await self._get_client()
        try:
            response = await client.post("/api/sleep/transition", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain sleep_transition failed: {e}")
            raise SomaBrainError(f"Sleep transition failed: {e}")

    # =========================================================================
    # CONTEXT / ADAPTATION
    # =========================================================================

    async def get_adaptation_state(self, tenant_id: str = None) -> dict:
        """GET /api/context/adaptation/state - Get adaptation weights."""
        client = await self._get_client()
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id

        try:
            response = await client.get("/api/context/adaptation/state", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_adaptation_state failed: {e}")
            raise SomaBrainError(f"Get adaptation state failed: {e}")

    async def adaptation_reset(self, payload: dict) -> dict:
        """POST /api/context/adaptation/reset - Reset adaptation to defaults."""
        client = await self._get_client()
        try:
            response = await client.post(
                "/api/context/adaptation/reset", params={"payload": payload}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain adaptation_reset failed: {e}")
            raise SomaBrainError(f"Adaptation reset failed: {e}")

    async def context_evaluate(self, payload: dict) -> dict:
        """POST /api/context/evaluate - Evaluate context and return prompt with memories."""
        client = await self._get_client()
        try:
            response = await client.post("/api/context/evaluate", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain context_evaluate failed: {e}")
            raise SomaBrainError(f"Context evaluate failed: {e}")

    async def context_feedback(self, payload: dict) -> dict:
        """POST /api/context/feedback - Record feedback for learning adaptation."""
        client = await self._get_client()
        try:
            response = await client.post("/api/context/feedback", params={"payload": payload})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain context_feedback failed: {e}")
            raise SomaBrainError(f"Context feedback failed: {e}")

    # =========================================================================
    # CONFIG
    # =========================================================================

    async def get_config(self) -> dict:
        """GET /api/config/ - Get current configuration for tenant."""
        client = await self._get_client()
        try:
            response = await client.get("/api/config/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_config failed: {e}")
            raise SomaBrainError(f"Get config failed: {e}")


# =========================================================================
# SINGLETON
# =========================================================================

_client: Optional[SomaBrainClient] = None


def get_somabrain_client() -> SomaBrainClient:
    """Get singleton SomaBrain client instance."""
    global _client
    if _client is None:
        _client = SomaBrainClient()
    return _client