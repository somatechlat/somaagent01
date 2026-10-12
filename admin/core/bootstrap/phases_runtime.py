"""Bootstrap phase P6: infrastructure keys + SomaBrain runtime settings.

P6 writes the ``InfrastructureConfig`` operator layer. Values are resolved
through the settings chain (Capsule → AgentSetting → InfrastructureConfig →
SettingsModel) — never from the process environment, never invented. What
this run provisioned is propagated honestly:

* ``SA01_DEFAULT_TENANT_ID``  ← the tenant row P3 just ensured
* ``SOMABRAIN_NAMESPACE``     ← the Capsule memory_pointer namespace (P5)
* ``MEM_EMBED_DIM``           ← the shared memory-contract constant
* ``SOMABRAIN_URL``           ← the chain only; empty stays empty

An empty deployment URL is a config error the operator resolves through the
settings chain — verify_chat_ready asserts it and exits 3. Never a guessed
host.

P6 also materialises SomaBrain's ``BrainSetting`` schema for the tenant over
the one HTTP trigger (``GET /brain/settings`` → ``ensure_seeded``), using
``require_service_url`` so the endpoint itself comes from the chain.
"""

from __future__ import annotations

from typing import Any, Optional

from admin.core.bootstrap.compare import decide_write
from admin.core.bootstrap.context import (
    BootstrapContext,
    ConfigError,
    DependencyError,
    PhaseResult,
    find_tenant,
)
from admin.core.bootstrap import seed_data

__all__ = ["phase_infra"]


def _chain_value(key: str, *, capsule: Any = None, agent_id: Optional[str] = None) -> Optional[str]:
    """Resolve one tunable through the settings chain. None = not configured.

    The chain never yields a guess: exhausted means "not configured", and the
    caller decides whether that is fatal. This is the only way P6 learns a
    value — there is no ``os.environ`` path.
    """
    from django.core.exceptions import ImproperlyConfigured

    from admin.core.helpers.service_urls import require_setting

    try:
        raw = require_setting(key, capsule=capsule, agent_id=agent_id)
    except ImproperlyConfigured:
        return None
    except Exception:  # noqa: BLE001 - ORM-not-ready etc. = "not configured"
        return None
    text = str(raw).strip()
    return text or None


def phase_infra(ctx: BootstrapContext) -> PhaseResult:
    """P6 — InfrastructureConfig service URLs via the settings chain, NOT env."""
    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    writes = 0
    skips = 0
    missing_required = []

    tenant_row = ctx.tenant_row
    if tenant_row is None and ctx.tenant:
        tenant_row = find_tenant(ctx.tenant)
    capsule = ctx.capsule

    # Values this run can state honestly because it just provisioned them.
    provisioned: dict[str, str] = {}
    if tenant_row is not None:
        provisioned["SA01_DEFAULT_TENANT_ID"] = str(tenant_row.id)
    if capsule is not None:
        pointer = getattr(capsule, "memory_pointer", None) or {}
        namespace = str(pointer.get("namespace") or "").strip()
        if namespace:
            provisioned["SOMABRAIN_NAMESPACE"] = namespace

    for service_name, key, value, value_type, editable, description in seed_data.INFRA_SEED_KEYS:
        service, _created = ServiceHealth.objects.get_or_create(
            service_name=service_name,
            defaults={
                "display_name": service_name.replace("_", " ").title(),
                "category": "core",
                "status": "unknown",
            },
        )
        existing = InfrastructureConfig.objects.filter(service=service, key=key).first()

        # Desired value, best first: what this run provisioned, then the
        # settings chain, then the seed's declared value (empty for every
        # deployment URL). Never env, never a literal host.
        desired = (
            provisioned.get(key)
            or _chain_value(key, capsule=capsule)
            or value
        )

        decision = decide_write(
            exists=existing is not None,
            current=(existing.value if existing else None),
            desired=desired,
            fill_only=True,  # operator-owned: never clobber an admin edit
        )
        if ctx.dry_run:
            if decision.wrote:
                writes += 1
            else:
                skips += 1
        elif decision.action == "create":
            InfrastructureConfig.objects.create(
                service=service,
                key=key,
                value=desired,
                default_value=value,
                is_secret=False,
                is_editable=editable,
                value_type=value_type,
                description=description,
            )
            writes += 1
        elif decision.wrote and existing is not None:
            existing.value = desired
            existing.save()
            writes += 1
        else:
            skips += 1

        # Fail-closed posture: a deployment URL that is still empty is a
        # config error the operator must resolve — never a guessed host.
        row = InfrastructureConfig.objects.filter(service=service, key=key).first()
        if key in ("SOMABRAIN_URL",) and (row is None or not (row.value or "").strip()):
            missing_required.append(key)

    detail = f"infrastructure keys seeded ({writes} wrote, {skips} skipped)"
    if missing_required:
        detail += (
            f"; REQUIRED still empty: {', '.join(missing_required)} — set through "
            "the settings chain before chat is usable"
        )
        # Not a hard failure here: verify_chat_ready asserts it and exits 3.

    # --- SomaBrain BrainSetting.ensure_seeded (one HTTP trigger) -----------
    brain_detail, brain_writes = _seed_brain_settings(ctx)
    detail += f"; {brain_detail}"
    writes += brain_writes

    return PhaseResult("infra", "ok", detail, writes=writes, skips=skips)


def _seed_brain_settings(ctx: BootstrapContext) -> tuple[str, int]:
    """Materialise BrainSetting schema on SomaBrain via the one HTTP trigger.

    ``GET /brain/settings`` calls ``BrainSetting.ensure_seeded`` on the
    credential's tenant. This never imports SomaBrain models into the agent
    process. When SOMABRAIN_URL is not configured the trigger is skipped and
    verify_chat_ready is what refuses the platform.
    """
    import asyncio

    from django.core.exceptions import ImproperlyConfigured

    from admin.core.helpers.service_urls import require_service_url

    try:
        brain_url = str(require_service_url("SOMABRAIN_URL")).strip()
    except ImproperlyConfigured as exc:
        return (
            f"BrainSetting.ensure_seeded skipped — SOMABRAIN_URL is not configured ({exc})",
            0,
        )
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(
            f"SOMABRAIN_URL is not resolvable ({type(exc).__name__}: {exc}). "
            "Set it through the settings chain before P6."
        ) from exc

    if not brain_url:
        raise ConfigError("SOMABRAIN_URL is empty; refusing to guess a brain host")

    from admin.core.somabrain_client import SomaBrainClient, SomaClientError
    from services.common.unified_secret_manager import get_secret_manager

    admin_token = get_secret_manager().get_credential("somabrain_admin_token")
    if not admin_token:
        raise ConfigError(
            "somabrain_admin_token is not provisioned in Vault "
            "(secret/agent/credentials/somabrain_admin_token). Admin routes "
            "refuse the shared memory token — provision the dedicated admin credential."
        )

    async def _trigger() -> Any:
        client = SomaBrainClient(base_url=brain_url)
        try:
            return await client._request(
                "GET",
                "/brain/settings",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        finally:
            await client.close()

    if ctx.dry_run:
        return (f"would GET {brain_url}/brain/settings to seed tenant {ctx.tenant}", 0)

    try:
        payload = asyncio.run(_trigger())
    except SomaClientError as exc:
        status = getattr(exc, "status_code", None)
        if status in (401, 403):
            raise DependencyError(
                f"SomaBrain rejected the admin token for /brain/settings: {exc}"
            ) from exc
        raise DependencyError(f"SomaBrain /brain/settings failed: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise DependencyError(f"SomaBrain unreachable: {type(exc).__name__}: {exc}") from exc

    seeded_tenant = str((payload or {}).get("tenant_id") or "")
    count = len((payload or {}).get("settings") or [])
    if not count:
        raise DependencyError(
            "SomaBrain /brain/settings returned no settings — BrainSetting.ensure_seeded "
            "did not materialise the schema"
        )
    return (
        f"BrainSetting.ensure_seeded via HTTP: tenant={seeded_tenant or ctx.tenant}, "
        f"{count} knobs materialised",
        1,
    )
