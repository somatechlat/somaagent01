"""P7 — verify_chat_ready: the fail-closed gate that answers "chat-ready?".

Every assert is DB + settings-chain truth. Any failing assert fails the gate
and the command exits 3. ``--check`` is this gate alone: it writes nothing.

Operator identity is resolved, never invented. With ``--tenant`` /
``--sysadmin-email`` the asserts name those rows. Bare ``--check`` (the
start.sh path) discovers the unique sysadmin identity and the tenant from
``SA01_DEFAULT_TENANT_ID``; zero or several candidates is a reported failure,
never a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from admin.core.bootstrap.context import (
    BootstrapContext,
    PhaseResult,
    discover_sysadmin_identity,
    find_identity,
    find_tenant,
    settings_chain_tenant_ref,
)
from admin.core.bootstrap import seed_data

__all__ = ["Assert", "run_verify_chat_ready", "ASSERTS"]


@dataclass(frozen=True)
class Assert:
    """One named chat-ready guarantee."""

    id: str
    description: str
    check: Callable[[BootstrapContext], Optional[str]]

    def run(self, ctx: BootstrapContext) -> Optional[str]:
        try:
            return self.check(ctx)
        except Exception as exc:  # noqa: BLE001 - a raise is a failed assert
            return f"{type(exc).__name__}: {exc}"


# ── scope resolution (no invention) ────────────────────────────────────────


def _identity_row(ctx: BootstrapContext) -> Tuple[Any, Optional[str]]:
    """The identity these asserts cover, and why it could not be found."""
    if ctx.sysadmin_email:
        row = find_identity(ctx.sysadmin_email)
        return row, (None if row is not None else f"no LocalIdentity for {ctx.sysadmin_email}")
    row, error = discover_sysadmin_identity()
    return row, error


def _tenant_row(ctx: BootstrapContext) -> Tuple[Any, Optional[str]]:
    """The tenant these asserts cover, and why it could not be found."""
    ref = ctx.tenant or settings_chain_tenant_ref()
    if not ref:
        return None, (
            "tenant not named and SA01_DEFAULT_TENANT_ID is unset; "
            "pass --tenant or provision the settings chain"
        )
    row = find_tenant(ref)
    return row, (None if row is not None else f"tenant {ref!r} absent")


def _capsule_row(ctx: BootstrapContext) -> Tuple[Any, Optional[str]]:
    from admin.core.models import Capsule

    cap = (
        Capsule.objects.filter(name=seed_data.CAPSULE_NAME).order_by("-updated_at").first()
    )
    return cap, (None if cap is not None else f"capsule {seed_data.CAPSULE_NAME!r} missing")


def _role_setting(role: str) -> Tuple[Any, Optional[str]]:
    """Tenant-scope AgentSetting row for one Model Role."""
    from admin.core.models import AgentSetting
    from admin.llm.providers import DEFAULTS_AGENT_ID, ROLE_SETTING_KEYS

    key = ROLE_SETTING_KEYS[role]
    row = AgentSetting.objects.filter(agent_id=DEFAULTS_AGENT_ID, key=key).first()
    if row is None or not row.value:
        return None, f"Model Role {role} unbound (AgentSetting {key})"
    return row, None


# ── asserts ────────────────────────────────────────────────────────────────


def _a1_identity_exists(ctx: BootstrapContext) -> Optional[str]:
    _row, error = _identity_row(ctx)
    return error


def _a2_identity_active_sysadmin(ctx: BootstrapContext) -> Optional[str]:
    row, error = _identity_row(ctx)
    if error is not None:
        return error
    if not row.is_active:
        return "identity is inactive"
    if "sysadmin" not in list(row.roles or []):
        return f"roles={row.roles!r} lacks 'sysadmin'"
    return None


def _a3_identity_username(ctx: BootstrapContext) -> Optional[str]:
    row, error = _identity_row(ctx)
    if error is not None:
        return error
    return None if row.username else "username empty"


def _a4_password_hash_set(ctx: BootstrapContext) -> Optional[str]:
    row, error = _identity_row(ctx)
    if error is not None:
        return error
    return None if row.password_hash else "password_hash empty"


def _a5_tenant_exists(ctx: BootstrapContext) -> Optional[str]:
    _row, error = _tenant_row(ctx)
    return error


def _a6_tenant_user_sysadmin(ctx: BootstrapContext) -> Optional[str]:
    from admin.platform.models import TenantUser

    identity, id_error = _identity_row(ctx)
    tenant, t_error = _tenant_row(ctx)
    if id_error is not None or t_error is not None:
        return id_error or t_error
    tu = TenantUser.objects.filter(tenant=tenant, user_id=identity.id).first()
    if tu is None:
        return "TenantUser row missing"
    # TenantUser.roles is the one role store — a JSON list, never a column.
    if "sysadmin" not in list(tu.roles or []):
        return f"TenantUser.roles={tu.roles!r} lacks 'sysadmin'"
    return None


def _a7_chat_catalog_row(ctx: BootstrapContext) -> Optional[str]:
    from admin.llm.models import LLMModelConfig

    row = LLMModelConfig.objects.filter(name=seed_data.MIMO_FLASH_NAME).first()
    return None if row is not None else f"{seed_data.MIMO_FLASH_NAME} catalog row missing"


def _a8_chat_default_priority(ctx: BootstrapContext) -> Optional[str]:
    from admin.llm.models import LLMModelConfig

    row = LLMModelConfig.objects.filter(name=seed_data.MIMO_FLASH_NAME).first()
    if row is None:
        return f"{seed_data.MIMO_FLASH_NAME} missing"
    if not row.is_active:
        return f"{seed_data.MIMO_FLASH_NAME} is_active=False"
    if row.priority != 100:
        return f"{seed_data.MIMO_FLASH_NAME} priority={row.priority} != 100 (must win priority DESC)"
    return None


def _a9_groq_present(ctx: BootstrapContext) -> Optional[str]:
    from admin.llm.models import LLMModelConfig

    for row in seed_data.GROQ_MODEL_ROWS:
        name = row["name"]
        if LLMModelConfig.objects.filter(name=name).first() is None:
            return f"groq model {name} missing"
    return None


def _a10_embedding_present(ctx: BootstrapContext) -> Optional[str]:
    from admin.llm.models import LLMModelConfig

    row = LLMModelConfig.objects.filter(model_type="embedding", is_active=True).first()
    return None if row is not None else "no active embedding model"


def _a11_decision_catalog_row(ctx: BootstrapContext) -> Optional[str]:
    from admin.llm.models import LLMModelConfig

    name = seed_data.CLEF_DECISION_ROW["name"]
    row = LLMModelConfig.objects.filter(name=name).first()
    return None if row is not None else f"{name} catalog row missing"


def _a12_capsule_active(ctx: BootstrapContext) -> Optional[str]:
    from admin.core.models import Capsule

    cap, error = _capsule_row(ctx)
    if error is not None:
        return error
    if cap.status != Capsule.STATUS_ACTIVE:
        return f"capsule status={cap.status!r} != 'active'"
    return None


def _a13_capsule_model_fks(ctx: BootstrapContext) -> Optional[str]:
    """chat_role and vision_role as Capsule sovereignty FKs (Rule 91)."""
    from admin.llm.models import LLMModelConfig

    cap, error = _capsule_row(ctx)
    if error is not None:
        return error
    problems = []
    for field_name, role in (("chat_model", "chat_role"), ("image_model", "vision_role")):
        fk_id = getattr(cap, f"{field_name}_id", None)
        if fk_id is None:
            problems.append(f"{role}: Capsule.{field_name} FK is NULL")
            continue
        bound = getattr(cap, field_name, None)
        if not isinstance(bound, LLMModelConfig):
            problems.append(
                f"{role}: Capsule.{field_name} is {type(bound).__name__}, "
                "must be an LLMModelConfig instance (never a string)"
            )
        elif not bound.is_active:
            problems.append(f"{role}: bound {field_name} is inactive")
    return "; ".join(problems) if problems else None


def _a14_personality_big5(ctx: BootstrapContext) -> Optional[str]:
    cap, error = _capsule_row(ctx)
    if error is not None:
        return error
    traits = dict(cap.personality_traits or {})
    missing = [n for n in seed_data.BIG5_TRAIT_NAMES if n not in traits]
    return f"Big-5 missing {missing}" if missing else None


def _a15_neuromodulator_baseline(ctx: BootstrapContext) -> Optional[str]:
    cap, error = _capsule_row(ctx)
    if error is not None:
        return error
    base = dict(cap.neuromodulator_baseline or {})
    missing = [n for n in seed_data.DEFAULT_NEUROMODULATOR_BASELINE if n not in base]
    return f"neuromodulator_baseline missing {missing}" if missing else None


def _a16_knobs_and_memory_pointer(ctx: BootstrapContext) -> Optional[str]:
    cap, error = _capsule_row(ctx)
    if error is not None:
        return error
    knobs = dict((cap.persona_config or {}).get("knobs") or {})
    missing_knobs = [n for n in seed_data.DEFAULT_KNOBS if n not in knobs]
    if missing_knobs:
        return f"persona_config.knobs missing {missing_knobs}"
    ptr = dict(cap.memory_pointer or {})
    for name in seed_data.DEFAULT_MEMORY_POINTER_KEYS:
        if name not in ptr or ptr[name] in (None, ""):
            return f"memory_pointer missing/empty {name}"
    if not cap.system_prompt:
        return "system_prompt empty"
    if not cap.learning_config:
        return "learning_config empty"
    return None


def _a17_infra_chain(ctx: BootstrapContext) -> Optional[str]:
    from admin.core.infrastructure.models import InfrastructureConfig

    from services.common.memory_contract import DEFAULT_MEM_EMBED_DIM

    def _value(key: str) -> str:
        row = InfrastructureConfig.objects.filter(key=key).first()
        return (row.value or "").strip() if row else ""

    problems = []
    if not _value("SOMABRAIN_NAMESPACE"):
        problems.append("SOMABRAIN_NAMESPACE empty")
    embed = _value("MEM_EMBED_DIM")
    expected = str(DEFAULT_MEM_EMBED_DIM)
    if embed != expected:
        problems.append(f"MEM_EMBED_DIM={embed!r} != {expected!r}")
    if not _value("SA01_DEFAULT_TENANT_ID"):
        problems.append("SA01_DEFAULT_TENANT_ID empty")
    return "; ".join(problems) if problems else None


def _a18_brain_url_configured(ctx: BootstrapContext) -> Optional[str]:
    """SOMABRAIN_URL must be resolvable through the settings chain, not env."""
    from django.core.exceptions import ImproperlyConfigured

    from admin.core.helpers.service_urls import require_service_url

    try:
        url = str(require_service_url("SOMABRAIN_URL")).strip()
    except ImproperlyConfigured:
        return "SOMABRAIN_URL empty — chat memory lane is unconfigured"
    except Exception as exc:  # noqa: BLE001
        return f"SOMABRAIN_URL unresolvable: {type(exc).__name__}: {exc}"
    return None if url else "SOMABRAIN_URL empty — chat memory lane is unconfigured"


def _a19_model_roles_bound(ctx: BootstrapContext) -> Optional[str]:
    """All five Model Roles bound at tenant scope."""
    from admin.llm.providers import MODEL_ROLES

    problems = []
    for role in MODEL_ROLES:
        _row, error = _role_setting(role)
        if error is not None:
            problems.append(error)
    return "; ".join(problems) if problems else None


ASSERTS: List[Assert] = [
    Assert("A1", "LocalIdentity exists for sysadmin email", _a1_identity_exists),
    Assert("A2", "identity active with roles containing sysadmin", _a2_identity_active_sysadmin),
    Assert("A3", "identity username set", _a3_identity_username),
    Assert("A4", "password_hash set", _a4_password_hash_set),
    Assert("A5", "Tenant row exists", _a5_tenant_exists),
    Assert("A6", "TenantUser roles contain sysadmin", _a6_tenant_user_sysadmin),
    Assert("A7", f"{seed_data.MIMO_FLASH_NAME} catalog row exists", _a7_chat_catalog_row),
    Assert("A8", f"{seed_data.MIMO_FLASH_NAME} active at priority 100", _a8_chat_default_priority),
    Assert("A9", "groq chat models seeded", _a9_groq_present),
    Assert("A10", "embedding model present", _a10_embedding_present),
    Assert("A11", "decision catalog row present", _a11_decision_catalog_row),
    Assert("A12", "Capsule status=active", _a12_capsule_active),
    Assert("A13", "Capsule chat_model + image_model FKs bound (Rule 91)", _a13_capsule_model_fks),
    Assert("A14", "Big-5 personality_traits complete", _a14_personality_big5),
    Assert("A15", "neuromodulator_baseline complete", _a15_neuromodulator_baseline),
    Assert("A16", "knobs + memory_pointer + system_prompt + learning_config", _a16_knobs_and_memory_pointer),
    Assert("A17", "InfrastructureConfig namespace/tenant/embed_dim", _a17_infra_chain),
    Assert("A18", "SOMABRAIN_URL configured via settings chain", _a18_brain_url_configured),
    Assert("A19", "all five Model Roles bound at tenant scope", _a19_model_roles_bound),
]


def run_verify_chat_ready(ctx: BootstrapContext) -> PhaseResult:
    """Run every assert. Status 'ok' only when every one passes."""
    failures: List[str] = []
    for assertion in ASSERTS:
        error = assertion.run(ctx)
        if error is not None:
            failures.append(f"{assertion.id} ({assertion.description}): {error}")

    if failures:
        return PhaseResult(
            "verify_chat_ready",
            "failed",
            f"{len(failures)}/{len(ASSERTS)} asserts failed: " + " | ".join(failures),
        )
    return PhaseResult(
        "verify_chat_ready",
        "ok",
        f"all {len(ASSERTS)} chat-ready asserts passed",
    )
