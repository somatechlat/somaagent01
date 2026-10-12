"""Bootstrap run context — one object through all phases.

Carries the operator inputs (tenant, email, password source), the per-phase
results, and the fail-closed guards. Phases never read argv or stdin directly;
they read the context.

Operator identity is never invented here. The write path takes it from
``--tenant`` / ``--sysadmin-email``. The read-only ``--check`` path resolves
what already exists (the settings chain's ``SA01_DEFAULT_TENANT_ID``, or the
unique sysadmin identity) and refuses to guess when that is ambiguous.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from admin.core.bootstrap.exit_codes import ExitCode

__all__ = [
    "PhaseResult",
    "BootstrapContext",
    "ConfigError",
    "DependencyError",
    "find_identity",
    "find_tenant",
    "discover_sysadmin_identity",
    "settings_chain_tenant_ref",
]


@dataclass
class PhaseResult:
    """Outcome of one phase."""

    name: str
    status: str  # "ok" | "skipped" | "partial" | "failed"
    detail: str = ""
    writes: int = 0
    skips: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.name,
            "status": self.status,
            "detail": self.detail,
            "writes": self.writes,
            "skips": self.skips,
        }


def find_identity(email: str) -> Any:
    """LocalIdentity row for ``email``, or None. Read-only."""
    if not email:
        return None
    from admin.platform.models import LocalIdentity

    return LocalIdentity.objects.filter(email=email).first()


def find_tenant(tenant_ref: str) -> Any:
    """Tenant row for an operator-supplied reference.

    The reference is the operator's ``--tenant`` value: a UUID (stored as the
    row id), the slug, or the name. Nothing is derived or invented here.
    """
    if not tenant_ref:
        return None
    from admin.platform.models import Tenant

    import uuid as uuid_mod

    try:
        tenant_id = uuid_mod.UUID(str(tenant_ref))
    except (ValueError, AttributeError, TypeError):
        tenant_id = None
    if tenant_id is not None:
        row = Tenant.objects.filter(id=tenant_id).first()
        if row is not None:
            return row
    return (
        Tenant.objects.filter(slug=tenant_ref).first()
        or Tenant.objects.filter(name=tenant_ref).first()
    )


def discover_sysadmin_identity() -> Tuple[Any, Optional[str]]:
    """Find the platform's sysadmin identity for a bare ``--check``.

    Returns ``(row, error)``. Exactly one active LocalIdentity holding the
    ``sysadmin`` role is required; zero or several is an error naming what to
    do — never a guess at which one matters.
    """
    from admin.platform.models import LocalIdentity

    rows = [
        r
        for r in LocalIdentity.objects.filter(is_active=True)
        if "sysadmin" in list(r.roles or [])
    ]
    if not rows:
        return None, "no active LocalIdentity holds role 'sysadmin'; run bootstrap_soma"
    if len(rows) > 1:
        return None, (
            f"{len(rows)} sysadmin identities exist; pass --sysadmin-email to name one"
        )
    return rows[0], None


def settings_chain_tenant_ref() -> Optional[str]:
    """The tenant this deployment defaults to, from the settings chain.

    ``SA01_DEFAULT_TENANT_ID`` is the designated default-tenant key. It is
    read through the chain (never env, never a literal); None means the chain
    has not been provisioned yet.
    """
    try:
        from admin.core.helpers.service_urls import require_setting

        raw = require_setting("SA01_DEFAULT_TENANT_ID")
    except Exception:  # noqa: BLE001 - "not configured" is a legal state here
        return None
    text = str(raw).strip()
    return text or None


@dataclass
class BootstrapContext:
    """Shared state for one bootstrap_soma run."""

    tenant: str
    sysadmin_email: str
    password_stdin: bool = False
    dry_run: bool = False
    check_only: bool = False
    skip_verify: bool = False
    phase_filter: Optional[str] = None
    json_output: bool = False

    password: Optional[str] = None
    pepper: Optional[str] = None

    # Objects handed between phases.
    identity: Any = None
    tenant_row: Any = None
    tenant_user: Any = None
    mimo_flash: Any = None
    capsule: Any = None
    agent: Any = None

    results: List[PhaseResult] = field(default_factory=list)

    def record(self, result: PhaseResult) -> PhaseResult:
        self.results.append(result)
        return result

    def read_password(self) -> str:
        """Password for the sysadmin identity.

        Exactly one line on stdin (never argv — argv is visible in `ps`).
        Interactive runs get a prompt; non-interactive runs are --password-stdin.
        """
        if self.password is not None:
            return self.password
        if not self.password_stdin:
            if sys.stdin.isatty():
                import getpass

                first = getpass.getpass(f"Password for {self.sysadmin_email}: ")
                confirm = getpass.getpass("Confirm: ")
                if first != confirm:
                    raise ConfigError("the two passwords did not match")
                self.password = first
                return first
            raise ConfigError(
                "no password supplied. Pass --password-stdin and pipe one line, "
                "or run interactively."
            )
        line = sys.stdin.readline().rstrip("\n")
        if not line:
            raise ConfigError("refusing to provision an identity with an empty password")
        self.password = line
        return line

    def exit_code(self) -> ExitCode:
        """Map phase results onto the stable exit-code contract."""
        statuses = {r.status for r in self.results}
        if "failed" in statuses:
            names = [r.name for r in self.results if r.status == "failed"]
            if any(n in ("preflight", "pepper") for n in names):
                return ExitCode.DEPENDENCY if "preflight" in names else ExitCode.CONFIG
            if "verify_chat_ready" in names:
                return ExitCode.VERIFY
            return ExitCode.PARTIAL
        if "partial" in statuses:
            return ExitCode.PARTIAL
        return ExitCode.OK

    def as_dict(self) -> Dict[str, Any]:
        return {
            "tenant": self.tenant,
            "sysadmin_email": self.sysadmin_email,
            "dry_run": self.dry_run,
            "check_only": self.check_only,
            "phases": [r.as_dict() for r in self.results],
            "exit_code": int(self.exit_code()),
        }


class ConfigError(RuntimeError):
    """Missing or invalid bootstrap configuration (exit code 1)."""


class DependencyError(RuntimeError):
    """DB / Vault / SomaBrain unreachable (exit code 4)."""
