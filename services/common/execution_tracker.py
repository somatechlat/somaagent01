"""Execution tracker — tracks status of multimodal job execution.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

LOGGER = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status constants."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SUCCESS = "success"


@dataclass
class ExecutionRecord:
    """Record of a single execution attempt."""

    id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    asset_id: Optional[str] = None


class ExecutionTracker:
    """Tracks execution status of a job."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.job_id = ""
        self.status = ExecutionStatus.PENDING
        self.progress = 0.0

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get_latest_for_step(
        self,
        plan_id: Optional[UUID],
        step_index: int,
    ) -> Optional[ExecutionRecord]:
        """Get the latest execution record for a step."""
        from admin.core.models import ExecutionRecord as ExecutionRecordModel

        record = (
            await ExecutionRecordModel.objects.filter(
                plan_id=str(plan_id) if plan_id else "",
                step_index=step_index,
            )
            .order_by("-started_at")
            .afirst()
        )
        if not record:
            return None
        return ExecutionRecord(
            id=str(record.id),
            status=ExecutionStatus(record.status),
            started_at=record.started_at,
            asset_id=record.asset_id,
        )

    async def start(
        self,
        plan_id: Optional[UUID],
        step_index: int,
        tenant_id: str,
        provider_name: str,
        provider_id: str,
        attempt_number: int = 1,
        **kwargs: Any,
    ) -> ExecutionRecord:
        """Start tracking an execution attempt."""
        from admin.core.models import ExecutionRecord as ExecutionRecordModel

        obj = await ExecutionRecordModel.objects.acreate(
            plan_id=str(plan_id) if plan_id else "",
            step_index=step_index,
            tenant_id=tenant_id,
            provider_name=provider_name,
            provider_id=provider_id,
            attempt_number=attempt_number,
            status="running",
        )
        return ExecutionRecord(
            id=str(obj.id),
            status=ExecutionStatus.RUNNING,
            started_at=obj.started_at,
        )

    async def complete(
        self,
        execution_id: str,
        status: ExecutionStatus,
        asset_id: Optional[str] = None,
        latency_ms: float = 0.0,
        cost_estimate_cents: Optional[int] = None,
        quality_score: Optional[float] = None,
        quality_feedback: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Complete an execution attempt."""
        from admin.core.models import ExecutionRecord as ExecutionRecordModel
        from django.utils import timezone

        record = await ExecutionRecordModel.objects.filter(id=execution_id).afirst()
        if not record:
            return
        record.status = status.value
        record.asset_id = asset_id
        record.latency_ms = latency_ms
        record.cost_estimate_cents = cost_estimate_cents
        record.quality_score = quality_score
        record.quality_feedback = quality_feedback
        record.error_code = error_code
        record.error_message = error_message
        record.completed_at = timezone.now()
        await record.asave()

    def update(self, status: ExecutionStatus, progress: float) -> None:
        """Update execution status."""
        self.status = status
        self.progress = max(0.0, min(1.0, progress))
