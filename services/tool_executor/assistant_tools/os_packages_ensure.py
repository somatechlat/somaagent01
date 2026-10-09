"""os_packages_ensure — allowlisted container OS packages without free shell.

TOOLS-001 §5.4.1. Temporal ``OsPackageEnsureWorkflow`` runs ``apt-get`` as an
argv list inside the **agent container only** (never the host OS, never the
user laptop, never docker.sock, never ``sh -c``). Structured names from the
operator allowlist only; unknown names fail closed; approval is mandatory
(tier 3, Capsule ``approval_required``).
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    tool_error,
)
from services.tool_executor.os_package_profiles import (
    OS_PACKAGE_ALLOWLIST,
    OS_PROFILE_IDS,
    all_os_profile_ids,
    filter_os_allowlisted,
    resolve_os_profile,
)


def _conversation_queue() -> str:
    from django.conf import settings

    queue = str(getattr(settings, "TEMPORAL_CONVERSATION_QUEUE", "") or "").strip()
    if not queue:
        raise tool_error(
            "TEMPORAL_CONVERSATION_QUEUE is not configured; "
            "os_packages_ensure refuses to guess a task queue"
        )
    return queue


def _workflow_id(tenant_id: str, profile: str) -> str:
    tenant = re.sub(r"[^a-zA-Z0-9_.-]+", "-", tenant_id).strip("-") or "unknown"
    prof = re.sub(r"[^a-zA-Z0-9_.-]+", "-", profile).strip("-") or "os"
    return f"os-package-ensure-{tenant}-{prof}-{uuid.uuid4().hex[:12]}"


class OsPackagesEnsureTool(SomaAssistantTool):
    """Start a durable container OS package job (tier 3 Temporal-only start)."""

    name = "os_packages_ensure"
    description = (
        "Install operator-allowlisted OS packages (apt) inside the agent "
        "container using a durable Temporal job. Pass profile "
        f"(one of: {', '.join(all_os_profile_ids())}) for curated sets — "
        "media (ffmpeg, imagemagick), docs (poppler-utils, unzip) — or "
        "packages[] from the small OS allowlist only. Returns workflow_id; "
        "poll with job_status. Container-only: never the host OS, no "
        "docker.sock, no shell strings. Unknown packages fail closed."
    )
    tier = 3
    # Side effect is the container's package set, not the workroot — the
    # workroot guard has nothing to resolve here.
    needs_workroot = False
    needs_egress = True
    durable = True

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "description": (
                        "Curated OS profile id: "
                        + ", ".join(OS_PROFILE_IDS)
                        + ". Use media for ffmpeg/imagemagick, docs for "
                        "poppler-utils/unzip."
                    ),
                },
                "packages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional extra allowlisted Debian package names "
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
                packages.extend(resolve_os_profile(profile))
            except KeyError:
                raise tool_error(
                    f"unknown OS profile {profile!r}; "
                    f"allowed: {', '.join(OS_PROFILE_IDS)}"
                ) from None
        if extra:
            allowed, denied = filter_os_allowlisted([str(p) for p in extra])
            if denied:
                raise tool_error(
                    "packages not on the operator OS allowlist: "
                    + ", ".join(denied)
                    + f". Allowed: {', '.join(sorted(OS_PACKAGE_ALLOWLIST))}"
                )
            packages.extend(allowed)

        if not packages:
            raise tool_error(
                "os_packages_ensure requires profile and/or packages[] "
                f"(profiles: {', '.join(OS_PROFILE_IDS)})"
            )

        # de-dupe preserving order
        seen = set()
        uniq: List[str] = []
        for n in packages:
            if n not in seen:
                seen.add(n)
                uniq.append(n)

        # Identity is injected server-side by the tool loop, never from the
        # model. Fail closed without it — no anonymous installs.
        tenant_id = str(data.get("tenant_id") or "").strip()
        if not tenant_id:
            raise tool_error(
                "os_packages_ensure refuses without a capsule tenant "
                "(identity is injected server-side, not a model argument)"
            )
        capsule_id = str(data.get("capsule_id") or "").strip()

        queue = _conversation_queue()
        workflow_id = _workflow_id(tenant_id, profile or "custom")

        from services.conversation_worker.os_package_ensure_workflow import (
            OsPackageEnsureInput,
            OsPackageEnsureWorkflow,
        )
        from services.gateway.providers import get_temporal_client

        client = await get_temporal_client()
        await client.start_workflow(
            OsPackageEnsureWorkflow.run,
            OsPackageEnsureInput(
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
                f"OS package ensure job {workflow_id} started on queue {queue}. "
                "Poll job_status. apt runs in the agent container only."
            ),
        }


OS_PACKAGE_ASSISTANT_TOOLS: List[SomaAssistantTool] = [
    OsPackagesEnsureTool(),
]
