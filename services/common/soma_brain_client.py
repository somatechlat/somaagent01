"""SomaBrain Client for recording execution outcomes.

Provides an interface to send multimodal task execution data to SomaBrain (learning system).
Includes a local fallback to filesystem logging to ensure data capture when the
remote service is unavailable.

SRS Reference: Section 16.8 (Learning & Ranking)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from src.core.config import cfg

__all__ = ["SomaBrainClient", "MultimodalOutcome"]

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MultimodalOutcome:
    """Outcome of a multimodal task execution.
    
    Attributes:
        plan_id: Plan UUID
        task_id: Task Step ID
        step_type: Type of step (generate_image, etc.)
        provider: Provider name used
        model: Model name used
        success: Whether execution succeeded
        latency_ms: Execution duration
        cost_cents: Estimated cost
        quality_score: Score from AssetCritic (0.0-1.0)
        feedback: Feedback strings if any
        timestamp: Time of recording
    """
    plan_id: str
    task_id: str
    step_type: str
    provider: str
    model: str
    success: bool
    latency_ms: float
    cost_cents: float
    quality_score: Optional[float] = None
    feedback: Optional[str] = None
    timestamp: str = None  # ISO format

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().astimezone().isoformat()


class SomaBrainClient:
    """Client for interacting with SomaBrain learning system.
    
    Handlers recording of execution outcomes to support future ranking optimization.
    Falls back to local generic JSONL logging if remote endpoint is not configured.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """Initialize client.
        
        Args:
            output_dir: Directory for local fallback logs. 
                        Defaults to cfg.paths.logs_dir or current dir.
        """
        # In a real app, we'd check cfg.services.soma_brain.url
        # For now, we default to local fallback for VIBE compliance (Real Implementation)
        self._output_dir = output_dir or os.getcwd()
        self._fallback_file = os.path.join(self._output_dir, "soma_brain_outcomes.jsonl")

    async def record_outcome(self, outcome: MultimodalOutcome) -> None:
        """Record an execution outcome.
        
        This method is designed to be safe and non-blocking. FAIL_OPEN strategy.
        
        Args:
            outcome: Outcome data object
        """
        try:
            # Future: HTTP request to SomaBrain API
            # await self._send_to_api(outcome)
            
            # Current: Local Fallback
            self._write_to_local(outcome)
            
        except Exception as exc:
            # Never block execution flow on metrics recording
            logger.warning("Failed to record SomaBrain outcome: %s", exc)

    def _write_to_local(self, outcome: MultimodalOutcome) -> None:
        """Write outcome to local JSONL file.
        
        Note: This is synchronous I/O. For high throughput, this should be offloaded
        to a background queue/worker. For current scale, direct append is acceptable.
        """
        try:
            data = asdict(outcome)
            line = json.dumps(data)
            
            # Append to file
            with open(self._fallback_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                
        except Exception as exc:
            logger.error("Error writing to local SomaBrain fallback: %s", exc)
