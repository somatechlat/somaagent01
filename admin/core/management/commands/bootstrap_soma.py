"""bootstrap_soma — one command that makes the agent chat-ready.

Eight idempotent fail-closed phases::

    P0 preflight        DB reachable, migrations applied, Vault reachable
    P1 pepper           reuse bootstrap_password_pepper (create-if-absent)
    P2 identity         LocalIdentity + roles=['sysadmin'] + password from stdin
    P3 tenant           Tenant + TenantUser(roles=['sysadmin'])
    P4 models           LLM catalog + the five Model Roles
                        (chat_role, utility_role, embedding_role,
                         vision_role, decision_role)
    P5 capsule          Capsule-complete; chat_model + image_model FK instances
    P6 infra            InfrastructureConfig service URLs via the settings
                        chain (NOT env) + SomaBrain BrainSetting.ensure_seeded
    P7 verify           verify_chat_ready — the gate, exit non-zero on fail

Exit codes: 0 ok · 1 config error · 2 partial · 3 verify fail · 4 dependency down.

Operator inputs are explicit or they are missing. Nothing here invents a
tenant, an email, a host or a credential::

    python manage.py bootstrap_soma --password-stdin --tenant <slug> \\
        --sysadmin-email <email>
    python manage.py bootstrap_soma --check
    python manage.py bootstrap_soma --phase capsule --dry-run --json

``--check`` is read-only: it writes nothing and answers "is the platform
already chat-ready?". ``--password-stdin`` reads one line on stdin — the
password never appears in argv.
"""

from __future__ import annotations

import json
import sys
from typing import Callable, Dict, List

from django.core.management.base import BaseCommand, CommandError

from admin.core.bootstrap.context import (
    BootstrapContext,
    ConfigError,
    DependencyError,
    PhaseResult,
    settings_chain_tenant_ref,
)
from admin.core.bootstrap.exit_codes import ExitCode
from admin.core.bootstrap.phases_core import (
    phase_identity,
    phase_pepper,
    phase_preflight,
    phase_tenant,
)
from admin.core.bootstrap.phases_models import phase_capsule, phase_models
from admin.core.bootstrap.phases_runtime import phase_infra
from admin.core.bootstrap.verify import run_verify_chat_ready

PHASES: Dict[str, Callable[[BootstrapContext], PhaseResult]] = {
    "preflight": phase_preflight,
    "pepper": phase_pepper,
    "identity": phase_identity,
    "tenant": phase_tenant,
    "models": phase_models,
    "capsule": phase_capsule,
    "infra": phase_infra,
    "verify": run_verify_chat_ready,
}

PHASE_ORDER: List[str] = [
    "preflight",
    "pepper",
    "identity",
    "tenant",
    "models",
    "capsule",
    "infra",
    "verify",
]

# Phases that write. ``--check`` never enters them.
WRITE_PHASES = frozenset({"models", "capsule", "infra"})


class Command(BaseCommand):
    """Provision identity, tenant, Model Roles, capsule, infra and verify chat-ready."""

    help = __doc__

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--check",
            action="store_true",
            help="report state only; write nothing",
        )
        parser.add_argument(
            "--phase",
            choices=PHASE_ORDER,
            default=None,
            help="run a single phase (still runs its prerequisites' reads)",
        )
        parser.add_argument(
            "--skip-verify",
            action="store_true",
            help="do not run P7 verify_chat_ready",
        )
        parser.add_argument(
            "--tenant",
            default=None,
            help="tenant slug/id (required for writes; no default)",
        )
        parser.add_argument(
            "--sysadmin-email",
            default=None,
            help="sysadmin identity email (required for writes; no default)",
        )
        parser.add_argument(
            "--password-stdin",
            action="store_true",
            help="read the sysadmin password as one line on stdin (never argv)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="compute write/skip decisions; change nothing",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="json_output",
            help="emit a machine-readable result on stdout",
        )

    def handle(self, *args, **options) -> None:
        # Rule 1: a default IS a hardcoded value. Identity inputs are operator
        # parameters — required on write, never invented here.
        tenant = options.get("tenant")
        email = options.get("sysadmin_email")
        if not options.get("check"):
            if not tenant:
                raise CommandError("--tenant is required (no default)")
            if not email:
                raise CommandError("--sysadmin-email is required (no default)")
        ctx = BootstrapContext(
            tenant=str(tenant or ""),
            sysadmin_email=str(email or ""),
            password_stdin=bool(options.get("password_stdin")),
            dry_run=bool(options.get("dry_run")),
            check_only=bool(options.get("check")),
            skip_verify=bool(options.get("skip_verify")),
            phase_filter=options.get("phase"),
            json_output=bool(options.get("json_output")),
        )

        selected = (
            [ctx.phase_filter]
            if ctx.phase_filter
            else list(PHASE_ORDER)
        )
        if ctx.skip_verify and "verify" in selected:
            selected = [p for p in selected if p != "verify"]

        try:
            self._resolve_check_scope(ctx)
            self._run_phases(ctx, selected)
        except ConfigError as exc:
            self._fail(ctx, ExitCode.CONFIG, str(exc))
        except DependencyError as exc:
            self._fail(ctx, ExitCode.DEPENDENCY, str(exc))
        except CommandError:
            raise
        except Exception as exc:  # noqa: BLE001 - last-resort honesty
            self._fail(ctx, ExitCode.PARTIAL, f"{type(exc).__name__}: {exc}")

        code = ctx.exit_code()

        if ctx.json_output:
            self.stdout.write(json.dumps(ctx.as_dict(), indent=2, default=str))
        else:
            for result in ctx.results:
                style = self.style.SUCCESS if result.status == "ok" else (
                    self.style.WARNING if result.status in ("partial", "skipped") else self.style.ERROR
                )
                self.stdout.write(
                    style(f"[{result.name}] {result.status}: {result.detail}")
                )
            self.stdout.write(f"exit_code={int(code)}")

        if code != ExitCode.OK:
            sys.exit(int(code))

    def _resolve_check_scope(self, ctx: BootstrapContext) -> None:
        """For bare ``--check``, resolve tenant/email from existing state.

        The write path already has them as explicit CLI. The check path (what
        start.sh runs) has none, so it reads what exists: the settings chain's
        ``SA01_DEFAULT_TENANT_ID``, and the unique sysadmin identity. Nothing
        is invented; an ambiguous or absent scope is reported by the verify
        asserts rather than guessed here.
        """
        if not ctx.check_only:
            return
        if not ctx.tenant:
            ctx.tenant = settings_chain_tenant_ref() or ""

    def _run_phases(self, ctx: BootstrapContext, selected: List[str]) -> None:
        """Run the selected phases.

        ``--phase NAME`` runs exactly that phase; later phases resolve their
        own dependencies from the database (fail-closed) so a single-phase run
        is honest even when earlier phases have not run in this process.

        ``--check`` never writes: write phases are skipped and the verify gate
        answers "is it already chat-ready?".
        """
        for name in selected:
            if ctx.check_only and name in WRITE_PHASES:
                ctx.record(PhaseResult(name, "skipped", "--check: write phase skipped"))
                continue
            fn = PHASES[name]
            result = fn(ctx)
            ctx.record(result)
            if result.status == "failed" and name != "verify":
                raise ConfigError(f"phase {name} failed: {result.detail}")

    def _fail(self, ctx: BootstrapContext, code: ExitCode, message: str) -> None:
        ctx.record(PhaseResult("bootstrap_soma", "failed", message))
        if ctx.json_output:
            self.stdout.write(json.dumps(ctx.as_dict(), indent=2, default=str))
        else:
            self.stderr.write(self.style.ERROR(message))
        sys.exit(int(code))
