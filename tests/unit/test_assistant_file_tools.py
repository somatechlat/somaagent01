"""Assistant file tools — PathGuard escape, workroot roundtrip, unlisted→approval.

SOMA-ARCH-TOOLS-001 W3.1–W3.2: file_list / file_search / file_write / file_patch.
"""

from __future__ import annotations

import hashlib

import pytest

from services.tool_executor.assistant_tools import (
    ASSISTANT_TOOL_NAMES,
    FileListTool,
    FilePatchTool,
    FileSearchTool,
    FileWriteTool,
)
from services.tool_executor.tools import AVAILABLE_TOOLS, FileReadTool, ToolExecutionError

ESCAPE_CASES = [
    ("file_list", {"path": "../outside"}),
    ("file_search", {"query": "x", "path": "../outside"}),
    ("file_write", {"path": "../outside.txt", "content": "x"}),
    ("file_patch", {"path": "../outside.txt", "old": "a", "new": "b"}),
]


@pytest.fixture
def workroot(tmp_path, monkeypatch):
    """A real TOOL_WORK_DIR workroot — server-side, never a model arg."""
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    return tmp_path


# ---------------------------------------------------------------------------
# Registration / catalog
# ---------------------------------------------------------------------------


def test_registered_in_available_tools_with_clear_schemas():
    assert set(ASSISTANT_TOOL_NAMES) == {
        "file_list",
        "file_search",
        "file_write",
        "file_patch",
    }
    tiers = {"file_list": 1, "file_search": 1, "file_write": 2, "file_patch": 2}
    required = {
        "file_list": [],
        "file_search": ["query"],
        "file_write": ["path", "content"],
        "file_patch": ["path", "old", "new"],
    }
    for name, tier in tiers.items():
        tool = AVAILABLE_TOOLS.get(name)
        assert tool is not None, name
        assert tool.tier == tier, name
        assert tool.description.strip(), name
        schema = tool.input_schema()
        assert schema["type"] == "object"
        assert schema.get("required", []) == required[name], name


# ---------------------------------------------------------------------------
# PathGuard escape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("name,args", ESCAPE_CASES)
async def test_sibling_escape_refused(name, args, workroot):
    with pytest.raises(ToolExecutionError) as exc:
        await AVAILABLE_TOOLS[name].run(dict(args))
    assert "escape" in str(exc.value)


@pytest.mark.asyncio
async def test_absolute_path_refused(workroot):
    with pytest.raises(ToolExecutionError) as exc:
        await FileListTool().run({"path": "/etc"})
    assert "absolute" in str(exc.value)


@pytest.mark.asyncio
async def test_missing_workroot_fails_closed(monkeypatch):
    monkeypatch.delenv("TOOL_WORK_DIR", raising=False)
    with pytest.raises(ToolExecutionError) as exc:
        await FileListTool().run({})
    assert "TOOL_WORK_DIR" in str(exc.value)


# ---------------------------------------------------------------------------
# Write / read / list / search / patch roundtrip inside a tmp workroot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_read_list_search_patch_roundtrip(workroot):
    content = "hello soma\nline two\n"
    payload = content.encode("utf-8")

    written = await FileWriteTool().run({"path": "notes/hello.md", "content": content})
    assert written == {
        "path": "notes/hello.md",
        "bytes": len(payload),
        "hash": hashlib.sha256(payload).hexdigest(),
    }
    on_disk = workroot / "notes" / "hello.md"
    assert on_disk.read_bytes() == payload

    read = await FileReadTool().run({"path": "notes/hello.md"})
    assert read["content"] == content

    listing = await FileListTool().run({"path": "notes"})
    assert listing["path"] == "notes"
    assert listing["count"] == 1
    # Metadata only — no content dump.
    assert listing["entries"] == [
        {"name": "hello.md", "type": "file", "size": len(payload)}
    ]
    assert listing["truncated"] is False

    root_listing = await FileListTool().run({})
    assert root_listing["path"] == "."
    assert {"name": "notes", "type": "dir", "size": None} in root_listing["entries"]

    filtered = await FileListTool().run({"path": "notes", "glob": "*.md"})
    assert filtered["count"] == 1
    assert filtered["entries"][0]["name"] == "hello.md"

    search = await FileSearchTool().run({"query": "SOMA"})  # case-insensitive
    assert search["match_count"] == 1
    assert search["truncated"] is False
    match = search["matches"][0]
    assert match["path"] == "notes/hello.md"
    assert match["line"] == 1
    assert "hello soma" in match["text"]

    patched = await FilePatchTool().run(
        {"path": "notes/hello.md", "old": "hello soma", "new": "goodbye soma"}
    )
    assert patched["path"] == "notes/hello.md"
    assert patched["replacements"] == 1
    assert patched["bytes_before"] == len(payload)
    after = await FileReadTool().run({"path": "notes/hello.md"})
    assert "goodbye soma" in after["content"]
    assert "hello soma" not in after["content"]
    assert patched["hash"] == hashlib.sha256(after["content"].encode("utf-8")).hexdigest()


@pytest.mark.asyncio
async def test_write_overwrites_and_refuses_directories(workroot):
    tool = FileWriteTool()
    await tool.run({"path": "a.txt", "content": "one"})
    res = await tool.run({"path": "a.txt", "content": "two"})
    assert res["bytes"] == 3
    assert (workroot / "a.txt").read_text() == "two"

    (workroot / "sub").mkdir()
    with pytest.raises(ToolExecutionError) as exc:
        await tool.run({"path": "sub", "content": "x"})
    assert "not a writable file" in str(exc.value)


@pytest.mark.asyncio
async def test_patch_fails_unless_old_occurs_exactly_once(workroot):
    (workroot / "p.txt").write_text("a b a", encoding="utf-8")
    tool = FilePatchTool()

    with pytest.raises(ToolExecutionError) as exc:
        await tool.run({"path": "p.txt", "old": "zzz", "new": "y"})
    assert "not found" in str(exc.value)

    with pytest.raises(ToolExecutionError) as exc:
        await tool.run({"path": "p.txt", "old": "a", "new": "y"})
    assert "exactly once" in str(exc.value)

    with pytest.raises(ToolExecutionError):
        await tool.run({"path": "p.txt", "old": "", "new": "y"})

    # Patch is fail-closed: failed calls never touched the file.
    assert (workroot / "p.txt").read_text() == "a b a"


# ---------------------------------------------------------------------------
# Unlisted policy → approval (SOMA-ARCH-TOOLS-001 §7)
# ---------------------------------------------------------------------------


def test_unlisted_assistant_tools_default_to_approval():
    from admin.core.tool_calling import ToolPolicy

    legacy = ToolPolicy(
        auto_execute=("timestamp", "memory_recall", "file_read"),
        approval_required=(),
        denied=(),
    )
    for name in ASSISTANT_TOOL_NAMES:
        assert legacy.decision(name) == "approval_required", name

    explicit = ToolPolicy(
        auto_execute=("file_list", "file_search", "file_read"),
        approval_required=("file_write", "file_patch"),
        denied=(),
    )
    assert explicit.decision("file_list") == "auto_execute"
    assert explicit.decision("file_search") == "auto_execute"
    assert explicit.decision("file_write") == "approval_required"
    assert explicit.decision("file_patch") == "approval_required"

    opt_in_auto = ToolPolicy(auto_execute=ASSISTANT_TOOL_NAMES, approval_required=(), denied=())
    for name in ASSISTANT_TOOL_NAMES:
        assert opt_in_auto.decision(name) == "auto_execute", name
