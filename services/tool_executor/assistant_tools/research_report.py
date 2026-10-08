"""research_report + job_status — durable assistant jobs (SOMA-ARCH-TOOLS-001 §5/§6).

``research_report`` STARTS ``ResearchReportWorkflow`` on Temporal and returns
the workflow id immediately; the outline is produced by activities in the
worker (never long work in the chat turn). ``job_status`` reports one
workflow id's status via Temporal describe + the workflow ``progress`` query.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    resolve_guard,
    tool_error,
    workroot_guard,
)

_MAX_TOPIC_CHARS = 500


def _conversation_queue() -> str:
    """Task queue the conversation worker listens on — read from settings."""
    from django.conf import settings

    queue = str(getattr(settings, "TEMPORAL_CONVERSATION_QUEUE", "") or "").strip()
    if not queue:
        raise tool_error(
            "TEMPORAL_CONVERSATION_QUEUE is not configured; "
            "research_report refuses to guess a task queue"
        )
    return queue


def _workflow_id(tenant_id: str) -> str:
    tenant = re.sub(r"[^a-zA-Z0-9_.-]+", "-", tenant_id).strip("-") or "unknown"
    return f"research-report-{tenant}-{uuid.uuid4().hex[:12]}"


class ResearchReportTool(SomaAssistantTool):
    """Start a durable ResearchReportWorkflow (tier 2, durable)."""

    name = "research_report"
    description = (
        "Start a durable research-report job on Temporal for a topic. "
        "Returns the workflow id immediately; the outline file is written by "
        "the worker inside the agent work directory. Poll job_status with the "
        "workflow id."
    )
    tier = 2
    needs_workroot = True
    needs_egress = False
    durable = True

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Research topic for the report",
                },
                "workdir": {
                    "type": "string",
                    "description": (
                        "Optional subdirectory (relative to the work "
                        "directory) where the outline file is written"
                    ),
                },
            },
            "required": ["topic"],
            "additionalProperties": True,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[PathGuard] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        data = args or {}
        topic = str(data.get("topic") or "").strip()
        if not topic:
            raise tool_error("topic is required")
        if len(topic) > _MAX_TOPIC_CHARS:
            raise tool_error(f"topic is limited to {_MAX_TOPIC_CHARS} characters")

        # Identity is injected server-side by the tool loop (capsule), never
        # taken from the model. Fail closed without it — no anonymous jobs.
        tenant_id = str(data.get("tenant_id") or "").strip()
        capsule_id = str(data.get("capsule_id") or "").strip()
        if not tenant_id:
            raise tool_error(
                "research_report refuses without a capsule tenant "
                "(identity is injected server-side, not a model argument)"
            )

        workdir = str(data.get("workdir") or "").strip()
        if workdir:
            # Fail fast on a jail escape before a workflow id exists.
            resolve_guard(workroot_guard(guard), workdir)

        queue = _conversation_queue()
        workflow_id = _workflow_id(tenant_id)

        from services.conversation_worker.research_workflow import (
            ResearchReportInput,
            ResearchReportWorkflow,
        )
        from services.gateway.providers import get_temporal_client

        client = await get_temporal_client()
        await client.start_workflow(
            ResearchReportWorkflow.run,
            ResearchReportInput(
                topic=topic,
                tenant_id=tenant_id,
                capsule_id=capsule_id,
                workdir=workdir,
            ),
            id=workflow_id,
            task_queue=queue,
        )
        return {
            "status": "started",
            "workflow_id": workflow_id,
            "task_queue": queue,
            "message": f"Durable job {workflow_id} started — Jobs panel.",
        }


class JobStatusTool(SomaAssistantTool):
    """Report the status of one workflow id (tier 1 — read-only)."""

    name = "job_status"
    description = (
        "Report the status of a durable job by workflow id: execution status "
        "from Temporal plus the workflow's progress query when available."
    )
    tier = 1
    needs_workroot = False
    needs_egress = False
    durable = False

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow id returned by a durable job tool",
                },
            },
            "required": ["workflow_id"],
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[PathGuard] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        workflow_id = str((args or {}).get("workflow_id") or "").strip()
        if not workflow_id:
            raise tool_error("workflow_id is required")

        from services.conversation_worker.research_workflow import (
            ResearchReportWorkflow,
        )
        from services.gateway.providers import get_temporal_client

        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        try:
            desc = await handle.describe()
        except Exception as exc:
            raise tool_error(f"cannot describe workflow {workflow_id}: {exc}") from exc

        status = getattr(desc.status, "name", str(desc.status))
        progress: Optional[Dict[str, Any]] = None
        try:
            progress = await handle.query(ResearchReportWorkflow.progress)
        except Exception:
            # Non-ResearchReport workflow, closed before query, or worker
            # unreachable for the query — status above is still reported.
            progress = None

        return {
            "workflow_id": workflow_id,
            "status": status,
            "progress": progress,
            "start_time": str(getattr(desc, "start_time", None) or "") or None,
            "close_time": str(getattr(desc, "close_time", None) or "") or None,
        }
