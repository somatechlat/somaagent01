#!/usr/bin/env python3
"""Check file sizes against configured limits.

This script enforces file size limits as part of the architecture refactor.
It can be run as a pre-commit hook or standalone.

Usage:
    python scripts/check_file_sizes.py [--fix] [files...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# File size limits (lines)
LIMITS = {
    # Main entry points should be thin
    "**/main.py": 150,
    "**/service.py": 200,
    # Helper modules
    "python/helpers/*.py": 300,
    # Task modules
    # Agent modules
    "python/somaagent/*.py": 200,
    # Default for all Python files
    "**/*.py": 500,
}

# Files to exclude from checks
EXCLUDE = {
    "__pycache__",
    "node_modules",
    ".venv",
    "migrations",
    "tests",
    "*_test.py",
    "test_*.py",
    "conftest.py",
}


def count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def matches_pattern(path: Path, pattern: str) -> bool:
    """Check if path matches a glob pattern."""
    from fnmatch import fnmatch

    return fnmatch(str(path), pattern) or fnmatch(path.name, pattern)


def is_excluded(path: Path) -> bool:
    """Check if path should be excluded."""
    path_str = str(path)
    for part in path.parts:
        if part in EXCLUDE:
            return True
    return any(matches_pattern(path, pat) for pat in EXCLUDE)


def get_limit(path: Path) -> int:
    """Get the line limit for a file."""
    for pattern, limit in LIMITS.items():
        if matches_pattern(path, pattern):
            return limit
    return LIMITS.get("**/*.py", 500)


def check_file(path: Path) -> tuple[bool, int, int]:
    """Check a single file against its limit.

    Returns:
        Tuple of (passed, lines, limit)
    """
    if is_excluded(path):
        return True, 0, 0

    lines = count_lines(path)
    limit = get_limit(path)
    return lines <= limit, lines, limit


def main() -> int:
    """Execute main."""

    parser = argparse.ArgumentParser(description="Check file sizes")
    parser.add_argument("files", nargs="*", help="Files to check")
    parser.add_argument("--all", action="store_true", help="Check all Python files")
    args = parser.parse_args()

    if args.all:
        files = list(Path(".").rglob("*.py"))
    elif args.files:
        files = [Path(f) for f in args.files if f.endswith(".py")]
    else:
        # Default: check staged files (for pre-commit)
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
        )
        files = [Path(f) for f in result.stdout.strip().split("\n") if f.endswith(".py")]

    failures = []
    for path in files:
        if not path.exists():
            continue
        passed, lines, limit = check_file(path)
        if not passed:
            failures.append((path, lines, limit))

    if failures:
        print("❌ File size limit violations:")
        for path, lines, limit in failures:
            print(f"  {path}: {lines} lines (limit: {limit})")
        print(f"\n{len(failures)} file(s) exceed size limits.")
        print("Consider decomposing large files into smaller modules.")
        return 1

    print(f"✅ All {len(files)} file(s) within size limits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
