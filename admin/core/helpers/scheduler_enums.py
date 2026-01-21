"""Scheduler enums and metrics.

This module contains enums and Prometheus metrics for task scheduling.
Extracted from scheduler_models.py for 650-line compliance.
"""

from __future__ import annotations

from enum import Enum

from prometheus_client import Counter, Histogram


# =============================================================================
# TASK ENUMS
# =============================================================================


class TaskState(str, Enum):
    """Task execution state."""

    IDLE = "idle"
    RUNNING = "running"
    DISABLED = "disabled"
    ERROR = "error"


class TaskType(str, Enum):
    """Type of scheduled task."""

    AD_HOC = "adhoc"
    SCHEDULED = "scheduled"
    PLANNED = "planned"


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

task_schedule_evaluations_total = Counter(
    "sa01_task_schedule_evaluations_total",
    "Number of schedule evaluations per task",
    ["task"],
)

task_schedule_latency_seconds = Histogram(
    "sa01_task_schedule_latency_seconds",
    "Latency of schedule evaluation per task",
    ["task"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)
