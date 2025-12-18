"""SomaBrain Client for recording execution outcomes.

Provides an interface to send multimodal task execution data to SomaBrain (learning system).
Stores outcomes directly in PostgreSQL for learning and portfolio ranking.

SRS Reference: Section 16.8 (Learning & Ranking)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import asyncpg

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
    
    Stores execution outcomes in PostgreSQL for learning and portfolio ranking.
    VIBE COMPLIANT: Uses database, no file storage.
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize client with database connection.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to cfg.settings().database.dsn
        """
        self._dsn = dsn or cfg.settings().database.dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        """Ensure connection pool is initialized."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=1,
                max_size=5,
                command_timeout=10.0
            )
        return self._pool

    async def record_outcome(self, outcome: MultimodalOutcome) -> None:
        """Record an execution outcome to PostgreSQL.
        
        This method is designed to be safe and non-blocking. FAIL_OPEN strategy.
        
        Args:
            outcome: Outcome data object
        """
        try:
            pool = await self._ensure_pool()
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO multimodal_outcomes (
                        id, plan_id, task_id, step_type, provider, model,
                        success, latency_ms, cost_cents, quality_score, feedback, timestamp
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                    )
                    """,
                    uuid4(),
                    UUID(outcome.plan_id) if outcome.plan_id else None,
                    outcome.task_id,
                    outcome.step_type,
                    outcome.provider,
                    outcome.model,
                    outcome.success,
                    outcome.latency_ms,
                    outcome.cost_cents,
                    outcome.quality_score,
                    outcome.feedback,
                    datetime.fromisoformat(outcome.timestamp) if outcome.timestamp else datetime.now().astimezone()
                )
                
        except Exception as exc:
            # Never block execution flow on metrics recording
            logger.warning("Failed to record SomaBrain outcome to DB: %s", exc)

    async def fetch_outcomes(
        self,
        step_type: Optional[str] = None,
        limit: int = 100
    ) -> list[MultimodalOutcome]:
        """Fetch recent execution outcomes from PostgreSQL.
        
        Args:
            step_type: Filter by step type (e.g., 'generate_image')
            limit: Max records to return
            
        Returns:
            List of MultimodalOutcome objects, sorted by timestamp desc.
        """
        outcomes: list[MultimodalOutcome] = []
        
        try:
            pool = await self._ensure_pool()
            
            async with pool.acquire() as conn:
                if step_type:
                    rows = await conn.fetch(
                        """
                        SELECT plan_id, task_id, step_type, provider, model,
                               success, latency_ms, cost_cents, quality_score, feedback, timestamp
                        FROM multimodal_outcomes
                        WHERE step_type = $1
                        ORDER BY timestamp DESC
                        LIMIT $2
                        """,
                        step_type,
                        limit
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT plan_id, task_id, step_type, provider, model,
                               success, latency_ms, cost_cents, quality_score, feedback, timestamp
                        FROM multimodal_outcomes
                        ORDER BY timestamp DESC
                        LIMIT $1
                        """,
                        limit
                    )
                
                for row in rows:
                    outcome = MultimodalOutcome(
                        plan_id=str(row["plan_id"]) if row["plan_id"] else "",
                        task_id=row["task_id"],
                        step_type=row["step_type"],
                        provider=row["provider"],
                        model=row["model"],
                        success=row["success"],
                        latency_ms=float(row["latency_ms"]),
                        cost_cents=float(row["cost_cents"]),
                        quality_score=float(row["quality_score"]) if row["quality_score"] is not None else None,
                        feedback=row["feedback"],
                        timestamp=row["timestamp"].isoformat()
                    )
                    outcomes.append(outcome)
                    
        except Exception as exc:
            logger.error("Error fetching outcomes from DB: %s", exc)
            
        return outcomes

    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

