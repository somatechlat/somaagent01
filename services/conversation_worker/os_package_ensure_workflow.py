"""OsPackageEnsureWorkflow — allowlisted OS packages inside the agent container.

TOOLS-001 §5.4.1: same rails as Python ``PackageEnsureWorkflow``. Long apt
work runs here under Temporal, never in the chat loop.

Hard rules encoded in this module:
- ``apt-get`` runs as an **argv list** (``asyncio.create_subprocess_exec``),
  never a shell string — no ``sh -c``, no free strings from the model.
- Package names are re-checked against the operator allowlist inside the
  worker (fail closed even if tool-layer input were tampered with).
- Side effect is the **agent container only** — no host OS, no user laptop,
  no docker.sock. Apt sources/mirrors come from the container image; this
  file hardcodes no mirror, URL, or version pin.
- Workflow history carries package **names** and counts only.

Long installs are approval-gated at the tool choke before this workflow is
ever started (Capsule ``approval_required``).
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import activity, workflow

_CHECK_TIMEOUT = timedelta(seconds=60)
_INSTALL_TIMEOUT = timedelta(seconds=600)
_VERIFY_TIMEOUT = timedelta(seconds=120)

# Debian package-name charset — second gate before argv assembly. A name
# starting with "-" could otherwise be read by apt-get as an option.
_DEBIAN_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789+-.")


def _name_is_safe(name: str) -> bool:
    name = str(name or "")
    if not name or len(name) > 200:
        return False
    if name[0] in "-.":
        return False
    return all(c in _DEBIAN_NAME_CHARS for c in name.lower())


@dataclass(frozen=True)
class OsPackageEnsureInput:
    """Small durable input — names only."""

    profile: str = ""
    packages: tuple = ()  # tuple of str — frozen dataclass friendly
    tenant_id: str = ""
    capsule_id: str = ""

    def package_list(self) -> List[str]:
        if self.packages:
            return [str(p) for p in self.packages if str(p).strip()]
        return []


@activity.defn
async def check_allowlist_activity(inp: OsPackageEnsureInput) -> Dict[str, Any]:
    """Fail-closed allowlist gate inside the worker (defense in depth).

    The tool layer already filters, but the workflow never trusts that:
    any non-allowlisted or malformed name raises before apt is invoked.
    """
    from services.tool_executor.os_package_profiles import (
        OS_PACKAGE_ALLOWLIST,
        filter_os_allowlisted,
    )

    requested = inp.package_list()
    if not requested:
        raise RuntimeError("os package ensure requires at least one package name")
    # de-dupe preserving order before filtering
    seen: set = set()
    uniq: List[str] = []
    for n in requested:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    allowed, denied = filter_os_allowlisted(uniq)
    # filter canonicalizes case; a length mismatch or any denied name means a
    # name was not on the allowlist (or a non-canonical variant) — fail closed.
    if denied or len(allowed) != len(uniq):
        raise RuntimeError(
            "os package allowlist miss — refusing apt: "
            + ", ".join(sorted(set(denied)) or [n for n in uniq if n not in OS_PACKAGE_ALLOWLIST])
        )
    unsafe = [n for n in allowed if not _name_is_safe(n)]
    if unsafe:
        raise RuntimeError(
            "os package name fails Debian charset gate: " + ", ".join(unsafe)
        )
    return {"allowed": allowed, "denied": sorted(set(denied))}


@activity.defn
async def install_os_packages_activity(packages: List[str]) -> Dict[str, Any]:
    """``apt-get install -y --no-install-recommends <names>`` — argv, no shell.

    Runs inside the agent container (the worker's own container). Apt uses
    the sources the operator baked into the image; nothing here configures a
    mirror. Permission or network failures surface as an honest rc!=0 error.
    """
    from services.tool_executor.os_package_profiles import OS_PACKAGE_ALLOWLIST

    if not packages:
        return {"installed": [], "skipped": True, "detail": "no packages"}
    for name in packages:
        if name not in OS_PACKAGE_ALLOWLIST:
            raise RuntimeError(f"install refuses non-allowlisted name: {name}")
        if not _name_is_safe(name):
            raise RuntimeError(f"install refuses unsafe name: {name}")

    argv = [
        "apt-get",
        "install",
        "-y",
        "--no-install-recommends",
        *packages,
    ]
    env = dict(os.environ)
    env["DEBIAN_FRONTEND"] = "noninteractive"
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    out, err = await proc.communicate()
    tail = (err or out).decode("utf-8", "replace")[-1200:]
    if proc.returncode != 0:
        raise RuntimeError(f"apt-get install failed rc={proc.returncode}: {tail}")
    return {"installed": list(packages), "skipped": False, "detail": tail[-400:]}


@activity.defn
async def verify_os_binaries_activity(packages: List[str]) -> Dict[str, Any]:
    """``which <bin>`` per curated package — argv, no shell; mockable subprocess."""
    from services.tool_executor.os_package_profiles import os_binary_for

    results: Dict[str, bool] = {}
    unmapped: List[str] = []
    for pkg in packages:
        binary = os_binary_for(pkg)
        if not binary:
            unmapped.append(pkg)
            results[pkg] = False
            continue
        proc = await asyncio.create_subprocess_exec(
            "which",
            binary,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        results[pkg] = proc.returncode == 0
    ok = all(results.values()) if results else False
    return {"binaries": results, "unmapped": unmapped, "ok": ok}


@workflow.defn
class OsPackageEnsureWorkflow:
    """Ensure allowlisted OS packages in the agent container; report progress."""

    def __init__(self) -> None:
        self._progress: Dict[str, Any] = {"phase": "pending", "packages": []}

    @workflow.run
    async def run(self, inp: OsPackageEnsureInput) -> Dict[str, Any]:
        requested = inp.package_list()
        self._progress = {
            "phase": "check",
            "profile": inp.profile,
            "packages": requested,
            "tenant_id": inp.tenant_id,
        }
        checked = await workflow.execute_activity(
            check_allowlist_activity,
            inp,
            start_to_close_timeout=_CHECK_TIMEOUT,
        )
        packages = list(checked.get("allowed") or [])
        self._progress = {
            "phase": "install",
            "profile": inp.profile,
            "packages": packages,
        }
        install = await workflow.execute_activity(
            install_os_packages_activity,
            packages,
            start_to_close_timeout=_INSTALL_TIMEOUT,
        )
        self._progress = {
            "phase": "verify",
            "profile": inp.profile,
            "packages": packages,
        }
        verify = await workflow.execute_activity(
            verify_os_binaries_activity,
            packages,
            start_to_close_timeout=_VERIFY_TIMEOUT,
        )
        result = {
            "ok": bool(verify.get("ok")),
            "profile": inp.profile,
            "packages": packages,
            "installed": install.get("installed") or [],
            "binaries": verify.get("binaries") or {},
            "unmapped": verify.get("unmapped") or [],
            "tenant_id": inp.tenant_id,
        }
        self._progress = {
            "phase": "done",
            "ok": result["ok"],
            "profile": result["profile"],
            "packages": packages,
            "installed": result["installed"],
        }
        return result

    @workflow.query
    def progress(self) -> Dict[str, Any]:
        return dict(self._progress)
