"""packages_ensure + packages_list — A0 install capacity without free shell.

TOOLS-001 §5.4. Temporal PackageEnsureWorkflow installs operator-allowlisted
names into TOOL_WORK_DIR/.soma/venv. No host mutation, no pip strings from
the model, unknown packages fail closed.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    tool_error,
    workroot_guard,
)
from services.tool_executor.package_profiles import (
    PACKAGE_ALLOWLIST,
    PROFILE_IDS,
    filter_allowlisted,
    resolve_profile_packages,
)


def _conversation_queue() -> str:
    from django.conf import settings

    queue = str(getattr(settings, "TEMPORAL_CONVERSATION_QUEUE", "") or "").strip()
    if not queue:
        raise tool_error(
            "TEMPORAL_CONVERSATION_QUEUE is not configured; "
            "packages_ensure refuses to guess a task queue"
        )
    return queue


def _workflow_id(tenant_id: str, profile: str) -> str:
    tenant = re.sub(r"[^a-zA-Z0-9_.-]+", "-", tenant_id).strip("-") or "unknown"
    prof = re.sub(r"[^a-zA-Z0-9_.-]+", "-", profile).strip("-") or "pkg"
    return f"package-ensure-{tenant}-{prof}-{uuid.uuid4().hex[:12]}"


class PackagesEnsureTool(SomaAssistantTool):
    """Start a durable package-ensure job (tier 3 Temporal-only start + approval)."""

    name = "packages_ensure"
    description = (
        "Install operator-allowlisted Python packages into the agent work "
        "virtualenv using a durable Temporal job. Pass profile "
        f"(one of: {', '.join(PROFILE_IDS)}) for curated sets such as "
        "scientific (numpy/scipy/matplotlib/pandas/sympy/seaborn for math "
        "plots), or packages[] from the allowlist only. Returns workflow_id; "
        "poll with job_status. Never runs free-form pip on the host."
    )
    tier = 3
    needs_workroot = True
    needs_egress = True
    durable = True

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "description": (
                        "Curated profile id: "
                        + ", ".join(PROFILE_IDS)
                        + ". Use scientific for math/plot libraries."
                    ),
                },
                "packages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional extra allowlisted distribution names "
                        "(merged with profile). Unknown names are refused."
                    ),
                },
            },
            "required": [],
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
        profile = str(data.get("profile") or "").strip()
        extra = data.get("packages")
        if isinstance(extra, str):
            extra = [extra]
        if extra is not None and not isinstance(extra, list):
            raise tool_error("packages must be a list of distribution names")

        packages: List[str] = []
        if profile:
            try:
                packages.extend(resolve_profile_packages(profile))
            except KeyError:
                raise tool_error(
                    f"unknown profile {profile!r}; allowed: {', '.join(PROFILE_IDS)}"
                ) from None
        if extra:
            allowed, denied = filter_allowlisted([str(p) for p in extra])
            if denied:
                raise tool_error(
                    "packages not on the operator allowlist: "
                    + ", ".join(denied)
                    + f". Allowed examples: {', '.join(sorted(PACKAGE_ALLOWLIST)[:12])}…"
                )
            packages.extend(allowed)

        if not packages:
            raise tool_error(
                "packages_ensure requires profile and/or packages[] "
                f"(profiles: {', '.join(PROFILE_IDS)})"
            )

        # de-dupe
        seen = set()
        uniq: List[str] = []
        for n in packages:
            if n not in seen:
                seen.add(n)
                uniq.append(n)

        tenant_id = str(data.get("tenant_id") or "").strip()
        if not tenant_id:
            raise tool_error(
                "packages_ensure refuses without a capsule tenant "
                "(identity is injected server-side, not a model argument)"
            )
        capsule_id = str(data.get("capsule_id") or "").strip()

        # Fail closed if workroot is missing before starting a workflow.
        workroot_guard(guard)

        queue = _conversation_queue()
        workflow_id = _workflow_id(tenant_id, profile or "custom")

        from services.conversation_worker.package_ensure_workflow import (
            PackageEnsureInput,
            PackageEnsureWorkflow,
        )
        from services.gateway.providers import get_temporal_client

        client = await get_temporal_client()
        await client.start_workflow(
            PackageEnsureWorkflow.run,
            PackageEnsureInput(
                profile=profile,
                packages=tuple(uniq),
                tenant_id=tenant_id,
                capsule_id=capsule_id,
            ),
            id=workflow_id,
            task_queue=queue,
        )
        return {
            "status": "started",
            "workflow_id": workflow_id,
            "task_queue": queue,
            "profile": profile or None,
            "packages": uniq,
            "message": (
                f"Package ensure job {workflow_id} started on queue {queue}. "
                "Poll job_status. Installs land in the agent work venv only."
            ),
        }


class PackagesListTool(SomaAssistantTool):
    """List allowlist + what is importable in the workroot venv (tier 1)."""

    name = "packages_list"
    description = (
        "List operator package profiles/allowlist and, when present, the "
        "agent work virtualenv path. Use after packages_ensure / job_status."
    )
    tier = 1
    needs_workroot = True
    needs_egress = False

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[PathGuard] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        g = workroot_guard(guard)
        venv = g.workroot / ".soma" / "venv"
        exists = venv.is_dir()
        return {
            "profiles": {
                "scientific": list(
                    resolve_profile_packages("scientific")
                ),
                "office": list(resolve_profile_packages("office")),
                "data": list(resolve_profile_packages("data")),
                "vision": list(resolve_profile_packages("vision")),
            },
            "allowlist": sorted(PACKAGE_ALLOWLIST),
            "venv": str(venv) if exists else None,
            "venv_present": exists,
            "note": (
                "Work venv under the agent work directory. "
                "packages_ensure starts a Temporal job to populate it."
            ),
        }


PACKAGE_ASSISTANT_TOOLS: List[SomaAssistantTool] = [
    PackagesEnsureTool(),
    PackagesListTool(),
]
