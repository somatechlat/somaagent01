"""Property 1: No persist_chat imports.

**Feature: canonical-architecture-cleanup, Property 1: No persist_chat imports**
**Validates: Requirements 1.1-1.8**

For any Python file in the codebase, it SHALL NOT contain imports from the
deleted `persist_chat` module. The module was deleted as part of the canonical
architecture cleanup - all session persistence now uses PostgresSessionStore.
"""

import pathlib
from typing import Set

# Forbidden imports from the deleted persist_chat module
FORBIDDEN_PERSIST_CHAT_IMPORTS: Set[str] = {
    "from python.helpers import persist_chat",
    "from python.helpers.persist_chat import",
    "import python.helpers.persist_chat",
    "persist_chat.save_tmp_chat",
    "persist_chat.remove_chat",
    "persist_chat.get_chat_folder_path",
    "persist_chat.get_chat_msg_files_folder",
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
    ".kiro",
}

# Files to skip (test files that contain the forbidden strings as test data)
SKIP_FILES = {
    "tests/properties/test_no_persist_chat.py",
}


def _should_skip(filepath: pathlib.Path, repo: pathlib.Path) -> bool:
    """Check if file should be skipped."""
    parts = filepath.parts
    if any(skip in parts for skip in SKIP_DIRS):
        return True
    rel_path = filepath.relative_to(repo).as_posix()
    return rel_path in SKIP_FILES


def test_no_persist_chat_imports():
    """Property 1: No file imports persist_chat.

    **Feature: canonical-architecture-cleanup, Property 1: No persist_chat imports**
    **Validates: Requirements 1.1-1.8**

    The persist_chat module was deleted as part of the canonical architecture
    cleanup. All session persistence now uses PostgresSessionStore.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    violations: list[str] = []

    for filepath in repo.rglob("*.py"):
        if _should_skip(filepath, repo):
            continue

        rel_path = filepath.relative_to(repo).as_posix()

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for forbidden in FORBIDDEN_PERSIST_CHAT_IMPORTS:
            if forbidden in content:
                violations.append(f"{rel_path}: contains '{forbidden}'")

    assert not violations, (
        "Files still reference deleted persist_chat module:\n"
        + "\n".join(sorted(set(violations)))
        + "\n\nMigrate to PostgresSessionStore for session persistence."
    )


def test_no_save_tmp_chat_calls():
    """Verify no direct calls to save_tmp_chat function.

    **Validates: Requirements 1.1**

    The save_tmp_chat function was part of the deleted persist_chat module.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    violations: list[str] = []

    for filepath in repo.rglob("*.py"):
        if _should_skip(filepath, repo):
            continue

        rel_path = filepath.relative_to(repo).as_posix()

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if "save_tmp_chat(" in content:
            violations.append(f"{rel_path}: calls save_tmp_chat()")

    assert not violations, "Files still call deleted save_tmp_chat function:\n" + "\n".join(
        sorted(set(violations))
    )


def test_no_remove_chat_calls():
    """Verify no direct calls to remove_chat function.

    **Validates: Requirements 1.4, 1.5, 1.6**

    The remove_chat function was part of the deleted persist_chat module.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]

    violations: list[str] = []

    for filepath in repo.rglob("*.py"):
        if _should_skip(filepath, repo):
            continue

        rel_path = filepath.relative_to(repo).as_posix()

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Check for remove_chat but not PostgresSessionStore.delete_session
        if "remove_chat(" in content and "def remove_chat" not in content:
            violations.append(f"{rel_path}: calls remove_chat()")

    assert not violations, "Files still call deleted remove_chat function:\n" + "\n".join(
        sorted(set(violations))
    )
