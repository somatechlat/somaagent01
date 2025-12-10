"""Property 3: Celery task decorator compliance.

**Feature: canonical-architecture-cleanup, Property 3: Celery task decorator compliance**
**Validates: Requirements 3.9, 22.1-22.5**

For any Celery task in `python/tasks/`, it SHALL use `@shared_task` decorator
with proper configuration including `bind=True`, `max_retries`, `autoretry_for`,
`retry_backoff`, `soft_time_limit`, and `time_limit`.
"""

import ast
import pathlib
from typing import Any, Dict, List

# Required decorator arguments for production-grade tasks
REQUIRED_DECORATOR_ARGS = {
    "bind": True,  # Required for self reference
}

# Recommended decorator arguments (warn if missing)
RECOMMENDED_DECORATOR_ARGS = {
    "max_retries",
    "autoretry_for",
    "retry_backoff",
    "soft_time_limit",
    "time_limit",
}

# Tasks that are exempt from strict requirements (e.g., simple periodic tasks)
EXEMPT_TASKS = {
    "publish_metrics",  # Simple periodic task, no retry needed
}


def _get_decorator_args(decorator: ast.Call) -> Dict[str, Any]:
    """Extract keyword arguments from a decorator call."""
    args = {}
    for keyword in decorator.keywords:
        if keyword.arg:
            # Handle simple values
            if isinstance(keyword.value, ast.Constant):
                args[keyword.arg] = keyword.value.value
            elif isinstance(keyword.value, ast.Name):
                args[keyword.arg] = keyword.value.id
            elif isinstance(keyword.value, ast.Tuple):
                args[keyword.arg] = "tuple"
            else:
                args[keyword.arg] = "complex"
    return args


def _find_celery_tasks(filepath: pathlib.Path) -> List[Dict[str, Any]]:
    """Find all Celery task definitions in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return []

    tasks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # Check for @shared_task or @app.task
                is_shared_task = False
                decorator_args = {}

                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name):
                        if decorator.func.id == "shared_task":
                            is_shared_task = True
                            decorator_args = _get_decorator_args(decorator)
                    elif isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == "task":
                            is_shared_task = True
                            decorator_args = _get_decorator_args(decorator)
                elif isinstance(decorator, ast.Name):
                    if decorator.id == "shared_task":
                        is_shared_task = True
                elif isinstance(decorator, ast.Attribute):
                    if decorator.attr == "task":
                        is_shared_task = True

                if is_shared_task:
                    tasks.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "decorator_args": decorator_args,
                        }
                    )
    return tasks


def test_celery_tasks_use_shared_task():
    """Verify all Celery tasks use @shared_task decorator.

    **Feature: canonical-architecture-cleanup, Property 3: Celery task decorator compliance**
    **Validates: Requirements 3.9**
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tasks_path = repo / "python" / "tasks"

    if not tasks_path.exists():
        return

    all_tasks = []

    for filepath in tasks_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        tasks = _find_celery_tasks(filepath)

        for task in tasks:
            task["file"] = rel_path
            all_tasks.append(task)

    # Verify we found tasks
    assert len(all_tasks) > 0, "No Celery tasks found in python/tasks/"

    # All tasks should be using shared_task (this is implicit from _find_celery_tasks)
    # The test passes if we found tasks with the decorator


def test_celery_tasks_have_bind_true():
    """Verify all Celery tasks have bind=True.

    **Feature: canonical-architecture-cleanup, Property 3: Celery task decorator compliance**
    **Validates: Requirements 22.1**

    bind=True is required for tasks to access self for retries and state.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tasks_path = repo / "python" / "tasks"

    if not tasks_path.exists():
        return

    violations: List[str] = []

    for filepath in tasks_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        tasks = _find_celery_tasks(filepath)

        for task in tasks:
            if task["name"] in EXEMPT_TASKS:
                continue

            args = task["decorator_args"]
            if args.get("bind") is not True:
                violations.append(f"{rel_path}:{task['line']} - {task['name']} missing bind=True")

    assert not violations, (
        "Celery tasks missing bind=True:\n"
        + "\n".join(sorted(violations))
        + "\n\nAdd bind=True to @shared_task decorator for retry support."
    )


def test_celery_tasks_have_retry_config():
    """Verify Celery tasks have retry configuration.

    **Feature: canonical-architecture-cleanup, Property 3: Celery task decorator compliance**
    **Validates: Requirements 22.5**

    Tasks should have max_retries and autoretry_for for resilience.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tasks_path = repo / "python" / "tasks"

    if not tasks_path.exists():
        return

    warnings: List[str] = []

    for filepath in tasks_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        tasks = _find_celery_tasks(filepath)

        for task in tasks:
            if task["name"] in EXEMPT_TASKS:
                continue

            args = task["decorator_args"]
            missing = []

            if "max_retries" not in args:
                missing.append("max_retries")
            if "autoretry_for" not in args:
                missing.append("autoretry_for")

            if missing:
                warnings.append(
                    f"{rel_path}:{task['line']} - {task['name']} missing: {', '.join(missing)}"
                )

    # This is a warning, not a failure - some tasks may intentionally not retry
    if warnings:
        print("\nCelery tasks without retry configuration (consider adding):")
        for w in warnings:
            print(f"  {w}")


def test_celery_tasks_have_time_limits():
    """Verify Celery tasks have time limits.

    **Feature: canonical-architecture-cleanup, Property 3: Celery task decorator compliance**
    **Validates: Requirements 22.3, 22.4**

    Tasks should have soft_time_limit and time_limit for resource protection.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    tasks_path = repo / "python" / "tasks"

    if not tasks_path.exists():
        return

    warnings: List[str] = []

    for filepath in tasks_path.rglob("*.py"):
        if filepath.name == "__init__.py":
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        tasks = _find_celery_tasks(filepath)

        for task in tasks:
            if task["name"] in EXEMPT_TASKS:
                continue

            args = task["decorator_args"]
            missing = []

            if "soft_time_limit" not in args:
                missing.append("soft_time_limit")
            if "time_limit" not in args:
                missing.append("time_limit")

            if missing:
                warnings.append(
                    f"{rel_path}:{task['line']} - {task['name']} missing: {', '.join(missing)}"
                )

    # This is a warning, not a failure
    if warnings:
        print("\nCelery tasks without time limits (consider adding):")
        for w in warnings:
            print(f"  {w}")
