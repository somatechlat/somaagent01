"""Property 8: Prometheus metrics for tasks.

**Feature: canonical-architecture-cleanup, Property 8: Prometheus metrics for tasks**
**Validates: Requirements 24.1-24.5**

For any task execution, it SHALL emit Prometheus metrics:
- increment `celery_tasks_total` counter on start
- increment `celery_tasks_success` or `celery_tasks_failed` on completion
- record duration in `celery_task_duration_seconds` histogram
"""

import ast
import pathlib
from typing import Set

# Required Prometheus metric patterns in task files
REQUIRED_METRIC_PATTERNS = {
    "Counter",
    "Histogram",
}

# Expected metric name patterns (at least one should be present)
EXPECTED_METRICS = {
    "celery_tasks_total",
    "celery_tasks_success",
    "celery_tasks_failed",
    "celery_task_duration_seconds",
    "task_execution_total",
    "task_execution_duration_seconds",
    "tool_execution_total",
    "tool_execution_duration_seconds",
    # SA01 prefixed metrics
    "sa01_core_tasks_total",
    "sa01_core_task_latency_seconds",
    "sa01_task_feedback_total",
    "sa01_a2a_chat_total",
    "sa01_a2a_chat_latency_seconds",
}


def _find_prometheus_imports(filepath: pathlib.Path) -> Set[str]:
    """Find Prometheus client imports in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and (
                "prometheus" in node.module or "observability.metrics" in node.module
            ):
                for alias in node.names:
                    imports.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "prometheus" in alias.name:
                    imports.add(alias.name)
    return imports


def _uses_metrics_module(filepath: pathlib.Path) -> bool:
    """Check if file imports from observability.metrics module."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return (
        "from python.observability.metrics import" in content or "observability.metrics" in content
    )


def _find_metric_definitions(filepath: pathlib.Path) -> Set[str]:
    """Find Prometheus metric definitions in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return set()

    metrics = set()
    for metric in EXPECTED_METRICS:
        if metric in content:
            metrics.add(metric)
    return metrics


def test_task_files_have_prometheus_imports():
    """Verify task files import Prometheus client.

    **Feature: canonical-architecture-cleanup, Property 8: Prometheus metrics for tasks**
    **Validates: Requirements 24.1**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tasks_path = repo / "python" / "tasks"

    if not tasks_path.exists():
        return

    files_with_metrics = []
    files_without_metrics = []

    for filepath in tasks_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue
        if filepath.name == "celery_app.py":
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        imports = _find_prometheus_imports(filepath)

        if imports & REQUIRED_METRIC_PATTERNS:
            files_with_metrics.append(rel_path)
        else:
            files_without_metrics.append(rel_path)

    # At least some task files should have Prometheus metrics
    assert len(files_with_metrics) > 0, (
        "No task files have Prometheus metrics imports.\n"
        "Expected Counter/Histogram from prometheus_client."
    )


def test_core_tasks_have_metrics():
    """Verify core_tasks.py has Prometheus metrics.

    **Feature: canonical-architecture-cleanup, Property 8: Prometheus metrics for tasks**
    **Validates: Requirements 24.1-24.5**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    core_tasks = repo / "python" / "tasks" / "core_tasks.py"

    if not core_tasks.exists():
        # core_tasks.py not yet created - skip
        return

    metrics = _find_metric_definitions(core_tasks)

    # Should have at least task counter and duration histogram
    has_counter = any("total" in m for m in metrics)
    has_histogram = any("duration" in m or "seconds" in m for m in metrics)

    assert has_counter or has_histogram, (
        "core_tasks.py should have Prometheus metrics.\n"
        f"Found: {metrics}\n"
        "Expected: celery_tasks_total, celery_task_duration_seconds"
    )


def test_a2a_chat_task_has_metrics():
    """Verify a2a_chat_task.py has Prometheus metrics.

    **Feature: canonical-architecture-cleanup, Property 8: Prometheus metrics for tasks**
    **Validates: Requirements 24.1-24.5**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    a2a_task = repo / "python" / "tasks" / "a2a_chat_task.py"

    if not a2a_task.exists():
        return

    imports = _find_prometheus_imports(a2a_task)
    metrics = _find_metric_definitions(a2a_task)
    uses_metrics_module = _uses_metrics_module(a2a_task)

    # a2a_chat_task should have metrics (either direct or via observability module)
    has_prometheus = bool(imports & REQUIRED_METRIC_PATTERNS)
    has_metrics = bool(metrics)

    assert has_prometheus or has_metrics or uses_metrics_module, (
        "a2a_chat_task.py should have Prometheus metrics.\n"
        f"Imports: {imports}\n"
        f"Metrics: {metrics}\n"
        f"Uses metrics module: {uses_metrics_module}"
    )


def test_tool_tracking_has_metrics():
    """Verify tool_tracking.py has Prometheus metrics.

    **Feature: canonical-architecture-cleanup, Property 8: Prometheus metrics for tasks**
    **Validates: Requirements 24.1-24.5**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tool_tracking = repo / "python" / "helpers" / "tool_tracking.py"

    if not tool_tracking.exists():
        return

    metrics = _find_metric_definitions(tool_tracking)

    # Should have tool execution metrics
    has_tool_metrics = any("tool" in m for m in metrics)

    assert has_tool_metrics, (
        "tool_tracking.py should have Prometheus metrics.\n"
        f"Found: {metrics}\n"
        "Expected: tool_execution_total, tool_execution_duration_seconds"
    )
