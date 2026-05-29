"""SomaBrain outcomes store — tracks multimodal operation results.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

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


class SomaBrainOutcomesStore(BaseStore[MultimodalOutcome]):
    """Django ORM-backed store for SomaBrain operation outcomes."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def fetch_outcomes(
        self, step_type: str, limit: int = 100
    ) -> list[MultimodalOutcome]:
        """Fetch recent multimodal outcomes for a step type."""
        from admin.core.models import MultimodalOutcome as OutcomeModel

        qs = OutcomeModel.objects.filter(step_type=step_type).order_by("-created_at")[:limit]
        results = []
        async for outcome in qs:
            results.append(
                MultimodalOutcome(
                    task_id=outcome.task_id,
                    status=outcome.status,
                    result=outcome.result,
                    provider=outcome.provider or "",
                    success=outcome.success,
                    latency_ms=outcome.latency_ms or 0.0,
                    quality_score=outcome.quality_score,
                    cost_cents=outcome.cost_cents or 0.0,
                )
            )
        return results

    async def record(
        self,
        task_id: str,
        step_type: str,
        status: str,
        result: Dict[str, Any],
        provider: str = "",
        success: bool = False,
        latency_ms: float = 0.0,
        quality_score: Optional[float] = None,
        cost_cents: float = 0.0,
    ) -> None:
        """Record an outcome."""
        from admin.core.models import MultimodalOutcome as OutcomeModel

        await OutcomeModel.objects.acreate(
            task_id=task_id,
            step_type=step_type,
            status=status,
            result=result,
            provider=provider,
            success=success,
            latency_ms=latency_ms,
            quality_score=quality_score,
            cost_cents=cost_cents,
        )

    async def get(self, identifier: str) -> Optional[MultimodalOutcome]:
        """Get an outcome by task_id."""
        from admin.core.models import MultimodalOutcome as OutcomeModel

        outcome = await OutcomeModel.objects.filter(task_id=identifier).afirst()
        if not outcome:
            return None
        return MultimodalOutcome(
            task_id=outcome.task_id,
            status=outcome.status,
            result=outcome.result,
            provider=outcome.provider or "",
            success=outcome.success,
            latency_ms=outcome.latency_ms or 0.0,
            quality_score=outcome.quality_score,
            cost_cents=outcome.cost_cents or 0.0,
        )

    async def create(self, record: MultimodalOutcome) -> MultimodalOutcome:
        """Persist an outcome."""
        await self.record(
            task_id=record.task_id,
            step_type="unknown",
            status=record.status,
            result=record.result,
            provider=record.provider,
            success=record.success,
            latency_ms=record.latency_ms,
            quality_score=record.quality_score,
            cost_cents=record.cost_cents,
        )
        return record

    async def update(
        self, identifier: str, changes: Dict[str, Any]
    ) -> Optional[MultimodalOutcome]:
        """Update an outcome."""
        from admin.core.models import MultimodalOutcome as OutcomeModel

        outcome = await OutcomeModel.objects.filter(task_id=identifier).afirst()
        if not outcome:
            return None
        if "status" in changes:
            outcome.status = changes["status"]
        if "result" in changes:
            outcome.result = changes["result"]
        if "success" in changes:
            outcome.success = changes["success"]
        await outcome.asave()
        return await self.get(identifier)

    async def delete(self, identifier: str) -> bool:
        """Remove an outcome."""
        from admin.core.models import MultimodalOutcome as OutcomeModel

        deleted, _ = await OutcomeModel.objects.filter(task_id=identifier).adelete()
        return deleted > 0
