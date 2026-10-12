"""Bootstrap phases P0–P3: preflight, pepper, identity, tenant.

Each phase is a function ``phase_*(ctx) -> PhaseResult``. Fail-closed: a
missing dependency raises, it never degrades into a guessed default. Every
write is get_or_create / update_or_create, and operator-owned rows are left
alone (compare-before-write).

Identity inputs come from the operator (``--tenant`` / ``--sysadmin-email`` /
``--password-stdin``) or from rows that already exist. This module invents
neither: an unusable email raises instead of falling back to a placeholder
username (Rule 1 / Rule 3).
"""

from __future__ import annotations

from typing import Any

from admin.core.bootstrap.context import (
    BootstrapContext,
    ConfigError,
    DependencyError,
    PhaseResult,
    find_identity,
    find_tenant,
)

__all__ = [
    "phase_preflight",
    "phase_pepper",
    "phase_identity",
    "phase_tenant",
]


def phase_preflight(ctx: BootstrapContext) -> PhaseResult:
    """P0 — DB reachable, Vault reachable, migrations applied.

    Runs in ``--check`` too: a check that cannot reach the database is not a
    clean bill of health.
    """
    # --- DB -------------------------------------------------------------
    try:
        from django.db import connection

        connection.ensure_connection()
    except Exception as exc:  # noqa: BLE001 - any failure is "dependency down"
        raise DependencyError(f"database unreachable: {type(exc).__name__}: {exc}") from exc

    # --- migrations -----------------------------------------------------
    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            names = ", ".join(f"{m.app_label}.{m.name}" for m, _ in plan[:8])
            raise DependencyError(
                f"unapplied migrations ({len(plan)} pending: {names}). "
                "Run `python manage.py migrate` first."
            )
    except DependencyError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DependencyError(f"migration state unreadable: {exc}") from exc

    # --- Vault ----------------------------------------------------------
    try:
        from services.common.identity.pepper import get_password_pepper

        get_password_pepper()
    except Exception as exc:  # noqa: BLE001
        # Absent pepper is the case P1 exists for; unreachable Vault is not.
        name = type(exc).__name__
        if name in ("MissingPasswordPepper",):
            return PhaseResult(
                "preflight",
                "ok",
                "database ready; pepper not yet provisioned (P1 will create it)",
            )
        raise DependencyError(f"vault unreachable: {name}: {exc}") from exc

    return PhaseResult("preflight", "ok", "database, migrations and vault ready")


def phase_pepper(ctx: BootstrapContext) -> PhaseResult:
    """P1 — password pepper. Reuse bootstrap_password_pepper (create-if-absent)."""
    if ctx.check_only:
        from services.common.identity.pepper import PASSWORD_PEPPER_VAULT_KEY, get_password_pepper

        try:
            get_password_pepper()
        except Exception as exc:  # noqa: BLE001
            raise ConfigError(f"identity_password_pepper: NOT provisioned ({exc})") from exc
        ctx.pepper = "present"
        return PhaseResult("pepper", "ok", f"pepper present at {PASSWORD_PEPPER_VAULT_KEY}")

    from services.common.identity.pepper import (
        PASSWORD_PEPPER_VAULT_KEY,
        bootstrap_password_pepper,
        get_password_pepper,
    )

    # Dry-run: report the decision, never write (the --dry-run contract).
    if ctx.dry_run:
        try:
            get_password_pepper()
            ctx.pepper = "present"
            return PhaseResult(
                "pepper",
                "ok",
                f"pepper already present at {PASSWORD_PEPPER_VAULT_KEY} (dry-run)",
                skips=1,
            )
        except Exception:  # noqa: BLE001 - absent is the create-if-absent case
            return PhaseResult(
                "pepper",
                "ok",
                f"would create pepper at {PASSWORD_PEPPER_VAULT_KEY} (dry-run)",
                writes=1,
            )

    # Reuse the audited helper: create-if-absent, never overwrite.
    pepper = bootstrap_password_pepper()
    ctx.pepper = pepper
    return PhaseResult(
        "pepper",
        "ok",
        f"pepper ready at secret/agent/credentials/{PASSWORD_PEPPER_VAULT_KEY} "
        f"(value not shown; it is in Vault and nowhere else)",
        writes=1,
    )


def _username_from_email(email: str) -> str:
    """Sign-in name derived from the operator-supplied email.

    The local part is used verbatim. An email that cannot yield one raises —
    there is no fallback name (Rule 1: a default is a hardcoded value).
    """
    local = str(email).split("@", 1)[0].strip().lower()
    if not local:
        raise ConfigError(
            f"cannot derive a username from {email!r}; pass a normal email address"
        )
    return local


def phase_identity(ctx: BootstrapContext) -> PhaseResult:
    """P2 — LocalIdentity with roles containing 'sysadmin', password from stdin.

    The password goes through ``LocalIdentity.set_password`` so the real
    password policy (privileged minimum length included) is enforced —
    bootstrap must not be a back door around the credential rules.
    Existing roles are never clobbered: 'sysadmin' is added, the rest kept.
    """
    if ctx.check_only:
        from admin.core.bootstrap.context import discover_sysadmin_identity

        if not ctx.sysadmin_email:
            row, error = discover_sysadmin_identity()
            if error is not None:
                return PhaseResult("identity", "partial", error)
            ctx.identity = row
            ctx.sysadmin_email = row.email
            return PhaseResult(
                "identity", "ok", f"{row.email} active with sysadmin (discovered)"
            )

        row = find_identity(ctx.sysadmin_email)
        if row is None:
            return PhaseResult("identity", "partial", f"no identity for {ctx.sysadmin_email}")
        roles = list(row.roles or [])
        if "sysadmin" not in roles:
            return PhaseResult(
                "identity", "partial", f"{ctx.sysadmin_email} lacks sysadmin role"
            )
        if not row.is_active:
            return PhaseResult("identity", "partial", f"{ctx.sysadmin_email} is inactive")
        if not (row.password_hash or "").strip():
            return PhaseResult(
                "identity", "partial", f"{ctx.sysadmin_email} has no password set"
            )
        return PhaseResult("identity", "ok", f"{ctx.sysadmin_email} active with sysadmin")

    from admin.platform.models import LocalIdentity
    from services.common.identity.password import PasswordPolicyError

    username = _username_from_email(ctx.sysadmin_email)
    existing = find_identity(ctx.sysadmin_email)
    needs_password = existing is None or not (existing.password_hash or "").strip()
    rotate = ctx.password is not None or ctx.password_stdin

    # Dry-run: report the decision and stop. Pepper is not resolved here —
    # P1 may have reported "would create", so the value may not exist yet.
    if ctx.dry_run:
        if existing is None:
            return PhaseResult(
                "identity",
                "ok",
                f"would create {ctx.sysadmin_email} as sysadmin (dry-run)",
                writes=1,
            )
        detail = f"{ctx.sysadmin_email} already provisioned"
        if needs_password or rotate:
            detail = f"would set password for {ctx.sysadmin_email} (dry-run)"
        return PhaseResult("identity", "ok", detail, writes=int(needs_password or rotate))

    from services.common.identity.pepper import get_password_pepper

    pepper = ctx.pepper or get_password_pepper()

    # Build/patch the row with roles first, so set_password's privileged
    # policy branch sees the sysadmin role and applies the stricter minimum.
    if existing is None:
        row = LocalIdentity(
            email=ctx.sysadmin_email,
            username=username,
            display_name=username,
            roles=["sysadmin"],
            is_active=True,
        )
        created = True
    else:
        row = existing
        created = False
        roles = list(row.roles or [])
        if "sysadmin" not in roles:
            row.roles = [*roles, "sysadmin"]
        if not row.username:
            row.username = username
        if not row.display_name:
            row.display_name = row.username or username
        if not row.is_active:
            row.is_active = True

    wrote = created
    if needs_password or rotate:
        password = ctx.read_password()
        if not password:
            raise ConfigError("refusing to provision an identity with an empty password")
        try:
            row.set_password(password, pepper)
        except PasswordPolicyError as exc:
            raise ConfigError(f"password rejected by policy: {exc}") from exc
        wrote = True

    row.save()
    ctx.identity = row

    if created:
        return PhaseResult("identity", "ok", f"created {ctx.sysadmin_email} as sysadmin", writes=1)
    if wrote:
        return PhaseResult("identity", "ok", f"updated {ctx.sysadmin_email}", writes=1)
    return PhaseResult(
        "identity", "ok", f"{ctx.sysadmin_email} already provisioned", writes=0, skips=1
    )


def phase_tenant(ctx: BootstrapContext) -> PhaseResult:
    """P3 — Tenant + TenantUser(roles=['sysadmin']) bound to the identity."""
    from admin.platform.models import LocalIdentity, Tenant, TenantUser
    from admin.platform.models.choices import TenantStatus

    if ctx.check_only:
        if not ctx.tenant:
            from admin.core.bootstrap.context import settings_chain_tenant_ref

            ref = settings_chain_tenant_ref()
            if ref is None:
                return PhaseResult(
                    "tenant",
                    "partial",
                    "tenant not named and SA01_DEFAULT_TENANT_ID is unset; "
                    "pass --tenant or provision the settings chain",
                )
            ctx.tenant = ref
        tenant = find_tenant(ctx.tenant)
        if tenant is None:
            return PhaseResult("tenant", "partial", f"tenant {ctx.tenant!r} absent")
        return PhaseResult("tenant", "ok", f"tenant {tenant.slug} present")

    # Tenant slug is the partition key; id stays a UUID. When the operator
    # passed a UUID we store it as the row id so SA01_DEFAULT_TENANT_ID can
    # name it without inventing a second identifier.
    import uuid as uuid_mod

    tenant_id: Any = None
    try:
        tenant_id = uuid_mod.UUID(str(ctx.tenant))
        tenant = Tenant.objects.filter(id=tenant_id).first()
        defaults = {
            "name": ctx.tenant,
            # The slug is the operator's reference verbatim when it is already
            # slug-shaped; a UUID reference has no other name to use, so the
            # UUID string itself is the slug. Never a generated placeholder.
            "slug": str(tenant_id),
            "status": TenantStatus.ACTIVE,
        }
    except (ValueError, AttributeError, TypeError):
        tenant = Tenant.objects.filter(slug=ctx.tenant).first() or Tenant.objects.filter(
            name=ctx.tenant
        ).first()
        defaults = {
            "name": ctx.tenant,
            "slug": ctx.tenant,
            "status": TenantStatus.ACTIVE,
        }

    writes = 0
    skips = 0

    if tenant is None:
        if not ctx.dry_run:
            if tenant_id is not None:
                defaults["id"] = tenant_id
            tenant = Tenant.objects.create(**defaults)
        writes += 1
    else:
        skips += 1

    identity = ctx.identity
    if identity is None:
        identity = find_identity(ctx.sysadmin_email)
    if identity is None:
        raise ConfigError(
            f"no LocalIdentity for {ctx.sysadmin_email}; P2 must run before P3"
        )

    existing_tu = None
    if tenant is not None:
        existing_tu = TenantUser.objects.filter(tenant=tenant, user_id=identity.id).first()

    if existing_tu is None:
        if not ctx.dry_run and tenant is not None:
            TenantUser.objects.create(
                tenant=tenant,
                user_id=identity.id,
                email=ctx.sysadmin_email,
                display_name=identity.display_name or identity.username,
                roles=["sysadmin"],
                is_active=True,
            )
        writes += 1
    else:
        # TenantUser.roles is the one role store (JSON list). Merge the role
        # in; never replace the list and never touch a singular 'role' column
        # that does not exist.
        roles = list(existing_tu.roles or [])
        changed = False
        if "sysadmin" not in roles:
            existing_tu.roles = [*roles, "sysadmin"]
            changed = True
        if not existing_tu.is_active:
            existing_tu.is_active = True
            changed = True
        if changed and not ctx.dry_run:
            existing_tu.save()
            writes += 1
        else:
            skips += 1

    ctx.tenant_row = tenant
    if existing_tu is not None:
        ctx.tenant_user = existing_tu
    elif tenant is not None and not ctx.dry_run:
        ctx.tenant_user = TenantUser.objects.get(tenant=tenant, user_id=identity.id)

    label = getattr(tenant, "slug", ctx.tenant) if tenant is not None else ctx.tenant
    return PhaseResult(
        "tenant",
        "ok",
        f"tenant {label} + TenantUser(sysadmin) for {ctx.sysadmin_email}",
        writes=writes,
        skips=skips,
    )
