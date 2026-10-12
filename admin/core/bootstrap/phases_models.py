"""Bootstrap phases P4–P5: Model Roles and the Capsule-complete contract.

P4 re-asserts the LLM catalog and binds the five Model Roles of
``admin.llm.providers.MODEL_ROLES`` — ``chat_role`` / ``utility_role`` /
``embedding_role`` / ``vision_role`` / ``decision_role`` — into the
tenant-defaults ``AgentSetting`` scope. Role binding keys come from
``ROLE_SETTING_KEYS``; the model each role binds is named in
``seed_data.MODEL_ROLE_DEFAULTS``. Model ids are stored, never names.

P5 writes a Capsule with **every** field populated and the two model
sovereignty FKs bound as real ``LLMModelConfig`` instances — never a string:
``chat_model`` (chat_role) and ``image_model`` (vision_role).
"""

from __future__ import annotations

from typing import Any, Optional

from admin.core.bootstrap.compare import decide_write
from admin.core.bootstrap.context import (
    BootstrapContext,
    ConfigError,
    PhaseResult,
    find_tenant,
)
from admin.core.bootstrap import seed_data

__all__ = ["phase_models", "phase_capsule"]


def _clef_api_base() -> str:
    """CLEF_API_BASE from the settings chain, empty when not configured.

    Empty is honest: the decision row is catalog, its deployment endpoint is
    operator configuration (bootstrap_clef / the settings UI). Nothing here
    reads the process environment and nothing invents a host.
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    raw = resolve_setting("CLEF_API_BASE")
    return str(raw).strip().rstrip("/") if raw else ""


def _agent_setting_row(agent_id: str, key: str) -> Any:
    from admin.core.models import AgentSetting

    return AgentSetting.objects.filter(agent_id=agent_id, key=key).first()


def _create_agent_setting(agent_id: str, key: str, value: str) -> None:
    from admin.core.models import AgentSetting

    AgentSetting.objects.create(agent_id=agent_id, key=key, value=value, is_secret=False)


def _bind_role_setting(
    ctx: BootstrapContext,
    scope_id: str,
    role: str,
    model: Any,
    writes: int,
    skips: int,
) -> tuple[int, int]:
    """Bind one Model Role into an AgentSetting scope (fill-if-absent)."""
    from admin.llm.providers import ROLE_SETTING_KEYS

    key = ROLE_SETTING_KEYS[role]
    existing = _agent_setting_row(scope_id, key)
    desired = str(model.id)
    decision = decide_write(
        exists=existing is not None,
        current=None if existing is None else (existing.value or None),
        desired=desired,
        fill_only=True,  # an operator re-bind wins
    )
    if ctx.dry_run:
        return (writes + 1, skips) if decision.wrote else (writes, skips + 1)
    if decision.action == "create":
        _create_agent_setting(scope_id, key, desired)
        return writes + 1, skips
    if decision.wrote and existing is not None:
        existing.value = desired
        existing.save()
        return writes + 1, skips
    return writes, skips + 1


def phase_models(ctx: BootstrapContext) -> PhaseResult:
    """P4 — LLM catalog + the five Model Roles bound at tenant scope."""
    from admin.llm.models import LLMModelConfig
    from admin.llm.providers import DEFAULTS_AGENT_ID, MODEL_ROLES, ROLE_SETTING_KEYS

    writes = 0
    skips = 0

    # --- catalog ---------------------------------------------------------
    for row in seed_data.LLM_SEED_ROWS:
        defaults = {k: v for k, v in row.items() if k != "name"}
        is_clef = row["name"] == seed_data.CLEF_DECISION_ROW["name"]
        if is_clef:
            # A deployment endpoint is operator-owned: fill it when empty,
            # never clobber an admin edit.
            existing = LLMModelConfig.objects.filter(name=row["name"]).first()
            resolved = _clef_api_base()
            defaults["api_base"] = (
                existing.api_base if (existing is not None and existing.api_base) else resolved
            )

        existing = LLMModelConfig.objects.filter(name=row["name"]).first()
        # Seed-owned catalog: write when the row is absent or any seed field
        # has drifted. An unchanged re-assert is a skip (compare-before-write).
        changed = existing is None or any(
            getattr(existing, key, None) != value for key, value in defaults.items()
        )
        if ctx.dry_run:
            if changed:
                writes += 1
            else:
                skips += 1
            continue
        if not changed:
            skips += 1
            continue
        LLMModelConfig.objects.update_or_create(name=row["name"], defaults=defaults)
        writes += 1

    if ctx.dry_run:
        ctx.mimo_flash = LLMModelConfig.objects.filter(
            name=seed_data.MIMO_FLASH_NAME
        ).first()
        # Dry-run must also compute the Model Role binding decisions — the
        # contract is "compute write/skip decisions; change nothing".
        for role in MODEL_ROLES:
            model_name = seed_data.MODEL_ROLE_DEFAULTS.get(role)
            if not model_name:
                raise ConfigError(f"no seed model declared for Model Role {role!r}")
            model = LLMModelConfig.objects.filter(name=model_name, is_active=True).first()
            if model is None:
                raise ConfigError(
                    f"model {model_name!r} for {role} is missing or inactive in the catalog"
                )
            key = ROLE_SETTING_KEYS[role]
            existing_setting = _agent_setting_row(DEFAULTS_AGENT_ID, key)
            decision = decide_write(
                exists=existing_setting is not None,
                current=None if existing_setting is None else (existing_setting.value or None),
                desired=str(model.id),
                fill_only=True,
            )
            if decision.wrote:
                writes += 1
            else:
                skips += 1
        return PhaseResult(
            "models",
            "ok",
            f"catalog + {len(MODEL_ROLES)} Model Roles would be re-asserted; "
            f"default chat model = {seed_data.MIMO_FLASH_NAME}",
            writes=writes,
            skips=skips,
        )

    ctx.mimo_flash = LLMModelConfig.objects.filter(name=seed_data.MIMO_FLASH_NAME).first()
    if ctx.mimo_flash is None:
        raise ConfigError("mimo-flash row missing after catalog seed")

    # --- five Model Roles -------------------------------------------------
    # chat_role and vision_role are ALSO bound as Capsule FKs in P5. The
    # tenant-scope AgentSetting row is what the roles API reads when no
    # capsule is named, so all five are bound here.
    bound = []
    for role in MODEL_ROLES:
        if role not in seed_data.MODEL_ROLE_DEFAULTS:
            raise ConfigError(f"no seed model declared for Model Role {role!r}")
        model_name = seed_data.MODEL_ROLE_DEFAULTS[role]
        model = LLMModelConfig.objects.filter(name=model_name, is_active=True).first()
        if model is None:
            raise ConfigError(
                f"model {model_name!r} for {role} is missing or inactive in the catalog"
            )
        writes, skips = _bind_role_setting(
            ctx, DEFAULTS_AGENT_ID, role, model, writes, skips
        )
        bound.append(role)

    detail = (
        f"catalog re-asserted; Model Roles bound: {', '.join(bound)} "
        f"(scope agent_id={DEFAULTS_AGENT_ID})"
    )
    return PhaseResult("models", "ok", detail, writes=writes, skips=skips)


def phase_capsule(ctx: BootstrapContext) -> PhaseResult:
    """P5 — Capsule-complete: every field explicit, model FKs are instances.

    Fields written when empty (operator-owned fill-if-absent):
      system_prompt, personality_traits (Big-5), neuromodulator_baseline,
      learning_config, persona_config.knobs, memory_pointer, status=active.
    Model sovereignty FKs (Rule 91) bound as LLMModelConfig instances:
      chat_model  <- chat_role
      image_model <- vision_role
    """
    from admin.core.models import Capsule
    from admin.llm.models import LLMModelConfig
    from admin.llm.providers import MODEL_ROLES
    from admin.platform.models import Agent

    tenant = ctx.tenant_row
    if tenant is None:
        tenant = find_tenant(ctx.tenant)
    if tenant is None:
        raise ConfigError(f"tenant {ctx.tenant!r} absent; P3 must run before P5")

    def _role_model(role: str) -> LLMModelConfig:
        name = seed_data.MODEL_ROLE_DEFAULTS.get(role)
        if not name:
            raise ConfigError(f"no seed model declared for Model Role {role!r}")
        row = LLMModelConfig.objects.filter(name=name, is_active=True).first()
        if row is None:
            raise ConfigError(f"model {name!r} for {role} is missing from the catalog")
        return row

    chat_model = ctx.mimo_flash or _role_model("chat_role")
    vision_model = _role_model("vision_role")

    writes = 0
    skips = 0

    # --- Capsule ---------------------------------------------------------
    capsule = (
        Capsule.objects.filter(tenant=tenant, name=seed_data.CAPSULE_NAME)
        .order_by("-updated_at")
        .first()
    )
    if capsule is None:
        if ctx.dry_run:
            writes += 1
            capsule = None
        else:
            capsule = Capsule.objects.create(
                tenant=tenant,
                name=seed_data.CAPSULE_NAME,
                version="1.0.0",
                status=Capsule.STATUS_ACTIVE,
                system_prompt=seed_data.DEFAULT_SYSTEM_PROMPT,
                personality_traits=dict(seed_data.DEFAULT_PERSONALITY_TRAITS),
                neuromodulator_baseline=dict(seed_data.DEFAULT_NEUROMODULATOR_BASELINE),
                learning_config=dict(seed_data.DEFAULT_LEARNING_CONFIG),
                chat_model=chat_model,
                image_model=vision_model,
                persona_config={
                    "knobs": dict(seed_data.DEFAULT_KNOBS),
                    "prompts": {"injection_prompts": [], "tool_prompts": {}},
                    "memory": {
                        "recall_limit": seed_data.DEFAULT_RECALL_LIMIT,
                        "similarity_threshold": seed_data.DEFAULT_SIMILARITY_THRESHOLD,
                    },
                    # lane_preferences is ABSENT on purpose: the governor is
                    # the one ratio authority.  An empty mapping here would be
                    # "present but malformed" and the lane resolver refuses it
                    # (Rule 2/91) instead of falling through to defaults.
                    "learned": {},
                },
                memory_pointer={},
                is_active=True,
            )
            writes += 1
    else:
        # Fill-if-absent on every capsule-complete field. Model FKs are never
        # written as a string — always an LLMModelConfig instance.
        dirty_fields: list[str] = []

        if not capsule.system_prompt:
            capsule.system_prompt = seed_data.DEFAULT_SYSTEM_PROMPT
            dirty_fields.append("system_prompt")

        traits = dict(capsule.personality_traits or {})
        for name, value in seed_data.DEFAULT_PERSONALITY_TRAITS.items():
            if name not in traits:
                traits[name] = value
                dirty_fields.append("personality_traits")
        capsule.personality_traits = traits

        neuro = dict(capsule.neuromodulator_baseline or {})
        for name, value in seed_data.DEFAULT_NEUROMODULATOR_BASELINE.items():
            if name not in neuro:
                neuro[name] = value
                dirty_fields.append("neuromodulator_baseline")
        capsule.neuromodulator_baseline = neuro

        learning = dict(capsule.learning_config or {})
        for name, value in seed_data.DEFAULT_LEARNING_CONFIG.items():
            if name not in learning:
                learning[name] = value
                dirty_fields.append("learning_config")
        capsule.learning_config = learning

        persona = dict(capsule.persona_config or {})
        knobs = dict(persona.get("knobs") or {})
        for name, value in seed_data.DEFAULT_KNOBS.items():
            if name not in knobs:
                knobs[name] = value
                dirty_fields.append("persona_config.knobs")
        persona["knobs"] = knobs
        if "memory" not in persona or not persona["memory"]:
            persona["memory"] = {
                "recall_limit": seed_data.DEFAULT_RECALL_LIMIT,
                "similarity_threshold": seed_data.DEFAULT_SIMILARITY_THRESHOLD,
            }
            dirty_fields.append("persona_config.memory")
        capsule.persona_config = persona

        ptr = dict(capsule.memory_pointer or {})
        if not ptr.get("tenant"):
            ptr["tenant"] = ctx.tenant
            dirty_fields.append("memory_pointer")
        if not ptr.get("namespace"):
            ptr["namespace"] = f"agent_{str(capsule.id)[:8]}_chat_history"
            dirty_fields.append("memory_pointer")
        if ptr.get("recall_limit") is None:
            ptr["recall_limit"] = seed_data.DEFAULT_RECALL_LIMIT
            dirty_fields.append("memory_pointer")
        if ptr.get("similarity_threshold") is None:
            ptr["similarity_threshold"] = seed_data.DEFAULT_SIMILARITY_THRESHOLD
            dirty_fields.append("memory_pointer")
        capsule.memory_pointer = ptr

        # Model sovereignty FKs — instances only, never strings.
        if capsule.chat_model_id is None:
            capsule.chat_model = chat_model
            dirty_fields.append("chat_model")
        elif capsule.chat_model_id != chat_model.id:
            # Operator pinned a different model — leave it. Verify still
            # requires *some* bound chat_model.
            skips += 1

        if capsule.image_model_id is None:
            capsule.image_model = vision_model
            dirty_fields.append("image_model")
        elif capsule.image_model_id != vision_model.id:
            skips += 1

        if capsule.status != Capsule.STATUS_ACTIVE:
            capsule.status = Capsule.STATUS_ACTIVE
            dirty_fields.append("status")
        if not capsule.is_active:
            capsule.is_active = True
            dirty_fields.append("is_active")

        if dirty_fields and not ctx.dry_run:
            capsule.save()
            writes += 1
        elif dirty_fields and ctx.dry_run:
            writes += 1
        else:
            skips += 1

    # --- capsule-scoped Model Roles (what /llm/roles?capsule_id= reads) ----
    if capsule is not None and not ctx.dry_run:
        for role in MODEL_ROLES:
            if role in ("chat_role", "vision_role"):
                # Capsule FKs above are the capsule-scope binding for these.
                continue
            writes, skips = _bind_role_setting(
                ctx, str(capsule.id), role, _role_model(role), writes, skips
            )

    # --- Agent bound to the capsule --------------------------------------
    if capsule is not None:
        agent = Agent.objects.filter(tenant=tenant, slug=seed_data.AGENT_SLUG).first()
        if agent is None:
            if not ctx.dry_run:
                agent = Agent.objects.create(
                    tenant=tenant,
                    name=seed_data.AGENT_NAME,
                    slug=seed_data.AGENT_SLUG,
                    description="Bootstrap default agent (chat-ready)",
                    status="active",
                    primary_capsule=capsule,
                )
                agent.capsules.add(capsule)
                writes += 1
            else:
                writes += 1
        else:
            if agent.primary_capsule_id != capsule.id and not ctx.dry_run:
                agent.primary_capsule = capsule
                agent.save(update_fields=["primary_capsule"])
                writes += 1
            else:
                skips += 1
            if not ctx.dry_run and not agent.capsules.filter(id=capsule.id).exists():
                agent.capsules.add(capsule)
        ctx.agent = agent
    ctx.capsule = capsule

    if capsule is not None:
        for field_name, model in (("chat_model", chat_model), ("image_model", vision_model)):
            bound = getattr(capsule, field_name, None) or model
            if not isinstance(bound, LLMModelConfig):
                raise ConfigError(
                    f"Capsule.{field_name} must be an LLMModelConfig instance, never a string"
                )

    return PhaseResult(
        "capsule",
        "ok",
        f"capsule {seed_data.CAPSULE_NAME} complete; "
        f"chat_model FK → {chat_model.name}, image_model FK → {vision_model.name}",
        writes=writes,
        skips=skips,
    )
