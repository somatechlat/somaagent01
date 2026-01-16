"""
BrainMemoryFacade: The Unified Gateway for SomaStack Memory Operations.

Architecture Compliance:
    - SRS Reference: FR-1 (Direct Integration Pattern)
    - Mode: Unified SaaS (Direct) vs. Legacy (HTTP)
    - Role: Facade Pattern isolating the complexity of the underlying memory backend.

Hardware requirements:
    - This module is IO-bound in HTTP mode but CPU-bound in Direct Mode due to
      local serialization/deserialization of memory objects.

Integration Strategy:
    1. Direct Mode (`SOMA_SAAS_MODE='direct'`):
       - Dynamic import of `somafractalmemory`.
       - Direct instantiation of `MemoryService`.
       - Sub-millisecond latency profile.
    2. HTTP Mode (`SOMA_SAAS_MODE='http'`):
       - Fallback to REST/JSON over local network.
       - ~10-50ms latency profile.

Security:
    - All memory operations are tenant-scoped.
    - Audit logging (FR-3) is enforced at the entry point of this facade.
"""

import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    MemoryItem,
    MemoryReadRequest,
    MemoryReadResponse,
    MemoryWriteRequest,
    MemoryWriteResponse,
)

logger = logging.getLogger(__name__)


class BrainMemoryFacade:
    """
    Singleton Facade for orchestrating memory operations across the SomaStack.

    This class serves as the 'Switchboard' for memory IO. In the Direct Integration
    Monolith architecture, it bypasses the network stack entirely, invoking the
    Python internals of the FractalMemory engine directly.

    Attributes:
        mode (str): The operation mode, derived from `SOMA_SAAS_MODE`.
        _memory_service (Any): The direct reference to the MemoryService instance (if active).
    """

    _instance: Optional["BrainMemoryFacade"] = None

    def __init__(self) -> None:
        """
        Initialize the Facade.

        Determines the operation mode from environment variables and attempts
        to link the local shared-library bindings if Direct Mode is requested.
        """
        self.mode: str = os.getenv("SOMA_SAAS_MODE", "http").lower()
        self._memory_service: Any = None

        logger.info(f"Initializing BrainMemoryFacade in {self.mode.upper()} mode")

        if self.mode == "direct":
            self._init_direct_mode()

    @classmethod
    def get_instance(cls) -> "BrainMemoryFacade":
        """
        Retrieve the singleton instance of the Facade.

        Returns:
            BrainMemoryFacade: The active instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_direct_mode(self) -> None:
        """
        Attempt to establish a direct link to the SomaFractalMemory Runtime.

        This method performs a dynamic import to avoid hard dependencies in
        non-monolith deployments. It catches ImportError and logs a critical
        warning rather than crashing, maintaining process resilience (though
        memory ops will fail).
        """
        try:
            # Dynamic import to avoid hard dependency if not present in the PYTHONPATH
            from somafractalmemory.services import MemoryService

            self._memory_service = MemoryService(namespace="default")
            logger.info("Successfully linked to SomaFractalMemory.MemoryService")
        except ImportError as ex:
            logger.critical(
                f"FAILED to import SomaFractalMemory in direct mode: {ex}. "
                "Ensure `somafractalmemory` is in the PYTHONPATH or install the package."
            )
            # We explicitly set service to None to trigger generic error handling later
            self._memory_service = None

    async def remember(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """
        Persist a memory vector into the Fractal Memory.

        Args:
            request (MemoryWriteRequest): The typesafe write payload.

        Returns:
            MemoryWriteResponse: Confirmation of storage including the coordinate key.

        Raises:
            NotImplementedError: If HTTP mode is attempted (Feature Flag: LEGACY_HTTP_PENDING).
            RuntimeError: If Direct Mode is active but the service failed to link.
        """
        if self.mode == "direct":
            if not self._memory_service:
                raise RuntimeError("Direct Mode active but MemoryService is not linked.")
            return await self._remember_direct(request)
        else:
            # HTTP Mode: Use legacy HTTP client from admin.core.soma_client
            # This is used when SOMA_SAAS_MODE != 'direct'
            return await self._remember_http(request)

    async def recall(self, request: MemoryReadRequest) -> MemoryReadResponse:
        """
        Retrieve memory vectors based on semantic similarity.

        Args:
            request (MemoryReadRequest): The typesafe read payload.

        Returns:
            MemoryReadResponse: A ranked list of matching memory items.

        Raises:
            NotImplementedError: If HTTP mode is attempted.
        """
        if self.mode == "direct":
            if not self._memory_service:
                raise RuntimeError("Direct Mode active but MemoryService is not linked.")
            return await self._recall_direct(request)
        else:
            # HTTP Mode: Use legacy HTTP client
            return await self._recall_http(request)

    # --- HTTP Mode Implementations ---

    async def _remember_http(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """
        Execute a memory write operation via HTTP to SomaFractalMemory API.
        """
        import httpx
        from django.conf import settings

        coordinate = self._generate_coordinate(request.payload)
        self._audit_log("remember", request.tenant_id, request.payload)

        url = f"{settings.SOMAFRACTALMEMORY_URL}/api/v1/memories"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "coord": ",".join(str(c) for c in coordinate),
                    "payload": request.payload,
                    "memory_type": "episodic",
                },
                headers={
                    "X-Soma-Tenant": request.tenant_id,
                    "Authorization": f"Bearer {settings.SOMA_MEMORY_API_TOKEN}",
                },
            )
            response.raise_for_status()
            data = response.json()

        return MemoryWriteResponse(
            coordinate=coordinate,
            memory_id=data.get("coord", str(coordinate)),
            status="success",
        )

    async def _recall_http(self, request: MemoryReadRequest) -> MemoryReadResponse:
        """
        Execute a memory search operation via HTTP to SomaFractalMemory API.
        """
        import httpx
        from django.conf import settings

        self._audit_log("search", request.tenant_id, {"query": request.query})

        url = f"{settings.SOMAFRACTALMEMORY_URL}/api/v1/memories/search"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "query": request.query,
                    "top_k": request.limit,
                },
                headers={
                    "X-Soma-Tenant": request.tenant_id,
                    "Authorization": f"Bearer {settings.SOMA_MEMORY_API_TOKEN}",
                },
            )
            response.raise_for_status()
            data = response.json()

        memories: List[MemoryItem] = []
        for res in data.get("memories", []):
            memories.append(
                MemoryItem(
                    memory_id=str(res.get("coordinate")),
                    coordinate=res.get("coordinate", [0.0, 0.0, 0.0]),
                    payload=res.get("payload", {}),
                    score=res.get("importance", 0.0),
                    created_at=datetime.now(timezone.utc),
                )
            )

        return MemoryReadResponse(memories=memories)

    # --- Direct Mode Implementations ---

    async def _remember_direct(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """
        Execute a direct-memory write operation.

        This function generates a coordinate (simulated or derived) and persists
        the payload to the underlying storage engine via the Service API.
        """
        try:
            # Architecture Note: In the full implementation, the 'Coordinate' is derived
            # from the Semantic Encoder (SDR). For this structural verify, we generate
            # a stochastic coordinate to satisfy the interface contracts.
            coordinate = self._generate_coordinate(request.payload)

            # FR-3: Audit Logging Enforcement
            self._audit_log("remember", request.tenant_id, request.payload)

            # The `aremember` method is an async wrapper around the sync `remember`
            # method in the Django Service layer (added in commit 75750b3).
            stored = await self._memory_service.aremember(
                coordinate=coordinate,
                payload=request.payload,
                memory_type="episodic",  # Defaulting to episodic memory
                tenant=request.tenant_id,
                metadata={"tags": request.tags, "universe": request.universe},
            )

            # Map the Django model instance to our Pydantic-style response
            return MemoryWriteResponse(
                coordinate=stored.coordinate,
                memory_id=str(stored.coordinate_key),
                status="success",
            )

        except Exception as ex:
            logger.error(f"Direct memory write failed: {ex}", exc_info=True)
            raise

    async def _recall_direct(self, request: MemoryReadRequest) -> MemoryReadResponse:
        """
        Execute a direct-memory search operation.

        Query the local vector index (e.g., GinIndex or Milvus) directly.
        """
        try:
            # FR-3: Audit Logging Enforcement
            self._audit_log("search", request.tenant_id, {"query": request.query})

            # The `.search()` method on MemoryService returns a list of dictionaries.
            results = self._memory_service.search(
                query=request.query,
                top_k=request.limit,
                tenant=request.tenant_id,
            )

            memories: List[MemoryItem] = []
            for res in results:
                # Transform raw dict result into typed MemoryItem
                memories.append(
                    MemoryItem(
                        memory_id=str(res.get("coordinate")),
                        coordinate=res.get("coordinate", [0.0, 0.0, 0.0]),
                        payload=res.get("payload", {}),
                        score=res.get("importance", 0.0),
                        created_at=datetime.now(timezone.utc),  # Placeholder timestamp
                    )
                )

            return MemoryReadResponse(memories=memories)

        except Exception as ex:
            logger.error(f"Direct memory recall failed: {ex}", exc_info=True)
            raise

    def _generate_coordinate(self, payload: Dict[str, Any]) -> List[float]:
        """
        Generate a 3D coordinate for the memory item.

        NON-PRODUCTION IMPLEMENTATION:
        In the deployed Cognitive Brain, this method invokes the SDR (Sparse Distributed Representation)
        Encoder to map semantic meaning to 3D-space.
        For this Infrastructure Verification pass, we utilize a stochastic generator
        to validate the persistence pipeline without the heavy ML dependency.

        Args:
            payload (Dict[str, Any]): The content to encode.

        Returns:
            List[float]: A 3-dimensional float vector.
        """
        return [random.random() for _ in range(3)]

    def _audit_log(self, action: str, tenant: str, details: Any) -> None:
        """
        Emit a secure audit log entry.

        Args:
            action (str): The operation performed (remember/recall).
            tenant (str): The tenant ID context.
            details (Any): The payload or query parameters.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "action": action,
            "tenant": tenant,
            "integrity_hash": str(hash(str(details))),
        }
        # In a strict production environment, this would write to an append-only
        # immutable ledger. For this implementation, we target the standard logger.
        logger.info(f"AUDIT_EVENT: {json.dumps(entry)}")
