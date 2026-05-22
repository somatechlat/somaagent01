"""SomaBrain outcomes store — tracks multimodal operation results.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    import asyncpg  # type: ignore
except ImportError:
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class MultimodalOutcome:
    """Outcome of a multimodal operation."""

    task_id: str
    status: str
    result: Dict[str, Any]
    provider: str = ""
    success: bool = False
    latency_ms: float = 0.0
    quality_score: Optional[float] = None
    cost_cents: float = 0.0


class SomaBrainOutcomesStore:
    """PostgreSQL-backed store for SomaBrain operation outcomes."""

    TABLE_NAME = "soma_brain_outcomes"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def fetch_outcomes(
        self, step_type: str, limit: int = 100
    ) -> list[MultimodalOutcome]:
        """Fetch recent multimodal outcomes for a step type."""
        if not self.dsn or asyncpg is None:
            raise RuntimeError("SomaBrainOutcomesStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT task_id, status, result
                    FROM {self.TABLE_NAME}
                    WHERE result->>'step_type' = $1
                    ORDER BY result->>'timestamp' DESC
                    LIMIT $2
                    """,
                    step_type,
                    limit,
                )
                return [
                    MultimodalOutcome(
                        task_id=row["task_id"],
                        status=row["status"],
                        result=row["result"],
                        provider=row["result"].get("provider", ""),
                        success=row["result"].get("success", False),
                        latency_ms=row["result"].get("latency_ms", 0.0),
                        quality_score=row["result"].get("quality_score"),
                        cost_cents=row["result"].get("cost_cents", 0.0),
                    )
                    for row in rows
                ]
        finally:
            await pool.close()

    async def record(self, outcome: MultimodalOutcome) -> None:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("SomaBrainOutcomesStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                import json

                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (task_id, status, result)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (task_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        result = EXCLUDED.result
                    """,
                    outcome.task_id,
                    outcome.status,
                    json.dumps(outcome.result),
                )
        finally:
            await pool.close()
