"""ResearchReportWorkflow activities + research_report/job_status tools (W3.3).

Covers the real chain without a Temporal server: plan → PathGuard write →
verify, plus the tool hooks that start/query the workflow.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.conversation_worker.research_workflow import (
    ResearchReportInput,
    ResearchReportWorkflow,
    mark_complete_activity,
    plan_outline_activity,
    write_outline_file_activity,
)

TOPIC = "Edge caching strategies"
INP = ResearchReportInput(
    topic=TOPIC, tenant_id="t-1", capsule_id="cap-1", workdir="reports/edge"
)


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_outline_returns_small_manifest():
    manifest = await plan_outline_activity(INP)
    assert manifest["topic"] == TOPIC
    assert manifest["slug"]
    assert manifest["relpath"].startswith("reports/edge/")
    assert manifest["relpath"].endswith("-outline.md")
    assert len(manifest["sections"]) >= 5
    # History discipline: the manifest is a plan, not the artifact.
    assert "content" not in manifest and "body" not in manifest


@pytest.mark.asyncio
async def test_plan_outline_requires_topic():
    with pytest.raises(ValueError, match="topic"):
        await plan_outline_activity(
            ResearchReportInput(topic="  ", tenant_id="t", capsule_id="c")
        )


@pytest.mark.asyncio
async def test_write_outline_file_via_pathguard(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    manifest = await plan_outline_activity(INP)
    written = await write_outline_file_activity(manifest)

    target = tmp_path / "reports" / "edge" / Path(manifest["relpath"]).name
    assert target.is_file()
    data = target.read_bytes()
    assert written["bytes"] == len(data)
    assert written["sha256"] == hashlib.sha256(data).hexdigest()
    assert written["path"] == "reports/edge/" + target.name
    # The artifact is real markdown for this topic, not an empty placeholder.
    assert TOPIC in data.decode("utf-8")
    assert "## 1. Overview" in data.decode("utf-8")


@pytest.mark.asyncio
async def test_write_refuses_path_escape(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    manifest = await plan_outline_activity(INP)
    evil = {**manifest, "relpath": "../outside.md"}
    with pytest.raises(RuntimeError, match="escapes workroot"):
        await write_outline_file_activity(evil)
    assert not (tmp_path.parent / "outside.md").exists()


@pytest.mark.asyncio
async def test_write_requires_workroot(monkeypatch):
    monkeypatch.delenv("TOOL_WORK_DIR", raising=False)
    manifest = await plan_outline_activity(INP)
    with pytest.raises(RuntimeError, match="TOOL_WORK_DIR"):
        await write_outline_file_activity(manifest)


@pytest.mark.asyncio
async def test_mark_complete_verifies_hash(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    manifest = await plan_outline_activity(INP)
    written = await write_outline_file_activity(manifest)
    result = await mark_complete_activity(manifest, written)
    assert result["status"] == "completed"
    assert result["path"] == written["path"]
    assert result["sha256"] == written["sha256"]
    assert result["tenant_id"] == "t-1"


@pytest.mark.asyncio
async def test_mark_complete_rejects_tampered_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    manifest = await plan_outline_activity(INP)
    written = await write_outline_file_activity(manifest)
    target = tmp_path / written["path"]
    target.write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="changed between write and completion"):
        await mark_complete_activity(manifest, written)


def test_workflow_has_progress_query_and_all_steps():
    assert hasattr(ResearchReportWorkflow, "progress")
    assert hasattr(
        ResearchReportWorkflow.progress, "__temporal_query_definition"
    )
    assert ResearchReportWorkflow().progress()["step"] == "created"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class _FakeHandle:
    def __init__(self, status="RUNNING", progress=None, describe_error=None):
        self._desc = SimpleNamespace(
            status=SimpleNamespace(name=status),
            start_time="2026-10-08T00:00:00+00:00",
            close_time=None,
        )
        self._progress = progress
        self._describe_error = describe_error
        self.queried = False

    async def describe(self):
        if self._describe_error is not None:
            raise self._describe_error
        return self._desc

    async def query(self, _fn):
        self.queried = True
        return self._progress


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


@pytest.mark.asyncio
async def test_research_report_starts_workflow(temporal_fake, tmp_path, monkeypatch):
    from services.tool_executor.assistant_tools.research_report import (
        ResearchReportTool,
    )

    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    client, _ = temporal_fake
    tool = ResearchReportTool()
    result = await tool.run(
        {
            "topic": TOPIC,
            "workdir": "reports/edge",
            # server-side identity as the tool loop injects it:
            "tenant_id": "t-1",
            "capsule_id": "cap-1",
        }
    )
    assert result["status"] == "started"
    assert result["workflow_id"].startswith("research-report-t-1-")
    assert client.started is not None
    assert client.started["id"] == result["workflow_id"]
    assert client.started["task_queue"] == "conversation"
    arg = client.started["arg"]
    assert arg.topic == TOPIC
    assert arg.tenant_id == "t-1"
    assert arg.workdir == "reports/edge"


@pytest.mark.asyncio
async def test_research_report_fails_closed_without_tenant(
    temporal_fake, tmp_path, monkeypatch
):
    from services.tool_executor.assistant_tools.research_report import (
        ResearchReportTool,
    )

    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    client, _ = temporal_fake
    with pytest.raises(Exception, match="capsule tenant"):
        await ResearchReportTool().run({"topic": TOPIC})
    assert client.started is None


@pytest.mark.asyncio
async def test_research_report_rejects_workdir_escape(
    temporal_fake, tmp_path, monkeypatch
):
    from services.tool_executor.assistant_tools.research_report import (
        ResearchReportTool,
    )

    monkeypatch.setenv("TOOL_WORK_DIR", str(tmp_path))
    client, _ = temporal_fake
    with pytest.raises(Exception, match="escapes workroot"):
        await ResearchReportTool().run(
            {"topic": TOPIC, "tenant_id": "t-1", "workdir": "../outside"}
        )
    assert client.started is None


@pytest.mark.asyncio
async def test_job_status_reports_status_and_progress(temporal_fake):
    from services.tool_executor.assistant_tools.research_report import JobStatusTool

    client, handle = temporal_fake
    handle._progress = {"step": "write_outline_file", "topic": TOPIC}
    result = await JobStatusTool().run({"workflow_id": "research-report-t-1-abc"})
    assert result["status"] == "RUNNING"
    assert result["progress"]["step"] == "write_outline_file"
    assert result["workflow_id"] == "research-report-t-1-abc"
    assert handle.queried is True


@pytest.mark.asyncio
async def test_job_status_unknown_workflow_fails_closed(temporal_fake):
    from services.tool_executor.assistant_tools.research_report import JobStatusTool

    _, handle = temporal_fake
    handle._describe_error = RuntimeError("workflow not found")
    with pytest.raises(Exception, match="cannot describe workflow"):
        await JobStatusTool().run({"workflow_id": "nope"})
    with pytest.raises(Exception, match="workflow_id is required"):
        await JobStatusTool().run({})


# ---------------------------------------------------------------------------
# Registration / worker wiring
# ---------------------------------------------------------------------------


def test_durable_tools_in_default_kit():
    from services.tool_executor.default_tools import (
        DEFAULT_AGENT_TOOLS,
        default_tool_definitions,
    )

    assert "research_report" in DEFAULT_AGENT_TOOLS
    assert "job_status" in DEFAULT_AGENT_TOOLS
    names = {d["function"]["name"] for d in default_tool_definitions()}
    assert {"research_report", "job_status"} <= names


def test_worker_registers_research_workflow():
    """The worker must actually serve the workflow and its activities."""
    src = Path(
        "services/conversation_worker/temporal_worker.py"
    ).read_text(encoding="utf-8")
    assert "ResearchReportWorkflow" in src
    assert "plan_outline_activity" in src
    assert "write_outline_file_activity" in src
    assert "mark_complete_activity" in src


def test_workflow_history_carries_no_content_writes():
    """File bytes must be written inside an activity, never by the workflow."""
    src = Path(
        "services/conversation_worker/research_workflow.py"
    ).read_text(encoding="utf-8")
    workflow_part = src.split("@workflow.defn", 1)[1]
    assert "write_text" not in workflow_part
    assert "write_bytes" not in workflow_part
    assert "open(" not in workflow_part
