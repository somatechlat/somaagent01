"""PackageEnsureWorkflow — install allowlisted packages into a workroot venv.

TOOLS-001 §5.4: no free pip in the chat loop. Long installs run here under
Temporal. History carries package names and counts only — never file bytes.
Side effect is ``TOOL_WORK_DIR/.soma/venv`` (PathGuard-relative), never the
host OS or chat process environment.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List

from temporalio import activity, workflow

_VENV_TIMEOUT = timedelta(seconds=180)
_INSTALL_TIMEOUT = timedelta(seconds=600)
_VERIFY_TIMEOUT = timedelta(seconds=120)

# Relative venv location under the agent workroot (never absolute from model).
VENV_REL = ".soma/venv"


@dataclass(frozen=True)
class PackageEnsureInput:
    """Small durable input — names only."""

    profile: str
    packages: tuple = ()  # tuple of str — frozen dataclass friendly
    tenant_id: str = ""
    capsule_id: str = ""

    def package_list(self) -> List[str]:
        if self.packages:
            return [str(p) for p in self.packages if str(p).strip()]
        return []


def _workroot() -> Path:
    raw = os.environ.get("TOOL_WORK_DIR") or ""
    if not raw.strip():
        raise RuntimeError(
            "TOOL_WORK_DIR is not configured; package ensure refuses without a workroot"
        )
    return Path(raw).expanduser().resolve()


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


@activity.defn
async def create_venv_activity(inp: PackageEnsureInput) -> Dict[str, Any]:
    """Create (or reuse) the workroot-scoped virtualenv."""
    root = _workroot()
    venv = (root / VENV_REL).resolve()
    # Stay under workroot even for our own path math.
    if root not in venv.parents and venv != root:
        raise RuntimeError(f"venv path escapes workroot: {venv}")
    venv.parent.mkdir(parents=True, exist_ok=True)

    py = _venv_python(venv)
    if not py.is_file():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "venv",
            str(venv),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"venv create failed rc={proc.returncode}: "
                f"{(err or out).decode('utf-8', 'replace')[-800:]}"
            )
    if not py.is_file():
        raise RuntimeError(f"venv python missing after create: {py}")
    return {"venv": str(venv), "python": str(py), "created": True}


@activity.defn
async def install_packages_activity(
    venv_python: str, packages: List[str]
) -> Dict[str, Any]:
    """pip install allowlisted names into the venv (subprocess, no shell)."""
    if not packages:
        return {"installed": [], "skipped": True, "detail": "no packages"}
    # --no-input: never prompt. --disable-pip-version-check: no network noise.
    # Names come only from the operator allowlist (tool layer).
    cmd = [
        venv_python,
        "-m",
        "pip",
        "install",
        "--no-input",
        "--disable-pip-version-check",
        *packages,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    tail = (err or out).decode("utf-8", "replace")[-1200:]
    if proc.returncode != 0:
        raise RuntimeError(f"pip install failed rc={proc.returncode}: {tail}")
    return {"installed": list(packages), "skipped": False, "detail": tail[-400:]}


@activity.defn
async def verify_imports_activity(venv_python: str, packages: List[str]) -> Dict[str, Any]:
    """Import-check each distribution's top-level module where possible."""
    # Distribution name → import name map for the curated set only.
    import_map = {
        "python-docx": "docx",
        "python-pptx": "pptx",
        "pillow": "PIL",
        "pyyaml": "yaml",
    }
    results: Dict[str, bool] = {}
    for dist in packages:
        mod = import_map.get(dist.lower(), dist.lower().replace("-", "_"))
        # Skip pip itself
        code = f"import {mod}"
        proc = await asyncio.create_subprocess_exec(
            venv_python,
            "-c",
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        results[dist] = proc.returncode == 0
    ok = all(results.values()) if results else True
    return {"imports": results, "ok": ok}


@workflow.defn
class PackageEnsureWorkflow:
    """Ensure allowlisted packages in the workroot venv; report progress."""

    def __init__(self) -> None:
        self._progress: Dict[str, Any] = {"phase": "pending", "packages": []}

    @workflow.run
    async def run(self, inp: PackageEnsureInput) -> Dict[str, Any]:
        packages = inp.package_list()
        self._progress = {
            "phase": "venv",
            "profile": inp.profile,
            "packages": packages,
            "tenant_id": inp.tenant_id,
        }
        venv_info = await workflow.execute_activity(
            create_venv_activity,
            inp,
            start_to_close_timeout=_VENV_TIMEOUT,
        )
        venv_python = str(venv_info.get("python") or "")
        self._progress = {
            "phase": "install",
            "profile": inp.profile,
            "packages": packages,
            "venv": venv_info.get("venv"),
        }
        install = await workflow.execute_activity(
            install_packages_activity,
            venv_python,
            packages,
            start_to_close_timeout=_INSTALL_TIMEOUT,
        )
        self._progress = {
            "phase": "verify",
            "profile": inp.profile,
            "packages": packages,
            "venv": venv_info.get("venv"),
        }
        verify = await workflow.execute_activity(
            verify_imports_activity,
            venv_python,
            packages,
            start_to_close_timeout=_VERIFY_TIMEOUT,
        )
        result = {
            "ok": bool(verify.get("ok")),
            "profile": inp.profile,
            "venv": venv_info.get("venv"),
            "python": venv_python,
            "installed": install.get("installed") or [],
            "imports": verify.get("imports") or {},
            "tenant_id": inp.tenant_id,
        }
        self._progress = {"phase": "done", **{k: result[k] for k in ("ok", "profile", "venv", "installed")}}
        return result

    @workflow.query
    def progress(self) -> Dict[str, Any]:
        return dict(self._progress)
