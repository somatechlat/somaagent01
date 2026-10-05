"""AgentIQ HTTP surface — Capsule knobs and server-derived settings.

The UI never computes AgentIQ. This router is the only place a browser reads
``Capsule.persona_config.knobs`` or ``DerivedSettings``: writes land on the
Capsule row, and every derived value comes from
``admin.core.agentiq.derivation`` (the same tables the chat pipeline uses).

Resolution for missing knobs is the real settings chain
(Capsule → AgentSetting → InfrastructureConfig → SettingsModel); the API
returns the *effective* knobs derivation used, so a caller never has to guess
whether a level was stored or resolved.
"""

from __future__ import annotations

from typing import Optional

from asgiref.sync import sync_to_async
from ninja import Router, Schema
from ninja.errors import HttpError

from admin.common.auth import AuthBearer
from admin.core.agentiq.derivation import derive_all_settings, resolve_knobs
from admin.core.agentiq.settings import DerivedSettings
from admin.core.models.core import Capsule
from services.common.authorization import authorize

router = Router(tags=["AgentIQ"])


class KnobsIn(Schema):
    """The four control knobs. Absent fields are left unchanged."""

    intelligence_level: Optional[int] = None
    autonomy_level: Optional[int] = None
    resource_budget: Optional[float] = None
    response_style: Optional[str] = None


class AgentIQOut(Schema):
    """Effective knobs plus the derived settings the server computed."""

    capsule_id: str
    knobs: dict
    derived: dict
    response_styles: list[str]
    lanes: dict


def _derived_to_dict(d: DerivedSettings) -> dict:
    return {
        "response_style": d.response_style,
        "temperature": d.temperature,
        "max_tokens": d.max_tokens,
        "recall_limit": d.recall_limit,
        "model_tier": d.model_tier.value,
        "brain_query_enabled": d.brain_query_enabled,
        "require_hitl": d.require_hitl,
        "tool_approval": d.tool_approval.value,
        "egress_allowed": d.egress_allowed.value,
        "token_limit": d.token_limit,
    }


def _effective_knobs(capsule: Capsule, body: dict | None = None) -> dict:
    """Knobs as derivation actually used them (stored or chain-resolved)."""
    return resolve_knobs(capsule, body=body)


def _load_capsule(capsule_id: str) -> Capsule:
    try:
        return Capsule.objects.get(id=capsule_id)
    except Capsule.DoesNotExist:
        raise HttpError(404, f"Capsule {capsule_id} not found")


def _validate_knobs(knobs: dict) -> None:
    """Bounds match DerivedSettings / the derivation tables. Refuse, never clamp."""
    intel = knobs.get("intelligence_level")
    if intel is not None and not (1 <= int(intel) <= 10):
        raise HttpError(422, "intelligence_level must be 1-10")
    auto = knobs.get("autonomy_level")
    if auto is not None and not (1 <= int(auto) <= 10):
        raise HttpError(422, "autonomy_level must be 1-10")
    budget = knobs.get("resource_budget")
    if budget is not None and float(budget) < 0:
        raise HttpError(422, "resource_budget must be >= 0")
    style = knobs.get("response_style")
    if style is not None:
        from admin.core.agentiq.tables import STYLE_TABLE

        if str(style).strip().lower() not in STYLE_TABLE:
            allowed = ", ".join(sorted(STYLE_TABLE))
            raise HttpError(422, f"response_style must be one of: {allowed}")


async def _read(capsule: Capsule) -> AgentIQOut:
    """Assemble the AgentIQ view. Lanes come from the same allocator the
    chat context builder uses — never a browser-side percentage.

    ``capsule.body`` hits the ORM (``capabilities``). It is fetched once on a
    thread and handed to every resolver, so nothing on this async path calls
    the database synchronously (R-02).
    """
    from admin.core.agentiq.tables import STYLE_TABLE
    from admin.core.context.lanes import get_lane_allocation

    body = await capsule.async_body()
    derived = derive_all_settings(capsule, body=body)
    lanes = await get_lane_allocation(capsule, body=body)
    return AgentIQOut(
        capsule_id=str(capsule.id),
        knobs=_effective_knobs(capsule, body=body),
        derived=_derived_to_dict(derived),
        response_styles=sorted(STYLE_TABLE),
        lanes=lanes.to_dict(),
    )


@router.get(
    "/{capsule_id}",
    response=AgentIQOut,
    auth=AuthBearer(),
    summary="Read AgentIQ knobs and server-derived settings",
)
async def get_agentiq(request, capsule_id: str) -> AgentIQOut:
    await authorize(request, action="agent:read", resource="agents")
    capsule = await sync_to_async(_load_capsule)(capsule_id)
    return await _read(capsule)


@router.put(
    "/{capsule_id}",
    response=AgentIQOut,
    auth=AuthBearer(),
    summary="Update Capsule AgentIQ knobs (derived values recomputed on the server)",
)
async def put_agentiq(request, capsule_id: str, body: KnobsIn) -> AgentIQOut:
    await authorize(request, action="agent:configure_personality", resource="agents")
    capsule = await sync_to_async(_load_capsule)(capsule_id)

    patch = {
        k: v
        for k, v in {
            "intelligence_level": body.intelligence_level,
            "autonomy_level": body.autonomy_level,
            "resource_budget": body.resource_budget,
            "response_style": (
                body.response_style.strip().lower()
                if body.response_style is not None
                else None
            ),
        }.items()
        if v is not None
    }
    if not patch:
        raise HttpError(422, "No knobs supplied")

    _validate_knobs(patch)

    def _persist() -> Capsule:
        persona = dict(capsule.persona_config or {})
        knobs = dict(persona.get("knobs") or {})
        knobs.update(patch)
        persona["knobs"] = knobs
        capsule.persona_config = persona
        capsule.save(update_fields=["persona_config", "updated_at"])
        return capsule

    capsule = await sync_to_async(_persist)()
    return await _read(capsule)
