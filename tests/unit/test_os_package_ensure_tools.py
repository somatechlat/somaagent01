"""os_packages_ensure — TOOLS-001 §5.4.1 allowlisted container OS packages.

Covers the small OS allowlist + profiles, the fail-closed refusals (unknown
profile/package, no tenant), the Temporal start hook with a fake client, the
workflow's in-worker allowlist re-gate, argv-only ``apt-get`` / ``which``
invocations with a mocked subprocess, and worker/default-kit/policy wiring —
no Temporal server, no network, no real apt.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from services.tool_executor.os_package_profiles import (
    OS_PACKAGE_ALLOWLIST,
    OS_PACKAGE_BINARIES,
    OS_PACKAGE_PROFILES,
    OS_PROFILE_IDS,
    filter_os_allowlisted,
    os_binary_for,
    resolve_os_profile,
)
from services.tool_executor.tools import ToolExecutionError


# ---------------------------------------------------------------------------
# Allowlist + profiles (operator-owned, deliberately small)
# ---------------------------------------------------------------------------


def test_allowlist_is_union_of_profiles_and_stays_small():
    union = {n for names in OS_PACKAGE_PROFILES.values() for n in names}
    assert OS_PACKAGE_ALLOWLIST == frozenset(union)
    # The GO pins this allowlist: operator extends, model never does.
    assert OS_PACKAGE_ALLOWLIST == frozenset(
        {"ffmpeg", "imagemagick", "poppler-utils", "unzip"}
    )


def test_every_allowlisted_package_has_a_verify_binary():
    for pkg in OS_PACKAGE_ALLOWLIST:
        assert pkg in OS_PACKAGE_BINARIES
        assert OS_PACKAGE_BINARIES[pkg]


def test_resolve_profile_returns_members_and_tolerates_case():
    assert resolve_os_profile("media") == ["ffmpeg", "imagemagick"]
    assert resolve_os_profile("  DOCS ") == ["poppler-utils", "unzip"]


def test_unknown_profile_fails_closed():
    with pytest.raises(KeyError):
        resolve_os_profile("hax")
    with pytest.raises(KeyError):
        resolve_os_profile("")


def test_filter_splits_denied_and_canonicalizes():
    allowed, denied = filter_os_allowlisted(
        ["FFMPEG", "curl", "", "unzip", "ffmpeg"]
    )
    assert allowed == ["ffmpeg", "unzip"]
    assert denied == ["curl"]


def test_filter_empty_input_passes_through():
    assert filter_os_allowlisted([]) == ([], [])
    assert filter_os_allowlisted(None) == ([], [])


def test_os_binary_for_is_fail_closed_on_unknown():
    assert os_binary_for("ffmpeg") == "ffmpeg"
    assert os_binary_for("imagemagick") == "convert"
    assert os_binary_for("not-a-curated-package") == ""


# ---------------------------------------------------------------------------
# Fixtures: fake Temporal client (same shape as packages_ensure tests)
# ---------------------------------------------------------------------------


class _FakeHandle:
    def __init__(self):
        self._desc = SimpleNamespace(
            status=SimpleNamespace(name="RUNNING"),
            start_time="2026-10-09T00:00:00+00:00",
            close_time=None,
        )
        self.progress = None

    async def describe(self):
        return self._desc

    async def query(self, fn):
        return self.progress


class _FakeClient:
    def __init__(self, handle):
        self._handle = handle
        self.started = None

    def get_workflow_handle(self, *, workflow_id):
        self._handle.workflow_id = workflow_id
        return self._handle

    async def start_workflow(self, fn, arg, *, id, task_queue):
        self.started = {"id": id, "task_queue": task_queue, "arg": arg, "fn": fn}


@pytest.fixture
def temporal_fake(monkeypatch):
    pytest.importorskip("temporalio")
    handle = _FakeHandle()
    client = _FakeClient(handle)

    async def _fake_client():
        return client

    import services.gateway.providers as providers

    monkeypatch.setattr(providers, "get_temporal_client", _fake_client)
    monkeypatch.setattr(
        "django.conf.settings.TEMPORAL_CONVERSATION_QUEUE", "conversation", raising=False
    )
    return client, handle


# ---------------------------------------------------------------------------
# Tool — start hook + fail-closed paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_os_packages_ensure_starts_workflow(temporal_fake):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    result = await OsPackagesEnsureTool().run(
        {
            "profile": "media",
            "packages": ["unzip"],
            # server-side identity as the tool loop injects it:
            "tenant_id": "t-1",
            "capsule_id": "cap-1",
        }
    )
    assert result["status"] == "started"
    assert result["workflow_id"].startswith("os-package-ensure-t-1-media-")
    assert client.started is not None
    assert client.started["id"] == result["workflow_id"]
    assert client.started["task_queue"] == "conversation"
    arg = client.started["arg"]
    assert arg.tenant_id == "t-1"
    assert arg.capsule_id == "cap-1"
    packages = list(arg.packages)
    assert "ffmpeg" in packages and "unzip" in packages
    # Only allowlisted names ever reach the workflow input.
    assert set(packages) <= set(OS_PACKAGE_ALLOWLIST)
    assert len(packages) == len(set(packages))


@pytest.mark.asyncio
async def test_unknown_os_profile_refused(temporal_fake):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="unknown OS profile"):
        await OsPackagesEnsureTool().run({"profile": "hax", "tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_unknown_package_refused(temporal_fake):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="operator OS allowlist"):
        await OsPackagesEnsureTool().run(
            {"packages": ["evilpkg"], "tenant_id": "t-1"}
        )
    assert client.started is None


@pytest.mark.asyncio
async def test_shell_like_input_is_not_a_field(temporal_fake):
    """No shell/argv/command fields — structured {profile|packages[]} only."""
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    tool = OsPackagesEnsureTool()
    assert set(tool.input_schema()["properties"]) == {"profile", "packages"}
    # Extra shell-ish args are ignored, never interpreted as a command.
    result = await tool.run(
        {
            "profile": "docs",
            "tenant_id": "t-1",
            "command": "rm -rf /",
            "shell": "apt-get install anything",
        }
    )
    assert result["status"] == "started"
    assert set(result["packages"]) <= set(OS_PACKAGE_ALLOWLIST)


@pytest.mark.asyncio
async def test_requires_tenant(temporal_fake):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="capsule tenant"):
        await OsPackagesEnsureTool().run({"profile": "media"})
    assert client.started is None


@pytest.mark.asyncio
async def test_no_profile_or_packages_refused(temporal_fake):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="requires profile"):
        await OsPackagesEnsureTool().run({"tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_missing_task_queue_refuses_to_guess(temporal_fake, monkeypatch):
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    client, _ = temporal_fake
    monkeypatch.setattr(
        "django.conf.settings.TEMPORAL_CONVERSATION_QUEUE", "", raising=False
    )
    with pytest.raises(ToolExecutionError, match="guess a task queue"):
        await OsPackagesEnsureTool().run({"profile": "media", "tenant_id": "t-1"})
    assert client.started is None


# ---------------------------------------------------------------------------
# Workflow activities — allowlist re-gate + argv-only subprocess (mocked)
# ---------------------------------------------------------------------------


def _name_is_safe(name: str) -> bool:
    from services.conversation_worker.os_package_ensure_workflow import (
        _name_is_safe as fn,
    )

    return fn(name)


class _FakeProc:
    def __init__(self, rc: int = 0, out: bytes = b"", err: bytes = b""):
        self.returncode = rc
        self._out = out
        self._err = err

    async def communicate(self):
        return self._out, self._err


def test_debian_name_charset_gate():
    assert _name_is_safe("ffmpeg")
    assert _name_is_safe("poppler-utils")
    assert not _name_is_safe("--yes")
    assert not _name_is_safe("-oRemote::cmd")
    assert not _name_is_safe("pkg; rm -rf /")
    assert not _name_is_safe("")
    assert not _name_is_safe("./pkg")


@pytest.mark.asyncio
async def test_check_allowlist_passes_curated_names():
    pytest.importorskip("temporalio")
    from services.conversation_worker.os_package_ensure_workflow import (
        OsPackageEnsureInput,
        check_allowlist_activity,
    )

    out = await check_allowlist_activity(
        OsPackageEnsureInput(packages=("ffmpeg", "ffmpeg", "unzip"))
    )
    assert out["allowed"] == ["ffmpeg", "unzip"]
    assert out["denied"] == []


@pytest.mark.asyncio
async def test_check_allowlist_denies_unknown_even_if_tampered():
    """Defense in depth: the workflow never trusts the tool-layer filter."""
    pytest.importorskip("temporalio")
    from services.conversation_worker.os_package_ensure_workflow import (
        OsPackageEnsureInput,
        check_allowlist_activity,
    )

    with pytest.raises(RuntimeError, match="allowlist miss"):
        await check_allowlist_activity(
            OsPackageEnsureInput(packages=("ffmpeg", "evilpkg"))
        )


@pytest.mark.asyncio
async def test_check_allowlist_requires_at_least_one_name():
    pytest.importorskip("temporalio")
    from services.conversation_worker.os_package_ensure_workflow import (
        OsPackageEnsureInput,
        check_allowlist_activity,
    )

    with pytest.raises(RuntimeError, match="at least one package"):
        await check_allowlist_activity(OsPackageEnsureInput(packages=()))


@pytest.mark.asyncio
async def test_install_runs_argv_list_no_shell(monkeypatch):
    pytest.importorskip("temporalio")
    import asyncio

    from services.conversation_worker.os_package_ensure_workflow import (
        install_os_packages_activity,
    )

    calls = []

    async def _fake_exec(*argv, **kwargs):
        calls.append(list(argv))
        return _FakeProc(rc=0, err=b"Setting up ffmpeg ...\n")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    out = await install_os_packages_activity(["ffmpeg", "unzip"])
    assert out["installed"] == ["ffmpeg", "unzip"]
    assert len(calls) == 1
    argv = calls[0]
    # argv list, apt-get install -y --no-install-recommends, names last.
    assert isinstance(argv, list)
    assert argv[:4] == ["apt-get", "install", "-y", "--no-install-recommends"]
    assert argv[4:] == ["ffmpeg", "unzip"]
    # Never a shell, never -c, never a single command string.
    assert "sh" not in argv and "-c" not in argv
    assert all(isinstance(a, str) for a in argv)
    # No mirror/URL configured anywhere in the argv.
    assert not any("http" in a or "://" in a for a in argv)


@pytest.mark.asyncio
async def test_install_refuses_non_allowlisted_before_subprocess(monkeypatch):
    pytest.importorskip("temporalio")
    import asyncio

    from services.conversation_worker.os_package_ensure_workflow import (
        install_os_packages_activity,
    )

    calls = []

    async def _fake_exec(*argv, **kwargs):
        calls.append(list(argv))
        return _FakeProc(rc=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    with pytest.raises(RuntimeError, match="non-allowlisted"):
        await install_os_packages_activity(["evilpkg"])
    assert calls == []  # subprocess never spawned


@pytest.mark.asyncio
async def test_install_failure_surfaces_rc(monkeypatch):
    pytest.importorskip("temporalio")
    import asyncio

    from services.conversation_worker.os_package_ensure_workflow import (
        install_os_packages_activity,
    )

    async def _fake_exec(*argv, **kwargs):
        return _FakeProc(rc=100, err=b"E: Unable to locate package\n")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    with pytest.raises(RuntimeError, match="rc=100"):
        await install_os_packages_activity(["ffmpeg"])


@pytest.mark.asyncio
async def test_verify_uses_which_per_binary(monkeypatch):
    pytest.importorskip("temporalio")
    import asyncio

    from services.conversation_worker.os_package_ensure_workflow import (
        verify_os_binaries_activity,
    )

    calls = []

    async def _fake_exec(*argv, **kwargs):
        calls.append(list(argv))
        # ffmpeg + convert present; pdftotext missing.
        missing = argv[-1] == "pdftotext"
        return _FakeProc(rc=1 if missing else 0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    out = await verify_os_binaries_activity(
        ["ffmpeg", "imagemagick", "poppler-utils"]
    )
    assert out["binaries"] == {
        "ffmpeg": True,
        "imagemagick": True,
        "poppler-utils": False,
    }
    assert out["ok"] is False
    # argv-only `which <bin>` per package.
    assert all(c[0] == "which" and len(c) == 2 for c in calls)
    assert not any("-c" in c for c in calls)


@pytest.mark.asyncio
async def test_verify_ok_when_all_binaries_present(monkeypatch):
    pytest.importorskip("temporalio")
    import asyncio

    from services.conversation_worker.os_package_ensure_workflow import (
        verify_os_binaries_activity,
    )

    async def _fake_exec(*argv, **kwargs):
        return _FakeProc(rc=0)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_exec)
    out = await verify_os_binaries_activity(["ffmpeg", "unzip"])
    assert out["ok"] is True
    assert out["unmapped"] == []


# ---------------------------------------------------------------------------
# Workflow / worker / policy wiring
# ---------------------------------------------------------------------------


def test_workflow_has_progress_query():
    pytest.importorskip("temporalio")
    from services.conversation_worker.os_package_ensure_workflow import (
        OsPackageEnsureWorkflow,
    )

    assert hasattr(OsPackageEnsureWorkflow, "progress")
    assert hasattr(
        OsPackageEnsureWorkflow.progress, "__temporal_query_definition"
    )
    assert OsPackageEnsureWorkflow().progress()["phase"] == "pending"


def test_worker_registers_os_package_workflow_and_activities():
    src = Path("services/conversation_worker/temporal_worker.py").read_text(
        encoding="utf-8"
    )
    assert "OsPackageEnsureWorkflow" in src
    assert "check_allowlist_activity" in src
    assert "install_os_packages_activity" in src
    assert "verify_os_binaries_activity" in src


def test_os_package_tool_in_default_kit():
    from services.tool_executor.default_tools import (
        DEFAULT_AGENT_TOOLS,
        DEFAULT_TOOL_DESCRIPTIONS,
        default_tool_definitions,
    )

    assert "os_packages_ensure" in DEFAULT_AGENT_TOOLS
    # Inserted before the Python pair so packages_ensure/packages_list stay
    # last (existing tool_count_limit expectations unchanged).
    assert DEFAULT_AGENT_TOOLS[-2:] == ["packages_ensure", "packages_list"]
    assert (
        DEFAULT_AGENT_TOOLS.index("os_packages_ensure")
        < DEFAULT_AGENT_TOOLS.index("packages_ensure")
    )
    assert DEFAULT_TOOL_DESCRIPTIONS["os_packages_ensure"].strip()
    names = {d["function"]["name"] for d in default_tool_definitions()}
    assert "os_packages_ensure" in names


def test_capsule_seed_policy_wires_approval():
    src = Path("admin/core/models/core.py").read_text(encoding="utf-8")
    policy_seg = src.split("self.tool_policy = {", 1)[1]
    approval_seg = policy_seg.split('"approval_required": [', 1)[1].split("]", 1)[0]
    assert '"os_packages_ensure"' in approval_seg
    # Not auto-execute: it mutates the container package set.
    auto_seg = src.split("safe_auto = [", 1)[1].split("]", 1)[0]
    assert '"os_packages_ensure"' not in auto_seg


def test_os_packages_ensure_is_egress_gated():
    import admin.core.tool_calling as tool_calling

    assert "os_packages_ensure" in tool_calling._NETWORK_TOOLS


@pytest.mark.asyncio
async def test_job_status_queries_os_package_progress(temporal_fake):
    from services.tool_executor.assistant_tools.research_report import JobStatusTool

    client, _ = temporal_fake

    class _OsOnlyHandle:
        async def describe(self):
            return SimpleNamespace(
                status=SimpleNamespace(name="RUNNING"),
                start_time="2026-10-09T00:00:00+00:00",
                close_time=None,
            )

        async def query(self, fn):
            if fn.__qualname__.startswith("OsPackageEnsureWorkflow"):
                return {"phase": "install", "packages": ["ffmpeg"]}
            raise RuntimeError("query not found for this workflow type")

    client._handle = _OsOnlyHandle()
    result = await JobStatusTool().run({"workflow_id": "os-package-ensure-t-1-x"})
    assert result["status"] == "RUNNING"
    assert result["progress"]["phase"] == "install"


def test_tool_protocol_has_no_shell_fields():
    """Hard rule: structured {profile|packages[]} only — no shell strings."""
    from services.tool_executor.assistant_tools.os_packages_ensure import (
        OsPackagesEnsureTool,
    )

    schema = OsPackagesEnsureTool().input_schema()
    assert set(schema["properties"]) == {"profile", "packages"}
    assert schema.get("required", []) == []
    assert OsPackagesEnsureTool().tier == 3
    assert OsPackagesEnsureTool().durable is True
    assert OsPackagesEnsureTool().needs_egress is True
