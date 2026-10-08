"""ResearchReportWorkflow — durable assistant job (SOMA-ARCH-TOOLS-001 §6).

Chain: ``plan_outline`` → ``write_outline_file`` → ``mark_complete``.

History discipline (SOMA-ARCH-TOOLS-001 §6): the workflow history carries
only the small plan manifest, the relative path, byte counts, and a SHA-256.
File bytes are assembled and written inside ``write_outline_file_activity``
via ``PathGuard`` — content never crosses the history boundary.

The workroot is server-side (``TOOL_WORK_DIR``), never a model argument; the
optional ``workdir`` is a relative subdirectory resolved through PathGuard.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import activity, workflow

# Schedule-to-close budgets per activity (plan is CPU-light; IO is bounded).
_PLAN_TIMEOUT = timedelta(seconds=120)
_WRITE_TIMEOUT = timedelta(seconds=300)
_COMPLETE_TIMEOUT = timedelta(seconds=120)


@dataclass(frozen=True)
class ResearchReportInput:
    """Durable job input — small, server-side identity, optional subdir."""

    topic: str
    tenant_id: str
    capsule_id: str
    workdir: str = ""


def _slug(topic: str) -> str:
    """Filesystem-safe slug for the artifact name (never a path)."""
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return (slug[:60].rstrip("-")) or "research"


def _render_outline(manifest: Dict[str, Any]) -> str:
    """Assemble the markdown artifact inside the activity (not in history)."""
    topic = str(manifest.get("topic") or "")
    capsule_id = str(manifest.get("capsule_id") or "")
    sections: List[Dict[str, Any]] = list(manifest.get("sections") or [])
    lines: List[str] = [
        f"# {topic}",
        "",
        "Research report outline.",
        "",
        f"- Capsule: {capsule_id or 'unknown'}",
        f"- Sections: {len(sections)}",
        "",
    ]
    for index, section in enumerate(sections, 1):
        title = str(section.get("title") or f"Section {index}")
        focus = str(section.get("focus") or "")
        lines.append(f"## {index}. {title}")
        lines.append("")
        lines.append(f"Focus: {focus}")
        lines.append("")
        lines.append("- (evidence to collect)")
        lines.append("")
    return "\n".join(lines)


@activity.defn
async def plan_outline_activity(inp: ResearchReportInput) -> Dict[str, Any]:
    """Build the outline manifest for a topic — the real planning step."""
    topic = (inp.topic or "").strip()
    if not topic:
        raise ValueError("topic is required")
    if len(topic) > 500:
        raise ValueError("topic is limited to 500 characters")
    workdir = (inp.workdir or "").strip()

    slug = _slug(topic)
    sections = [
        {
            "id": "overview",
            "title": "Overview",
            "focus": f"Scope and purpose of {topic}",
        },
        {
            "id": "background",
            "title": "Background",
            "focus": f"Prior context and definitions for {topic}",
        },
        {
            "id": "key_questions",
            "title": "Key questions",
            "focus": f"Open questions this report on {topic} must answer",
        },
        {
            "id": "findings",
            "title": "Findings",
            "focus": f"Evidence to gather about {topic}",
        },
        {
            "id": "analysis",
            "title": "Analysis",
            "focus": f"Interpretation of the findings on {topic}",
        },
        {
            "id": "conclusions",
            "title": "Conclusions",
            "focus": f"Answer, limits, and next steps for {topic}",
        },
        {
            "id": "sources",
            "title": "Sources",
            "focus": "Cited material for every claim above",
        },
    ]
    relpath = f"{slug}-outline.md"
    if workdir:
        relpath = f"{workdir.rstrip('/')}/{relpath}"

    return {
        "topic": topic,
        "slug": slug,
        "relpath": relpath,
        "sections": sections,
        "tenant_id": str(inp.tenant_id or ""),
        "capsule_id": str(inp.capsule_id or ""),
    }


@activity.defn
async def write_outline_file_activity(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Write the outline file under the workroot via PathGuard.

    Content is built here from the manifest, so only path/bytes/hash leave
    this activity as its result.
    """
    from services.common.path_guard import PathGuard, PathGuardError

    workroot = (os.environ.get("TOOL_WORK_DIR") or "").strip()
    if not workroot:
        raise RuntimeError(
            "TOOL_WORK_DIR is not configured; the report file has no workroot"
        )
    relpath = str(manifest.get("relpath") or "").strip()
    if not relpath:
        raise RuntimeError("plan manifest carries no relpath")

    guard = PathGuard(workroot)
    try:
        target = guard.resolve(relpath)
    except PathGuardError as exc:
        raise RuntimeError(str(exc)) from exc

    content = _render_outline(manifest)

    def _write() -> Dict[str, Any]:
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        target.write_bytes(data)
        return {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    written = await asyncio.to_thread(_write)
    return {"path": guard.relative_to_workroot(target), **written}


@activity.defn
async def mark_complete_activity(
    manifest: Dict[str, Any],
    written: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify the artifact still matches what the write step reported.

    A job is never marked completed without re-reading the bytes and
    re-hashing them — mismatch fails the activity instead of completing.
    """
    from services.common.path_guard import PathGuard, PathGuardError

    workroot = (os.environ.get("TOOL_WORK_DIR") or "").strip()
    if not workroot:
        raise RuntimeError("TOOL_WORK_DIR is not configured")

    relpath = str(manifest.get("relpath") or "").strip()
    guard = PathGuard(workroot)
    try:
        target = guard.resolve(relpath)
    except PathGuardError as exc:
        raise RuntimeError(str(exc)) from exc

    def _verify() -> Dict[str, Any]:
        if not target.is_file():
            raise RuntimeError(f"artifact missing: {relpath}")
        data = target.read_bytes()
        return {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    verified = await asyncio.to_thread(_verify)
    if verified["sha256"] != written.get("sha256"):
        raise RuntimeError("artifact changed between write and completion")
    if verified["bytes"] != written.get("bytes"):
        raise RuntimeError("artifact size changed between write and completion")

    return {
        "status": "completed",
        "topic": str(manifest.get("topic") or ""),
        "path": str(written.get("path") or ""),
        "bytes": verified["bytes"],
        "sha256": verified["sha256"],
        "tenant_id": str(manifest.get("tenant_id") or ""),
        "capsule_id": str(manifest.get("capsule_id") or ""),
    }


@workflow.defn
class ResearchReportWorkflow:
    """Durable research-report job: plan → write → verify (SOMA §6)."""

    def __init__(self) -> None:
        self._progress: Dict[str, Any] = {"step": "created"}

    @workflow.run
    async def run(self, inp: ResearchReportInput) -> Dict[str, Any]:
        self._progress = {
            "step": "plan_outline",
            "topic": inp.topic,
            "tenant_id": inp.tenant_id,
        }
        manifest = await workflow.execute_activity(
            plan_outline_activity,
            inp,
            schedule_to_close_timeout=_PLAN_TIMEOUT,
        )

        self._progress = {
            "step": "write_outline_file",
            "topic": manifest.get("topic", ""),
            "sections": len(manifest.get("sections") or []),
        }
        written = await workflow.execute_activity(
            write_outline_file_activity,
            manifest,
            schedule_to_close_timeout=_WRITE_TIMEOUT,
        )

        self._progress = {
            "step": "mark_complete",
            "path": written.get("path", ""),
        }
        result = await workflow.execute_activity(
            mark_complete_activity,
            manifest,
            written,
            schedule_to_close_timeout=_COMPLETE_TIMEOUT,
        )

        self._progress = {
            "step": "completed",
            "path": result.get("path", ""),
            "bytes": result.get("bytes", 0),
        }
        return result

    @workflow.query
    def progress(self) -> Dict[str, Any]:
        """Query for job_status: current step + small manifest facts."""
        return dict(self._progress)
