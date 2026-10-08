"""PathGuard — sibling-dir, absolute, and home-path refusals (SOMA-ARCH-TOOLS-001)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from services.common.path_guard import (
    PathGuard,
    PathOutsideWorkroot,
    WorkrootNotConfigured,
    guard_for_env,
)


def test_absolute_path_refused():
    with tempfile.TemporaryDirectory() as tmp:
        g = PathGuard(tmp)
        with pytest.raises(PathOutsideWorkroot):
            g.resolve("/etc/passwd")


def test_home_expansion_refused():
    with tempfile.TemporaryDirectory() as tmp:
        g = PathGuard(tmp)
        with pytest.raises(PathOutsideWorkroot):
            g.resolve("~/.ssh/id_rsa")


def test_sibling_directory_escape():
    """startswith('/data/work') must not allow /data/work_evil."""
    with tempfile.TemporaryDirectory() as parent:
        work = Path(parent) / "work"
        evil = Path(parent) / "work_evil"
        work.mkdir()
        evil.mkdir()
        (evil / "secret.txt").write_text("nope")
        g = PathGuard(work)
        with pytest.raises(PathOutsideWorkroot):
            g.resolve("../work_evil/secret.txt")
        # relative that stays inside is fine
        (work / "ok.txt").write_text("yes")
        resolved = g.resolve("ok.txt")
        assert resolved == (work / "ok.txt").resolve()


def test_nested_inside_allowed():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a" / "b").mkdir(parents=True)
        (root / "a" / "b" / "f.md").write_text("x")
        g = PathGuard(root)
        assert g.resolve("a/b/f.md").is_file()


def test_guard_for_env_requires_config(monkeypatch):
    monkeypatch.delenv("TOOL_WORK_DIR", raising=False)
    with pytest.raises(WorkrootNotConfigured):
        guard_for_env("TOOL_WORK_DIR")


def test_tool_policy_unlisted_is_approval():
    from admin.core.tool_calling import ToolPolicy

    p = ToolPolicy(
        auto_execute=("file_read",),
        approval_required=(),
        denied=(),
    )
    assert p.decision("file_read") == "auto_execute"
    assert p.decision("file_write") == "approval_required"
    assert p.decision("shell_exec") == "approval_required"
