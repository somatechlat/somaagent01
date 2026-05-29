"""Job planner — plans and tracks multimodal job execution steps.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

LOGGER = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    """Type of job step."""

    GENERATE = "generate"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    GENERATE_DIAGRAM = "generate_diagram"
    CAPTURE_SCREENSHOT = "capture_screenshot"
    GENERATE_VIDEO = "generate_video"
    COMPOSE_DOCUMENT = "compose_document"
    GENERATE_IMAGE = "generate_image"


@dataclass
class TaskStep:
    """A single step in a job plan."""

    step_type: StepType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    task_id: str = ""
    modality: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    prompt: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    quality_gate: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobPlan:
    """A planned job with steps."""

    job_id: str
    steps: List[TaskStep]
    status: JobStatus = JobStatus.PENDING
    id: Optional[UUID] = None
    budget_used_cents: Optional[int] = None
    budget_limit_cents: Optional[int] = None
    tenant_id: str = ""
    session_id: str = ""
    request_id: str = ""
    user_id: str = ""
    tasks: List[TaskStep] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    quality_gate: Dict[str, Any] = field(default_factory=dict)
    prompt: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    error_message: Optional[str] = None


class PlanValidationError(Exception):
    """Raised when a job plan fails validation."""

    errors: str = ""

    def __init__(self, message: str = "") -> None:
        self.errors = message
        super().__init__(message)


class JobPlanner:
    """Planner for multimodal job execution."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        pass

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    def create_plan(self, job_id: str, request: Dict[str, Any]) -> JobPlan:
        """Create a job plan from a request."""
        steps = []
        for step_def in request.get("steps", []):
            steps.append(
                TaskStep(
                    step_type=StepType(step_def.get("type", "generate")),
                    description=step_def.get("description", ""),
                    parameters=step_def.get("parameters", {}),
                )
            )
        return JobPlan(job_id=job_id, steps=steps)

    def validate(self, plan: JobPlan) -> None:
        """Validate a job plan."""
        if not plan.steps:
            raise PlanValidationError("Job plan must have at least one step")

    async def claim_next_pending(self) -> Optional[JobPlan]:
        """Claim the next pending job plan for execution."""
        from admin.core.models import Job

        job = await Job.objects.filter(status="pending").order_by("created_at").afirst()
        if not job:
            return None
        job.status = "running"
        job.started_at = __import__("django.utils.timezone").now()
        await job.asave(update_fields=["status", "started_at", "updated_at"])
        return JobPlan(
            job_id=job.name,
            steps=[],
            status=JobStatus.RUNNING,
            id=job.id,
            tenant_id=job.tenant,
        )

    async def get(self, plan_id: Optional[UUID]) -> Optional[JobPlan]:
        """Get a job plan by ID."""
        from admin.core.models import Job

        if not plan_id:
            return None
        job = await Job.objects.filter(id=plan_id).afirst()
        if not job:
            return None
        payload = job.payload or {}
        return JobPlan(
            job_id=job.name,
            steps=[
                TaskStep(
                    step_type=StepType(s.get("type", "generate")),
                    description=s.get("description", ""),
                    parameters=s.get("parameters", {}),
                )
                for s in payload.get("steps", [])
            ],
            status=JobStatus(job.status),
            id=job.id,
            tenant_id=job.tenant,
            completed_steps=payload.get("completed_steps", 0),
            error_message=job.error,
        )

    async def update_status(
        self,
        plan_id: Optional[UUID],
        status: JobStatus,
        **kwargs: Any,
    ) -> None:
        """Update the status of a job plan."""
        from admin.core.models import Job

        if not plan_id:
            return
        job = await Job.objects.filter(id=plan_id).afirst()
        if not job:
            return
        job.status = status.value
        if "completed_steps" in kwargs:
            payload = job.payload or {}
            payload["completed_steps"] = kwargs["completed_steps"]
            job.payload = payload
        if "error_message" in kwargs:
            job.error = kwargs["error_message"]
        if status == JobStatus.COMPLETED:
            job.completed_at = __import__("django.utils.timezone").now()
        await job.asave()

    def compile(
        self,
        tenant_id: Optional[str] = None,
        session_id: str = "",
        dsl: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> JobPlan:
        """Compile a DSL into a job plan."""
        steps = []
        if dsl:
            for step_def in dsl.get("steps", []):
                steps.append(
                    TaskStep(
                        step_type=StepType(step_def.get("type", "generate")),
                        description=step_def.get("description", ""),
                        parameters=step_def.get("parameters", {}),
                    )
                )
        return JobPlan(
            job_id=request_id or "",
            steps=steps,
            tenant_id=tenant_id or "",
            session_id=session_id,
        )

    async def create(self, plan: JobPlan) -> JobPlan:
        """Create a new job plan."""
        from admin.core.models import Job

        obj = await Job.objects.acreate(
            name=plan.job_id,
            job_type="multimodal",
            tenant=plan.tenant_id,
            payload={
                "steps": [
                    {
                        "type": s.step_type.value,
                        "description": s.description,
                        "parameters": s.parameters,
                    }
                    for s in plan.steps
                ],
                "completed_steps": plan.completed_steps,
            },
            status=plan.status.value,
        )
        plan.id = obj.id
        return plan
