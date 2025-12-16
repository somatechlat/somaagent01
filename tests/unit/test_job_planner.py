"""Unit tests for JobPlanner (no DB required).

Tests verify DSL validation, topological sorting, cycle detection,
and data structures without database connections.

Pattern Reference: test_capability_registry.py
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.common.job_planner import (
    JobPlanner,
    JobPlan,
    TaskStep,
    StepType,
    JobStatus,
    PlanValidationError,
)


def make_task(**kwargs) -> dict:
    """Create a test task dictionary."""
    defaults = {
        "task_id": "task_1",
        "step_type": "generate_image",
        "modality": "image_photo",
        "params": {"prompt": "test prompt"},
    }
    defaults.update(kwargs)
    return defaults


def make_dsl(**kwargs) -> dict:
    """Create a test DSL document."""
    defaults = {
        "version": "1.0",
        "tasks": [make_task()],
        "budget": {"max_cost_cents": 100},
    }
    defaults.update(kwargs)
    return defaults


class TestTaskStep:
    """Tests for TaskStep dataclass."""

    def test_create_minimal(self):
        step = TaskStep(
            task_id="logo",
            step_type=StepType.GENERATE_IMAGE,
            modality="image_photo",
        )
        assert step.task_id == "logo"
        assert step.step_type == StepType.GENERATE_IMAGE
        assert step.depends_on == []
        assert step.on_failure == "fallback"

    def test_create_full(self):
        step = TaskStep(
            task_id="diagram",
            step_type=StepType.GENERATE_DIAGRAM,
            modality="image_diagram",
            depends_on=["logo"],
            params={"code": "graph TD\n  A-->B"},
            constraints={"max_cost_cents": 10},
            quality_gate={"enabled": True, "min_score": 0.8},
        )
        assert step.depends_on == ["logo"]
        assert "code" in step.params
        assert step.quality_gate["min_score"] == 0.8


class TestStepType:
    """Tests for StepType enum."""

    def test_step_type_values(self):
        assert StepType.GENERATE_IMAGE.value == "generate_image"
        assert StepType.GENERATE_DIAGRAM.value == "generate_diagram"
        assert StepType.CAPTURE_SCREENSHOT.value == "capture_screenshot"
        assert StepType.GENERATE_VIDEO.value == "generate_video"
        assert StepType.COMPOSE_DOCUMENT.value == "compose_document"
        assert StepType.TRANSFORM_ASSET.value == "transform_asset"


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"


class TestJobPlan:
    """Tests for JobPlan dataclass."""

    def test_create_plan(self):
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test-tenant",
            session_id="session-123",
            tasks=[
                TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo"),
            ],
        )
        assert plan.status == JobStatus.PENDING
        assert plan.total_steps == 1
        assert plan.completed_steps == 0

    def test_budget_limit_from_budget(self):
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[],
            budget={"max_cost_cents": 500},
        )
        assert plan.budget_limit_cents == 500


class TestDSLValidation:
    """Tests for DSL validation logic."""

    def test_valid_dsl(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl()
        errors = planner._validate_dsl(dsl)
        assert errors == []

    def test_missing_tasks(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = {"version": "1.0", "tasks": []}
        errors = planner._validate_dsl(dsl)
        assert "at least one task" in errors[0].lower()

    def test_missing_task_id(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[{"step_type": "generate_image", "modality": "image"}])
        errors = planner._validate_dsl(dsl)
        assert any("task_id" in e.lower() for e in errors)

    def test_duplicate_task_id(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[
            make_task(task_id="dup"),
            make_task(task_id="dup"),
        ])
        errors = planner._validate_dsl(dsl)
        assert any("duplicate" in e.lower() for e in errors)

    def test_missing_step_type(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[{"task_id": "t1", "modality": "image"}])
        errors = planner._validate_dsl(dsl)
        assert any("step_type" in e.lower() for e in errors)

    def test_invalid_step_type(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[
            {"task_id": "t1", "step_type": "invalid_type", "modality": "image"}
        ])
        errors = planner._validate_dsl(dsl)
        assert any("invalid step_type" in e.lower() for e in errors)

    def test_unknown_dependency(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[
            make_task(task_id="t1", depends_on=["unknown"])
        ])
        errors = planner._validate_dsl(dsl)
        assert any("unknown task" in e.lower() for e in errors)

    def test_invalid_budget(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(budget={"max_cost_cents": -10})
        errors = planner._validate_dsl(dsl)
        assert any("budget" in e.lower() for e in errors)


class TestCycleDetection:
    """Tests for circular dependency detection."""

    def test_no_cycle(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        tasks = [
            {"task_id": "a", "depends_on": []},
            {"task_id": "b", "depends_on": ["a"]},
            {"task_id": "c", "depends_on": ["b"]},
        ]
        cycle = planner._detect_cycle(tasks)
        assert cycle is None

    def test_simple_cycle(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        tasks = [
            {"task_id": "a", "depends_on": ["b"]},
            {"task_id": "b", "depends_on": ["a"]},
        ]
        cycle = planner._detect_cycle(tasks)
        assert cycle is not None
        assert len(cycle) >= 2

    def test_complex_cycle(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        tasks = [
            {"task_id": "a", "depends_on": []},
            {"task_id": "b", "depends_on": ["a", "d"]},
            {"task_id": "c", "depends_on": ["b"]},
            {"task_id": "d", "depends_on": ["c"]},  # Creates cycle: b -> c -> d -> b
        ]
        cycle = planner._detect_cycle(tasks)
        assert cycle is not None


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_simple_sort(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        tasks = [
            TaskStep("c", StepType.GENERATE_IMAGE, "image", depends_on=["b"]),
            TaskStep("a", StepType.GENERATE_IMAGE, "image", depends_on=[]),
            TaskStep("b", StepType.GENERATE_IMAGE, "image", depends_on=["a"]),
        ]
        sorted_tasks = planner._topological_sort(tasks)
        
        # a should come before b, b before c
        ids = [t.task_id for t in sorted_tasks]
        assert ids.index("a") < ids.index("b")
        assert ids.index("b") < ids.index("c")

    def test_parallel_tasks(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        tasks = [
            TaskStep("a", StepType.GENERATE_IMAGE, "image", depends_on=[]),
            TaskStep("b", StepType.GENERATE_IMAGE, "image", depends_on=[]),
            TaskStep("c", StepType.GENERATE_IMAGE, "image", depends_on=["a", "b"]),
        ]
        sorted_tasks = planner._topological_sort(tasks)
        
        ids = [t.task_id for t in sorted_tasks]
        # a and b should come before c
        assert ids.index("a") < ids.index("c")
        assert ids.index("b") < ids.index("c")

    def test_complex_dag(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        # Diamond dependency: a -> b, c -> d, b -> d, c -> d
        tasks = [
            TaskStep("d", StepType.GENERATE_IMAGE, "image", depends_on=["b", "c"]),
            TaskStep("b", StepType.GENERATE_IMAGE, "image", depends_on=["a"]),
            TaskStep("c", StepType.GENERATE_IMAGE, "image", depends_on=["a"]),
            TaskStep("a", StepType.GENERATE_IMAGE, "image", depends_on=[]),
        ]
        sorted_tasks = planner._topological_sort(tasks)
        
        ids = [t.task_id for t in sorted_tasks]
        assert ids.index("a") < ids.index("b")
        assert ids.index("a") < ids.index("c")
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")


class TestCompile:
    """Tests for plan compilation."""

    def test_compile_simple_plan(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(tasks=[
            make_task(task_id="logo"),
            make_task(task_id="banner", depends_on=["logo"]),
        ])
        
        plan = planner.compile(
            tenant_id="test-tenant",
            session_id="session-123",
            dsl=dsl,
        )
        
        assert plan.tenant_id == "test-tenant"
        assert plan.session_id == "session-123"
        assert len(plan.tasks) == 2
        assert plan.total_steps == 2
        assert plan.budget_limit_cents == 100

    def test_compile_with_budget(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = make_dsl(budget={"max_cost_cents": 500, "cost_tier_limit": "medium"})
        
        plan = planner.compile("t", "s", dsl)
        
        assert plan.budget_limit_cents == 500
        assert plan.budget["cost_tier_limit"] == "medium"

    def test_compile_invalid_dsl_raises(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        dsl = {"version": "1.0", "tasks": []}
        
        with pytest.raises(PlanValidationError) as exc_info:
            planner.compile("t", "s", dsl)
        
        assert len(exc_info.value.errors) > 0


class TestRowConversion:
    """Tests for row-to-plan conversion."""

    def test_row_to_plan(self):
        planner = JobPlanner(dsn="postgresql://test@localhost/test")
        plan_id = uuid4()
        
        mock_row = {
            "id": plan_id,
            "tenant_id": "acme-corp",
            "session_id": "session-123",
            "request_id": "req-abc",
            "plan_json": json.dumps({
                "version": "1.0",
                "tasks": [
                    {
                        "task_id": "logo",
                        "step_type": "generate_image",
                        "modality": "image_photo",
                        "depends_on": [],
                        "params": {"prompt": "company logo"},
                        "constraints": {},
                        "quality_gate": {"enabled": True},
                        "on_failure": "fallback",
                        "metadata": {},
                    }
                ],
                "budget": {"max_cost_cents": 100},
                "policy_overrides": {},
                "metadata": {},
            }),
            "plan_version": "1.0",
            "status": "pending",
            "total_steps": 1,
            "completed_steps": 0,
            "budget_limit_cents": 100,
            "budget_used_cents": 0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "error_details": None,
            "created_at": datetime(2025, 12, 16, 10, 0, 0),
        }
        
        plan = planner._row_to_plan(mock_row)
        
        assert plan.id == plan_id
        assert plan.tenant_id == "acme-corp"
        assert len(plan.tasks) == 1
        assert plan.tasks[0].task_id == "logo"
        assert plan.tasks[0].step_type == StepType.GENERATE_IMAGE


# Need json import for test class
import json

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
