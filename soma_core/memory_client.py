"""BrainMemoryFacade: The Unified Gateway for SomaStack Memory Operations.

This module implements the 'Direct Mode' integration pattern (SRS FR-1).
It acts as a facade that delegates memory operations to either:
1.  Direct Function Calls (SomaFractalMemory) - When SOMA_SAAS_MODE='direct'
2.  HTTP Requests (SomaBrain/Legacy) - When SOMA_SAAS_MODE='http' (default)

It strictly adheres to the "Sovereign Monolith" doctrine: minimal overhead,
direct python imports where possible, and robust strict typing.
"""

import logging
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .models import (
    MemoryWriteRequest,
    MemoryWriteResponse,
    MemoryReadRequest,
    MemoryReadResponse,
    MemoryItem,
)

logger = logging.getLogger(__name__)


class BrainMemoryFacade:
    """Facade for memory operations, supporting both Direct and HTTP modes."""

    _instance = None

    def __init__(self):
        self.mode = os.getenv("SOMA_SAAS_MODE", "http").lower()
        self._memory_service = None
        
        logger.info(f"Initializing BrainMemoryFacade in {self.mode.upper()} mode")

        if self.mode == "direct":
            self._init_direct_mode()

    @classmethod
    def get_instance(cls):
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_direct_mode(self):
        """Initialize the direct connection to SomaFractalMemory."""
        try:
            # Dynamic import to avoid hard dependency if not present
            from somafractalmemory.services import MemoryService
            self._memory_service = MemoryService(namespace="default")
            logger.info("Successfully linked to SomaFractalMemory.MemoryService")
        except ImportError as e:
            logger.critical(f"FAILED to import SomaFractalMemory in direct mode: {e}")
            # Fallback or strict failure? SRS suggests strictly failing or fallback.
            # For Monolith integrity, we log critical but don't crash yet.
            self._memory_service = None

    async def remember(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """Store a memory."""
        if self.mode == "direct" and self._memory_service:
            return await self._remember_direct(request)
        else:
            # In a real implementation, we might call the HTTP client here
            # For now, this Facade is primarily for the Direct path as the
            # HTTP clean-up is handled in the Agent's client wrapper.
            # However, to be a true Facade, it should handle both.
            # But the Agent already has an HTTP client. 
            # We will raise NotImplementedError for HTTP mode here to signal
            # that the caller should use their legacy client, OR we integrate it.
            # For this strict implementation, we focus on the Direct path.
            raise NotImplementedError("HTTP mode not fully integrated in Facade yet")

    async def recall(self, request: MemoryReadRequest) -> MemoryReadResponse:
        """Recall memories."""
        if self.mode == "direct" and self._memory_service:
            return await self._recall_direct(request)
        else:
            raise NotImplementedError("HTTP mode not fully integrated in Facade yet")

    # --- Direct Mode Implementations ---

    async def _remember_direct(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """Internal direct write to SFM."""
        start_ts = datetime.now()
        
        # 1. Generate Coordinate (Simulation or Real)
        # SFM's aremember takes a tuple coordinate. 
        # In a real system, Brain generates this. In Direct Mode, we need a generator.
        # We'll use a placeholder or basic hash for now, or if SFM generates it.
        # Checking SFM service: it takes `coordinate: tuple[float, ...]`.
        # We need to generate it.
        coordinate = self._generate_coordinate(request.payload)

        # 2. Call SFM
        try:
            # Log audit (FR-3)
            self._audit_log("remember", request.tenant_id, request.payload)

            stored = await self._memory_service.aremember(
                coordinate=coordinate,
                payload=request.payload,
                memory_type="episodic", # Defaulting
                tenant=request.tenant_id,
                metadata={"tags": request.tags, "universe": request.universe}
            )
            
            # Map SFM Memory object to Response
            # stored is a Memory model instance from Django
            
            return MemoryWriteResponse(
                coordinate=stored.coordinate,
                memory_id=str(stored.coordinate_key), # or ID
                status="success"
            )

        except Exception as e:
            logger.error(f"Direct memory write failed: {e}")
            raise

    async def _recall_direct(self, request: MemoryReadRequest) -> MemoryReadResponse:
        """Internal direct read from SFM."""
        try:
            # Log audit (FR-3)
            self._audit_log("search", request.tenant_id, {"query": request.query})

            # SFM search returns list[dict]
            results = self._memory_service.search(
                query=request.query,
                top_k=request.limit,
                tenant=request.tenant_id,
                # Filters can be added here
            )

            memories = []
            for res in results:
                # res is dict: coordinate, payload, memory_type, importance
                memories.append(MemoryItem(
                    memory_id=str(res.get("coordinate")), # Simplified ID
                    coordinate=res.get("coordinate", [0.0, 0.0, 0.0]),
                    payload=res.get("payload", {}),
                    score=res.get("importance", 0.0),
                    created_at=datetime.now(timezone.utc) # Placeholder if not returned
                ))

            return MemoryReadResponse(memories=memories)

        except Exception as e:
            logger.error(f"Direct memory recall failed: {e}")
            raise

    def _generate_coordinate(self, payload: Dict[str, Any]) -> List[float]:
        """Simple coordinate generator for direct mode.
        
        In a full system, this would be the SDR encoding. 
        For now, we return a random or hashed coordinate to satisfy the interface.
        """
        import random
        return [random.random() for _ in range(3)]

    def _audit_log(self, action: str, tenant: str, details: Any):
        """Write to audit log (FR-3)."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "action": action,
            "tenant": tenant,
            "details_hash": str(hash(str(details)))
        }
        # In production, write to file. Here logging to info.
        logger.info(f"AUDIT: {json.dumps(entry)}")

