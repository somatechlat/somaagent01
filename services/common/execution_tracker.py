"""Execution Tracker for multimodal step execution.

Tracks individual step execution within job plans, recording status,
metrics, and linking to generated assets.

SRS Reference: Section 16.5.2 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg

from src.core.config import cfg

__all__ = [
    "ExecutionRecord",
    "ExecutionStatus",
    "ExecutionTracker",
]

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Status of a step execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class ExecutionRecord:
    """Record of a single step execution.
    
    Attributes:
        id: Unique execution identifier
        plan_id: Parent job plan ID
        step_index: 0-based step index in plan
        tenant_id: Owning tenant
        tool_id: Tool used for execution
        provider: Provider of the tool
        status: Execution status
        attempt_number: Attempt number (1-based)
        asset_id: Generated asset ID (if successful)
        latency_ms: Execution latency in milliseconds
        cost_estimate_cents: Estimated cost in cents
        quality_score: Quality score (0.0-1.0)
        quality_feedback: Feedback from quality check
        error_code: Error code (if failed)
        error_message: Error message (if failed)
        started_at: Execution start time
        completed_at: Execution completion time
        created_at: Record creation time
    """
    id: UUID
    plan_id: UUID
    step_index: int
    tenant_id: str
    tool_id: str
    provider: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempt_number: int = 1
    asset_id: Optional[UUID] = None
    latency_ms: Optional[int] = None
    cost_estimate_cents: Optional[int] = None
    quality_score: Optional[float] = None
    quality_feedback: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ExecutionTracker:
    """Tracks step executions within multimodal job plans.
    
    Records execution state, metrics, and quality information for
    observability and learning.
    
    Usage:
        tracker = ExecutionTracker()
        
        # Start execution
        exec_record = await tracker.start(
            plan_id=plan.id,
            step_index=0,
            tenant_id="acme-corp",
            tool_id="dalle3_image_gen",
            provider="openai",
        )
        
        # Complete execution
        await tracker.complete(
            execution_id=exec_record.id,
            status=ExecutionStatus.SUCCESS,
            asset_id=asset.id,
            latency_ms=1500,
            cost_estimate_cents=50,
        )
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize tracker with database connection.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to config value.
        """
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Verify the multimodal_executions table exists."""
        conn = await asyncpg.connect(self._dsn)
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'multimodal_executions'
                )
            """)
            if not exists:
                raise RuntimeError(
                    "multimodal_executions table does not exist. "
                    "Run migration 017_multimodal_schema.sql."
                )
        finally:
            await conn.close()

    async def start(
        self,
        plan_id: UUID,
        step_index: int,
        tenant_id: str,
        tool_id: str,
        provider: str,
        attempt_number: int = 1,
    ) -> ExecutionRecord:
        """Start tracking a step execution.
        
        Args:
            plan_id: Parent job plan ID
            step_index: 0-based index in plan
            tenant_id: Owning tenant
            tool_id: Tool being used
            provider: Provider of the tool
            attempt_number: Attempt number (1 = first attempt)
        Returns:
            ExecutionRecord with assigned ID
        """
        execution_id = uuid4()
        now = datetime.now()
        
        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute("""
                INSERT INTO multimodal_executions (
                    id, plan_id, step_index, tenant_id, tool_id, provider,
                    status, attempt_number, started_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                execution_id,
                plan_id,
                step_index,
                tenant_id,
                tool_id,
                provider,
                ExecutionStatus.RUNNING.value,
                attempt_number,
                now,
                now,
            )
            
            logger.info(
                "Started execution %s for plan %s step %d",
                execution_id, plan_id, step_index
            )
            
            return ExecutionRecord(
                id=execution_id,
                plan_id=plan_id,
                step_index=step_index,
                tenant_id=tenant_id,
                tool_id=tool_id,
                provider=provider,
                status=ExecutionStatus.RUNNING,
                attempt_number=attempt_number,
                started_at=now,
                created_at=now,
            )
        finally:
            await conn.close()

    async def complete(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        asset_id: Optional[UUID] = None,
        latency_ms: Optional[int] = None,
        cost_estimate_cents: Optional[int] = None,
        quality_score: Optional[float] = None,
        quality_feedback: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Complete a step execution with results.
        
        Args:
            execution_id: Execution record ID
            status: Final status
            asset_id: Generated asset ID (if successful)
            latency_ms: Total latency
            cost_estimate_cents: Estimated cost
            quality_score: Quality score (0.0-1.0)
            quality_feedback: Quality check feedback
            error_code: Error code (if failed)
            error_message: Error message (if failed)
            
        Returns:
            True if updated, False if not found
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute("""
                UPDATE multimodal_executions
                SET status = $2,
                    asset_id = $3,
                    latency_ms = $4,
                    cost_estimate_cents = $5,
                    quality_score = $6,
                    quality_feedback = $7,
                    error_code = $8,
                    error_message = $9,
                    completed_at = NOW()
                WHERE id = $1
            """,
                execution_id,
                status.value,
                asset_id,
                latency_ms,
                cost_estimate_cents,
                quality_score,
                json.dumps(quality_feedback) if quality_feedback else None,
                error_code,
                error_message,
            )
            
            _, count_str = result.split(" ")
            updated = int(count_str) > 0
            
            if updated:
                logger.info(
                    "Completed execution %s with status %s",
                    execution_id, status.value
                )
            
            return updated
        finally:
            await conn.close()

    async def get(self, execution_id: UUID) -> Optional[ExecutionRecord]:
        """Get an execution record by ID.
        
        Args:
            execution_id: Execution UUID
            
        Returns:
            ExecutionRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM multimodal_executions WHERE id = $1",
                execution_id,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def list_for_plan(
        self,
        plan_id: UUID,
        status: Optional[ExecutionStatus] = None,
    ) -> List[ExecutionRecord]:
        """List all executions for a plan.
        
        Args:
            plan_id: Parent plan ID
            status: Optional status filter
            
        Returns:
            List of ExecutionRecord ordered by step_index
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            if status:
                rows = await conn.fetch("""
                    SELECT * FROM multimodal_executions
                    WHERE plan_id = $1 AND status = $2
                    ORDER BY step_index, attempt_number
                """,
                    plan_id, status.value,
                )
            else:
                rows = await conn.fetch("""
                    SELECT * FROM multimodal_executions
                    WHERE plan_id = $1
                    ORDER BY step_index, attempt_number
                """,
                    plan_id,
                )
            
            return [self._row_to_record(r) for r in rows]
        finally:
            await conn.close()

    async def get_latest_for_step(
        self,
        plan_id: UUID,
        step_index: int,
    ) -> Optional[ExecutionRecord]:
        """Get the latest execution attempt for a step.
        
        Args:
            plan_id: Parent plan ID
            step_index: Step index
            
        Returns:
            Latest ExecutionRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow("""
                SELECT * FROM multimodal_executions
                WHERE plan_id = $1 AND step_index = $2
                ORDER BY attempt_number DESC
                LIMIT 1
            """,
                plan_id, step_index,
            )
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def get_step_metrics(
        self,
        plan_id: UUID,
    ) -> Dict[str, Any]:
        """Get aggregated metrics for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Dict with total_latency_ms, total_cost_cents, avg_quality_score
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow("""
                SELECT 
                    SUM(latency_ms) as total_latency_ms,
                    SUM(cost_estimate_cents) as total_cost_cents,
                    AVG(quality_score) as avg_quality_score,
                    COUNT(*) as total_executions,
                    COUNT(*) FILTER (WHERE status = 'success') as successful_executions
                FROM multimodal_executions
                WHERE plan_id = $1
            """,
                plan_id,
            )
            
            return {
                "total_latency_ms": row["total_latency_ms"] or 0,
                "total_cost_cents": row["total_cost_cents"] or 0,
                "avg_quality_score": float(row["avg_quality_score"]) if row["avg_quality_score"] else None,
                "total_executions": row["total_executions"] or 0,
                "successful_executions": row["successful_executions"] or 0,
            }
        finally:
            await conn.close()

    def _row_to_record(self, row: asyncpg.Record) -> ExecutionRecord:
        """Convert database row to ExecutionRecord.
        
        Args:
            row: asyncpg Record from query
            
        Returns:
            ExecutionRecord instance
        """
        quality_feedback = None
        if row.get("quality_feedback"):
            quality_feedback = json.loads(row["quality_feedback"])
        
        return ExecutionRecord(
            id=row["id"],
            plan_id=row["plan_id"],
            step_index=row["step_index"],
            tenant_id=row["tenant_id"],
            tool_id=row["tool_id"],
            provider=row["provider"],
            status=ExecutionStatus(row["status"]) if row["status"] else ExecutionStatus.PENDING,
            attempt_number=row.get("attempt_number") or 1,
            asset_id=row.get("asset_id"),
            latency_ms=row.get("latency_ms"),
            cost_estimate_cents=row.get("cost_estimate_cents"),
            quality_score=row.get("quality_score"),
            quality_feedback=quality_feedback,
            error_code=row.get("error_code"),
            error_message=row.get("error_message"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            created_at=row.get("created_at"),
        )
