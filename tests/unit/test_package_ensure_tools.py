"""packages_ensure + packages_list — TOOLS-001 §5.4 allowlist fail-closed.

Covers profile resolution, allowlist filtering, the fail-closed refusals
(unknown profile/package, no tenant, no workroot, no queue), the Temporal
start hook with a fake client, and worker/default-kit/policy wiring — no
Temporal server, no network.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from services.tool_executor.package_profiles import (
    PACKAGE_ALLOWLIST,
    PACKAGE_PROFILES,
    PROFILE_IDS,
    filter_allowlisted,
    resolve_profile_packages,
)
from services.tool_executor.tools import ToolExecutionError


# ---------------------------------------------------------------------------
# Profile resolve
# ---------------------------------------------------------------------------


def test_resolve_profile_returns_curated_names():
    for pid in PROFILE_IDS:
        pkgs = resolve_profile_packages(pid)
        assert pkgs, pid
        assert pkgs == list(PACKAGE_PROFILES[pid])


def test_resolve_profile_tolerates_case_and_spacing():
    got = resolve_profile_packages("  SCIENTIFIC ")
    assert got == list(PACKAGE_PROFILES["scientific"])


def test_unknown_profile_fails_closed():
    with pytest.raises(KeyError):
        resolve_profile_packages("hax")
    with pytest.raises(KeyError):
        resolve_profile_packages("")


# ---------------------------------------------------------------------------
# Allowlist filter
# ---------------------------------------------------------------------------


def test_allowlist_is_union_of_profile_members():
    union = {n for names in PACKAGE_PROFILES.values() for n in names}
    assert PACKAGE_ALLOWLIST == frozenset(union)


def test_filter_splits_denied_and_canonicalizes():
    allowed, denied = filter_allowlisted(
        ["NUMPY", "requests", "", "pandas", "numpy"]
    )
    # Canonical casing from the allowlist, order preserved, de-duped.
    assert allowed == ["numpy", "pandas"]
    assert denied == ["requests"]


def test_filter_empty_input_passes_through():
    assert filter_allowlisted([]) == ([], [])
    assert filter_allowlisted(None) == ([], [])


# ---------------------------------------------------------------------------
# Fixtures: workroot + fake Temporal client
# ---------------------------------------------------------------------------


@pytest.fixture
def workroot(tmp_path, monkeypatch):
    """A real TOOL_WORK_DIR workroot — server-side, never a model arg."""
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    return tmp_path


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
# packages_ensure tool — start hook + fail-closed paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_packages_ensure_starts_workflow(temporal_fake, workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    result = await PackagesEnsureTool().run(
        {
            "profile": "scientific",
            "packages": ["pillow"],
            # server-side identity as the tool loop injects it:
            "tenant_id": "t-1",
            "capsule_id": "cap-1",
        }
    )
    assert result["status"] == "started"
    assert result["workflow_id"].startswith("package-ensure-t-1-scientific-")
    assert client.started is not None
    assert client.started["id"] == result["workflow_id"]
    assert client.started["task_queue"] == "conversation"
    arg = client.started["arg"]
    assert arg.tenant_id == "t-1"
    assert arg.capsule_id == "cap-1"
    packages = list(arg.packages)
    assert "numpy" in packages and "pillow" in packages
    # Only allowlisted names ever reach the workflow input.
    assert set(packages) <= set(PACKAGE_ALLOWLIST)
    assert len(packages) == len(set(packages))


@pytest.mark.asyncio
async def test_unknown_profile_refused(temporal_fake, workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="unknown profile"):
        await PackagesEnsureTool().run({"profile": "hax", "tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_unknown_package_refused(temporal_fake, workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="operator allowlist"):
        await PackagesEnsureTool().run(
            {"packages": ["evil-pkg"], "tenant_id": "t-1"}
        )
    assert client.started is None


@pytest.mark.asyncio
async def test_no_profile_or_packages_refused(temporal_fake, workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="requires profile"):
        await PackagesEnsureTool().run({"tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_requires_tenant(temporal_fake, workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="capsule tenant"):
        await PackagesEnsureTool().run({"profile": "scientific"})
    assert client.started is None


@pytest.mark.asyncio
async def test_missing_workroot_fails_closed(temporal_fake, monkeypatch):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    monkeypatch.delenv("TOOL_WORK_DIR", raising=False)
    client, _ = temporal_fake
    with pytest.raises(ToolExecutionError, match="TOOL_WORK_DIR"):
        await PackagesEnsureTool().run({"profile": "scientific", "tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_missing_task_queue_refuses_to_guess(temporal_fake, workroot, monkeypatch):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    client, _ = temporal_fake
    monkeypatch.setattr(
        "django.conf.settings.TEMPORAL_CONVERSATION_QUEUE", "", raising=False
    )
    with pytest.raises(ToolExecutionError, match="guess a task queue"):
        await PackagesEnsureTool().run({"profile": "scientific", "tenant_id": "t-1"})
    assert client.started is None


@pytest.mark.asyncio
async def test_packages_list_reports_profiles_and_venv(workroot):
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesListTool,
    )

    listing = await PackagesListTool().run({})
    assert set(listing["profiles"]) == set(PROFILE_IDS)
    assert listing["allowlist"] == sorted(PACKAGE_ALLOWLIST)
    assert listing["venv_present"] is False
    assert listing["venv"] is None

    (workroot / ".soma" / "venv").mkdir(parents=True)
    listing = await PackagesListTool().run({})
    assert listing["venv_present"] is True
    assert listing["venv"].endswith(".soma/venv")


def test_tool_protocol_has_no_free_form_pip_fields():
    """Hard rule 1: structured {profile|packages[]} only — no pip strings."""
    from services.tool_executor.assistant_tools.packages_ensure import (
        PackagesEnsureTool,
    )

    schema = PackagesEnsureTool().input_schema()
    assert set(schema["properties"]) == {"profile", "packages"}
    assert schema.get("required", []) == []


# ---------------------------------------------------------------------------
# Workflow / worker / policy wiring
# ---------------------------------------------------------------------------


def test_workflow_has_progress_query():
    pytest.importorskip("temporalio")
    from services.conversation_worker.package_ensure_workflow import (
        PackageEnsureWorkflow,
    )

    assert hasattr(PackageEnsureWorkflow, "progress")
    assert hasattr(
        PackageEnsureWorkflow.progress, "__temporal_query_definition"
    )
    assert PackageEnsureWorkflow().progress()["phase"] == "pending"


@pytest.mark.asyncio
async def test_create_venv_requires_workroot(monkeypatch):
    pytest.importorskip("temporalio")
    from services.conversation_worker.package_ensure_workflow import (
        PackageEnsureInput,
        create_venv_activity,
    )

    monkeypatch.delenv("TOOL_WORK_DIR", raising=False)
    with pytest.raises(RuntimeError, match="TOOL_WORK_DIR"):
        await create_venv_activity(PackageEnsureInput(profile="scientific"))


def test_worker_registers_package_ensure_workflow_and_activities():
    src = Path(
        "services/conversation_worker/temporal_worker.py"
    ).read_text(encoding="utf-8")
    assert "PackageEnsureWorkflow" in src
    assert "create_venv_activity" in src
    assert "install_packages_activity" in src
    assert "verify_imports_activity" in src


def test_package_tools_in_default_kit():
    from services.tool_executor.default_tools import (
        DEFAULT_AGENT_TOOLS,
        DEFAULT_TOOL_DESCRIPTIONS,
        default_tool_definitions,
    )

    assert "packages_ensure" in DEFAULT_AGENT_TOOLS
    assert "packages_list" in DEFAULT_AGENT_TOOLS
    # Appended last so an existing tool_count_limit cuts them first.
    assert DEFAULT_AGENT_TOOLS[-2:] == ["packages_ensure", "packages_list"]
    assert DEFAULT_TOOL_DESCRIPTIONS["packages_ensure"].strip()
    assert DEFAULT_TOOL_DESCRIPTIONS["packages_list"].strip()
    names = {d["function"]["name"] for d in default_tool_definitions()}
    assert {"packages_ensure", "packages_list"} <= names


def test_capsule_seed_policy_wires_approval_and_auto():
    """Capsule.save must seed approval for ensure and auto for list."""
    src = Path("admin/core/models/core.py").read_text(encoding="utf-8")
    # Anchor past the field's help_text, which also shows example lists.
    policy_seg = src.split("self.tool_policy = {", 1)[1]
    approval_seg = policy_seg.split('"approval_required": [', 1)[1].split("]", 1)[0]
    auto_seg = src.split("safe_auto = [", 1)[1].split("]", 1)[0]
    assert '"packages_ensure"' in approval_seg
    assert '"packages_list"' in auto_seg
    assert '"packages_list"' not in approval_seg


def test_packages_ensure_is_egress_gated():
    import admin.core.tool_calling as tool_calling

    assert "packages_ensure" in tool_calling._NETWORK_TOOLS


@pytest.mark.asyncio
async def test_job_status_queries_package_ensure_progress(temporal_fake):
    """job_status falls back to PackageEnsureWorkflow.progress (§5.4)."""
    from services.tool_executor.assistant_tools.research_report import JobStatusTool

    client, _ = temporal_fake

    class _PackageOnlyHandle:
        async def describe(self):
            return SimpleNamespace(
                status=SimpleNamespace(name="RUNNING"),
                start_time="2026-10-09T00:00:00+00:00",
                close_time=None,
            )

        async def query(self, fn):
            # The research workflow has no such query on this execution —
            # exactly what Temporal raises for a wrong workflow type.
            if fn.__qualname__.startswith("PackageEnsureWorkflow"):
                return {"phase": "install", "packages": ["numpy"]}
            raise RuntimeError("query not found for this workflow type")

    client._handle = _PackageOnlyHandle()
    result = await JobStatusTool().run({"workflow_id": "package-ensure-t-1-x"})
    assert result["status"] == "RUNNING"
    assert result["progress"]["phase"] == "install"
