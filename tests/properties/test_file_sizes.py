"""Property 1: File Size Limits.

Validates: Requirements 1.7, 2.6, 3.6, 14.1, 14.2

For any Python file in the codebase:
- General files SHALL be less than 500 lines
- Service entry points (main.py) SHALL be less than 150 lines
- Configuration files SHALL be less than 200 lines
"""

import pathlib
from typing import Dict, List, Tuple

# Maximum line counts by file type
MAX_LINES_GENERAL = 500
MAX_LINES_MAIN = 150
MAX_LINES_CONFIG = 200

# Files with known violations (tracked for decomposition)
# These are the baseline - tests will fail if new violations appear
KNOWN_VIOLATIONS: Dict[str, int] = {
    # Requirement 1: ConversationWorker (3022 lines, target < 150)
    "services/conversation_worker/main.py": 3022,
    # Requirement 2: Agent module (4092 lines, target < 200)
    "agent.py": 4092,
    # Requirement 4: Settings (610 lines after decomposition, target < 200)
    "python/helpers/settings.py": 610,
    # Requirement 5: Task scheduler (1276 lines, target < 300)
    "python/helpers/task_scheduler.py": 1276,
    # Requirement 6: MCP handler (1087 lines, target < 300)
    "python/helpers/mcp_handler.py": 1087,
    # Requirement 7: Memory (1010 lines, target < 300)
    "python/helpers/memory.py": 1010,
    # Requirement 10: Core tasks (764 lines, target split)
    "python/tasks/core_tasks.py": 764,
    # Requirement 9: Session repository (681 lines, target < 300)
    "services/common/session_repository.py": 681,
    # Requirement 8: Gateway main (438 lines, target < 100)
    "services/gateway/main.py": 438,
    # Additional violations discovered during baseline
    # "clean_agent.py": 764,  # DELETED - dead code, never imported
    "models.py": 1089,
    "observability/metrics.py": 650,
    "python/helpers/backup.py": 776,
    "python/helpers/document_query.py": 522,
    "python/helpers/memory_consolidation.py": 682,
    "python/integrations/soma_client.py": 902,  # Updated: added neuromodulation endpoints
    "services/delegation_gateway/main.py": 176,
    "services/memory_sync/main.py": 182,
    "services/outbox_sync/main.py": 206,
    "services/tool_executor/main.py": 748,
    # Config files (allowed up to 400 for now - complex domain)
    "src/core/config/__init__.py": 258,
    "src/core/config/loader.py": 284,
    "src/core/config/models.py": 313,
    "src/core/config/registry.py": 391,
}

# Directories to skip
SKIP_DIRS = {
    ".venv",
    "node_modules",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "venv",
    "env",
}


def _count_lines(filepath: pathlib.Path) -> int:
    """Count non-empty lines in a file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return len([line for line in content.splitlines() if line.strip()])
    except Exception:
        return 0


def _should_skip(filepath: pathlib.Path) -> bool:
    """Check if file should be skipped."""
    parts = filepath.parts
    return any(skip in parts for skip in SKIP_DIRS)


def _get_max_lines(filepath: pathlib.Path, rel_path: str) -> int:
    """Get maximum allowed lines for a file."""
    if filepath.name == "main.py":
        return MAX_LINES_MAIN
    if "config" in rel_path.lower():
        return MAX_LINES_CONFIG
    return MAX_LINES_GENERAL


def test_no_new_file_size_violations():
    """Verify no new files exceed size limits.

    Property 1: File Size Limits
    Validates: Requirements 1.7, 2.6, 3.6, 14.1, 14.2

    Known violations are tracked in KNOWN_VIOLATIONS.
    This test fails if:
    1. A new file exceeds limits
    2. A known violation gets worse (more lines)
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    new_violations: List[Tuple[str, int, int]] = []
    worse_violations: List[Tuple[str, int, int, int]] = []

    for filepath in repo.rglob("*.py"):
        if _should_skip(filepath):
            continue

        rel_path = filepath.relative_to(repo).as_posix()
        line_count = _count_lines(filepath)
        max_lines = _get_max_lines(filepath, rel_path)

        if line_count > max_lines:
            if rel_path in KNOWN_VIOLATIONS:
                # Check if it got worse
                known_count = KNOWN_VIOLATIONS[rel_path]
                if line_count > known_count + 50:  # Allow small fluctuation
                    worse_violations.append((rel_path, known_count, line_count, max_lines))
            else:
                new_violations.append((rel_path, line_count, max_lines))

    errors = []

    if new_violations:
        errors.append("New file size violations:")
        for path, count, max_l in sorted(new_violations):
            errors.append(f"  {path}: {count} lines (max {max_l})")

    if worse_violations:
        errors.append("Known violations got worse:")
        for path, old, new, max_l in sorted(worse_violations):
            errors.append(f"  {path}: {old} -> {new} lines (max {max_l})")

    assert not errors, "\n".join(errors)


def test_file_size_improvement_tracking():
    """Track progress on reducing known violations.

    This test reports improvements but does not fail.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    improvements: List[Tuple[str, int, int]] = []

    for rel_path, known_count in KNOWN_VIOLATIONS.items():
        filepath = repo / rel_path
        if not filepath.exists():
            continue

        current_count = _count_lines(filepath)
        if current_count < known_count - 50:  # Significant improvement
            improvements.append((rel_path, known_count, current_count))

    # This is informational - update KNOWN_VIOLATIONS when files are decomposed
    if improvements:
        print("\nFile size improvements detected:")
        for path, old, new in sorted(improvements):
            print(f"  {path}: {old} -> {new} lines")
