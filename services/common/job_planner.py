"""Job Planner for multimodal workflow orchestration.

Creates, validates, and stores multimodal job plans following the Task DSL v1.0
schema. Provides plan compilation with topological ordering for execution.

SRS Reference: Section 16.5 (Task Planning)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import asyncpg

from src.core.config import cfg

__all__ = [
    "JobPlan",
    "TaskStep",
    "StepType",
    "JobStatus",
    "JobPlanner",
    "PlanValidationError",
]

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Status of a job plan."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Type of task step."""
    GENERATE_IMAGE = "generate_image"
    GENERATE_DIAGRAM = "generate_diagram"
    CAPTURE_SCREENSHOT = "capture_screenshot"
    GENERATE_VIDEO = "generate_video"
    COMPOSE_DOCUMENT = "compose_document"
    TRANSFORM_ASSET = "transform_asset"


class PlanValidationError(Exception):
    """Raised when plan validation fails."""
    
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__(f"Plan validation failed: {errors}")


@dataclass(slots=True)
class TaskStep:
    """Individual task step within a plan.
    
    Attributes:
        task_id: Unique identifier within the plan
        step_type: Type of operation (generate_image, etc.)
        modality: Output modality (image, diagram, screenshot, etc.)
        depends_on: List of task_ids this step depends on
        params: Step-specific parameters (prompt, format, etc.)
        constraints: Execution constraints (provider, cost, timeout)
        quality_gate: Quality check configuration
        on_failure: Action on failure (fail, skip, fallback)
        metadata: Additional task metadata
    """
    task_id: str
    step_type: StepType
    modality: str
    depends_on: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    quality_gate: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "min_score": 0.7, "max_reworks": 2
    })
    on_failure: str = "fallback"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobPlan:
    """Multimodal job plan.
    
    Attributes:
        id: Unique plan identifier
        tenant_id: Owning tenant
        session_id: Session this plan belongs to
        request_id: Original request correlation ID
        version: Task DSL version
        tasks: List of task steps
        budget: Budget constraints (max_cost_cents, etc.)
        policy_overrides: Override default policies
        status: Current plan status
        total_steps: Total number of steps
        completed_steps: Number of completed steps
        budget_used_cents: Budget consumed
        created_at: Creation timestamp
        started_at: Execution start time
        completed_at: Completion time
        error_message: Error message if failed
    """
    id: UUID
    tenant_id: str
    session_id: str
    tasks: List[TaskStep]
    version: str = "1.0"
    request_id: Optional[str] = None
    budget: Dict[str, Any] = field(default_factory=dict)
    policy_overrides: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    total_steps: int = 0
    completed_steps: int = 0
    budget_used_cents: int = 0
    budget_limit_cents: Optional[int] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set total_steps from tasks length."""
        if not self.total_steps and self.tasks:
            self.total_steps = len(self.tasks)
        if self.budget.get("max_cost_cents") and not self.budget_limit_cents:
            self.budget_limit_cents = self.budget["max_cost_cents"]


class JobPlanner:
    """Creates, validates, and stores multimodal job plans.
    
    Provides plan compilation with topological ordering and validation
    against the Task DSL v1.0 schema.
    
    Usage:
        planner = JobPlanner()
        
        # Compile a plan from DSL
        plan = await planner.compile(
            tenant_id="acme-corp",
            session_id="session-123",
            dsl={
                "version": "1.0",
                "tasks": [
                    {"task_id": "logo", "step_type": "generate_image", "modality": "image_photo", ...}
                ],
                "budget": {"max_cost_cents": 100}
            }
        )
        
        # Store the plan
        await planner.create(plan)
        
        # Retrieve a plan
        plan = await planner.get(plan_id)
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize planner with database connection string.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to config value.
        """
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Verify the multimodal_job_plans table exists."""
        conn = await asyncpg.connect(self._dsn)
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'multimodal_job_plans'
                )
            """)
            if not exists:
                raise RuntimeError(
                    "multimodal_job_plans table does not exist. "
                    "Run migration 017_multimodal_schema.sql."
                )
        finally:
            await conn.close()

    def compile(
        self,
        tenant_id: str,
        session_id: str,
        dsl: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> JobPlan:
        """Compile a Task DSL document into a JobPlan.
        
        Validates the DSL, builds TaskStep objects, and performs
        topological ordering for execution.
        
        Args:
            tenant_id: Owning tenant
            session_id: Session ID
            dsl: Task DSL document following schemas/task_dsl_v1.json
            request_id: Optional request correlation ID
            
        Returns:
            Compiled JobPlan ready for storage and execution
            
        Raises:
            PlanValidationError: If DSL validation fails
        """
        # Validate DSL structure
        errors = self._validate_dsl(dsl)
        if errors:
            raise PlanValidationError(errors)
        
        # Build task steps
        tasks: List[TaskStep] = []
        for task_dict in dsl.get("tasks", []):
            step = TaskStep(
                task_id=task_dict["task_id"],
                step_type=StepType(task_dict["step_type"]),
                modality=task_dict["modality"],
                depends_on=task_dict.get("depends_on", []),
                params=task_dict.get("params", {}),
                constraints=task_dict.get("constraints", {}),
                quality_gate=task_dict.get("quality_gate", {
                    "enabled": True, "min_score": 0.7, "max_reworks": 2
                }),
                on_failure=task_dict.get("on_failure", "fallback"),
                metadata=task_dict.get("metadata", {}),
            )
            tasks.append(step)
        
        # Topological sort
        sorted_tasks = self._topological_sort(tasks)
        
        # Build plan
        budget = dsl.get("budget", {})
        plan = JobPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            session_id=session_id,
            request_id=request_id,
            version=dsl.get("version", "1.0"),
            tasks=sorted_tasks,
            budget=budget,
            budget_limit_cents=budget.get("max_cost_cents"),
            policy_overrides=dsl.get("policy_overrides", {}),
            metadata=dsl.get("metadata", {}),
            created_at=datetime.now(),
        )
        
        logger.info(
            "Compiled plan %s with %d tasks for tenant %s",
            plan.id, len(tasks), tenant_id
        )
        
        return plan

    def _validate_dsl(self, dsl: Dict[str, Any]) -> List[str]:
        """Validate DSL document.
        
        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []
        
        # Check version
        if dsl.get("version") not in ["1.0", None]:
            errors.append(f"Unsupported version: {dsl.get('version')}")
        
        # Check tasks present
        tasks = dsl.get("tasks", [])
        if not tasks:
            errors.append("Plan must have at least one task")
            return errors
        
        # Validate each task
        task_ids: Set[str] = set()
        for i, task in enumerate(tasks):
            task_id = task.get("task_id")
            
            if not task_id:
                errors.append(f"Task {i} missing task_id")
                continue
            
            if task_id in task_ids:
                errors.append(f"Duplicate task_id: {task_id}")
            task_ids.add(task_id)
            
            if "step_type" not in task:
                errors.append(f"Task {task_id} missing step_type")
            else:
                try:
                    StepType(task["step_type"])
                except ValueError:
                    errors.append(f"Task {task_id} has invalid step_type: {task['step_type']}")
            
            if "modality" not in task:
                errors.append(f"Task {task_id} missing modality")
        
        # Validate dependencies
        for task in tasks:
            task_id = task.get("task_id", "?")
            for dep in task.get("depends_on", []):
                if dep not in task_ids:
                    errors.append(f"Task {task_id} depends on unknown task: {dep}")
        
        # Check for circular dependencies
        if not errors:
            cycle = self._detect_cycle(tasks)
            if cycle:
                errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        # Validate budget
        budget = dsl.get("budget", {})
        if budget.get("max_cost_cents") is not None:
            if not isinstance(budget["max_cost_cents"], int) or budget["max_cost_cents"] < 0:
                errors.append("budget.max_cost_cents must be a non-negative integer")
        
        return errors

    def _detect_cycle(self, tasks: List[Dict[str, Any]]) -> Optional[List[str]]:
        """Detect circular dependencies using DFS.
        
        Returns cycle path if found, None otherwise.
        """
        # Build adjacency list
        graph: Dict[str, List[str]] = {}
        for task in tasks:
            task_id = task.get("task_id", "")
            graph[task_id] = task.get("depends_on", [])
        
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    path.append(neighbor)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    # Return the cycle portion
                    cycle_start = path.index(path[-1])
                    return path[cycle_start:]
        
        return None

    def _topological_sort(self, tasks: List[TaskStep]) -> List[TaskStep]:
        """Sort tasks in topological order using Kahn's algorithm.
        
        Args:
            tasks: List of TaskStep objects
            
        Returns:
            Topologically sorted list of tasks
            
        Raises:
            PlanValidationError: If circular dependency detected
        """
        # Build graph and in-degree map
        task_map = {t.task_id: t for t in tasks}
        in_degree: Dict[str, int] = {t.task_id: 0 for t in tasks}
        
        for task in tasks:
            for dep in task.depends_on:
                if dep in in_degree:
                    in_degree[task.task_id] += 1
        
        # Initialize queue with tasks having no dependencies
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        result: List[TaskStep] = []
        
        while queue:
            task_id = queue.popleft()
            result.append(task_map[task_id])
            
            # Reduce in-degree for dependent tasks
            for task in tasks:
                if task_id in task.depends_on:
                    in_degree[task.task_id] -= 1
                    if in_degree[task.task_id] == 0:
                        queue.append(task.task_id)
        
        if len(result) != len(tasks):
            raise PlanValidationError(["Circular dependency detected during topological sort"])
        
        return result

    async def create(self, plan: JobPlan) -> None:
        """Store a job plan in the database.
        
        Args:
            plan: JobPlan to store
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            # Serialize tasks to JSON
            plan_json = {
                "version": plan.version,
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "step_type": t.step_type.value,
                        "modality": t.modality,
                        "depends_on": t.depends_on,
                        "params": t.params,
                        "constraints": t.constraints,
                        "quality_gate": t.quality_gate,
                        "on_failure": t.on_failure,
                        "metadata": t.metadata,
                    }
                    for t in plan.tasks
                ],
                "budget": plan.budget,
                "policy_overrides": plan.policy_overrides,
                "metadata": plan.metadata,
            }
            
            await conn.execute("""
                INSERT INTO multimodal_job_plans (
                    id, tenant_id, session_id, request_id,
                    plan_json, plan_version, status,
                    total_steps, completed_steps,
                    budget_limit_cents, budget_used_cents,
                    started_at, completed_at,
                    error_message, error_details,
                    created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                )
            """,
                plan.id,
                plan.tenant_id,
                plan.session_id,
                plan.request_id,
                json.dumps(plan_json),
                plan.version,
                plan.status.value,
                plan.total_steps,
                plan.completed_steps,
                plan.budget_limit_cents,
                plan.budget_used_cents,
                plan.started_at,
                plan.completed_at,
                plan.error_message,
                json.dumps(plan.error_details) if plan.error_details else None,
                plan.created_at or datetime.now(),
            )
            
            logger.info("Created plan: %s", plan.id)
        finally:
            await conn.close()

    async def get(self, plan_id: UUID) -> Optional[JobPlan]:
        """Retrieve a job plan by ID.
        
        Args:
            plan_id: UUID of the plan
            
        Returns:
            JobPlan if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow(
                "SELECT * FROM multimodal_job_plans WHERE id = $1",
                plan_id,
            )
            if not row:
                return None
            return self._row_to_plan(row)
        finally:
            await conn.close()

    async def list(
        self,
        tenant_id: str,
        session_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[JobPlan]:
        """List job plans with filters.
        
        Args:
            tenant_id: Tenant to list from
            session_id: Optional session filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of JobPlan objects
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            query_parts = ["SELECT * FROM multimodal_job_plans WHERE tenant_id = $1"]
            params: List[Any] = [tenant_id]
            param_idx = 2
            
            if session_id:
                query_parts.append(f"AND session_id = ${param_idx}")
                params.append(session_id)
                param_idx += 1
            
            if status:
                query_parts.append(f"AND status = ${param_idx}")
                params.append(status.value)
                param_idx += 1
            
            query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}")
            params.extend([limit, offset])
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            return [self._row_to_plan(r) for r in rows]
        finally:
            await conn.close()

    async def update_status(
        self,
        plan_id: UUID,
        status: JobStatus,
        completed_steps: Optional[int] = None,
        budget_used_cents: Optional[int] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update plan status and progress.
        
        Args:
            plan_id: Plan UUID
            status: New status
            completed_steps: Number of completed steps
            budget_used_cents: Budget consumed
            error_message: Error message (for failed status)
            error_details: Error details
            
        Returns:
            True if updated, False if not found
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            # Build SET clause dynamically
            set_parts = ["status = $2", "updated_at = NOW()"]
            params: List[Any] = [plan_id, status.value]
            param_idx = 3
            
            if status == JobStatus.RUNNING:
                set_parts.append("started_at = COALESCE(started_at, NOW())")
            
            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                set_parts.append("completed_at = NOW()")
            
            if completed_steps is not None:
                set_parts.append(f"completed_steps = ${param_idx}")
                params.append(completed_steps)
                param_idx += 1
            
            if budget_used_cents is not None:
                set_parts.append(f"budget_used_cents = ${param_idx}")
                params.append(budget_used_cents)
                param_idx += 1
            
            if error_message is not None:
                set_parts.append(f"error_message = ${param_idx}")
                params.append(error_message)
                param_idx += 1
            
            if error_details is not None:
                set_parts.append(f"error_details = ${param_idx}")
                params.append(json.dumps(error_details))
                param_idx += 1
            
            query = f"UPDATE multimodal_job_plans SET {', '.join(set_parts)} WHERE id = $1"
            result = await conn.execute(query, *params)
            
            _, count_str = result.split(" ")
            updated = int(count_str) > 0
            
            if updated:
                logger.info("Updated plan %s status to %s", plan_id, status.value)
            
            return updated
        finally:
            await conn.close()

    def _row_to_plan(self, row: asyncpg.Record) -> JobPlan:
        """Convert database row to JobPlan.
        
        Args:
            row: asyncpg Record from query
            
        Returns:
            JobPlan instance
        """
        plan_json = json.loads(row["plan_json"]) if row["plan_json"] else {}
        
        # Build task steps from JSON
        tasks: List[TaskStep] = []
        for task_dict in plan_json.get("tasks", []):
            step = TaskStep(
                task_id=task_dict["task_id"],
                step_type=StepType(task_dict["step_type"]),
                modality=task_dict["modality"],
                depends_on=task_dict.get("depends_on", []),
                params=task_dict.get("params", {}),
                constraints=task_dict.get("constraints", {}),
                quality_gate=task_dict.get("quality_gate", {}),
                on_failure=task_dict.get("on_failure", "fallback"),
                metadata=task_dict.get("metadata", {}),
            )
            tasks.append(step)
        
        error_details = None
        if row.get("error_details"):
            error_details = json.loads(row["error_details"])
        
        return JobPlan(
            id=row["id"],
            tenant_id=row["tenant_id"],
            session_id=row["session_id"],
            request_id=row.get("request_id"),
            version=row.get("plan_version", "1.0"),
            tasks=tasks,
            budget=plan_json.get("budget", {}),
            policy_overrides=plan_json.get("policy_overrides", {}),
            status=JobStatus(row["status"]) if row["status"] else JobStatus.PENDING,
            total_steps=row.get("total_steps", 0),
            completed_steps=row.get("completed_steps", 0),
            budget_limit_cents=row.get("budget_limit_cents"),
            budget_used_cents=row.get("budget_used_cents", 0),
            created_at=row.get("created_at"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            error_message=row.get("error_message"),
            error_details=error_details,
            metadata=plan_json.get("metadata", {}),
        )
