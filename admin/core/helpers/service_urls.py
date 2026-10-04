"""Fail-closed resolution of deployment service endpoints.

A service endpoint that is not configured **raises**. There is no guessed
host, no ``getattr(settings, X, "http://localhost…")``, and no silent
substitute. A URL a caller invents is a URL an operator cannot change and a
reviewer cannot see (VIBE Rule 91 / SOMA-STD-CONFIG-001).

Resolution chain (highest wins) — identical to every other tunable:

    Capsule.persona_config["settings"][CATEGORY][UPPER_NAME]
        → AgentSetting ORM (agent_id, UPPER_NAME)
            → Django settings / SettingsModel
                → process environment (12-factor override of Django settings)
                    → schema default (empty for every deployment URL)

``require_service_url`` is the single shared helper. Import it; do not
re-implement it at a call site. Process environment is consulted only for
topology (URLs, hosts, ports, broker lists) and never for secrets — it is
how a worker that has not loaded Django settings still reads the deploy.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from django.core.exceptions import ImproperlyConfigured


def _from_env(setting_name: str) -> Optional[str]:
    """12-factor topology override: UPPER_NAME, then SA01_UPPER_NAME.

    Secrets never resolve here (VIBE Rule 164). This is only a deployment
    endpoint / broker list / host, which the environment is allowed to carry.
    """
    for key in (setting_name, f"SA01_{setting_name}"):
        value = _nonempty(os.environ.get(key))
        if value is not None:
            return value
    return None


def _nonempty(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def require_service_url(
    setting_name: str,
    *,
    capsule: Any = None,
    agent_id: Optional[str] = None,
) -> str:
    """Resolve one deployment URL through the settings chain, or refuse.

    Args:
        setting_name: UPPER Django setting name (the KEY_CATEGORY key),
            e.g. ``"SOMABRAIN_URL"``, ``"LLM_API_URL"``, ``"WHISPER_API_URL"``.
        capsule: optional Capsule whose persona_config may override the value.
        agent_id: optional agent whose AgentSetting rows may override the value.

    Returns:
        The configured URL, stripped.

    Raises:
        ImproperlyConfigured: when no layer configures the endpoint. This is
            the only legal outcome for a missing deployment URL.
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    value = _nonempty(
        resolve_setting(setting_name, capsule=capsule, agent_id=agent_id)
    )
    if value is not None:
        return value

    # SettingsModel stores deployment URLs under snake_case ``service_*``
    # fields. The UPPER Django name is what operators set; the model field is
    # the schema view of that same name.
    from admin.core.helpers.settings import get_settings

    model = get_settings(capsule=capsule, agent_id=agent_id)
    snake = setting_name.lower()
    for attr in (f"service_{snake}", snake):
        value = _nonempty(getattr(model, attr, None))
        if value is not None:
            return value

    value = _from_env(setting_name)
    if value is not None:
        return value

    raise ImproperlyConfigured(
        f"{setting_name} is not configured. Set it through Django settings or "
        f"AgentSetting (service endpoints are administrator-managed). "
        f"See docs/standards/SOMA-STD-CONFIG-001.md."
    )


def require_setting(setting_name: str, *, capsule: Any = None, agent_id: Optional[str] = None) -> Any:
    """Resolve one required tunable through the settings chain, or refuse.

    Same chain as :func:`require_service_url`, for values that are not URLs
    (broker lists, ports, names). Missing means misconfiguration, not default.
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    value = resolve_setting(setting_name, capsule=capsule, agent_id=agent_id)
    if value is not None and str(value).strip():
        return value

    from admin.core.helpers.settings import get_settings

    model = get_settings(capsule=capsule, agent_id=agent_id)
    snake = setting_name.lower()
    for attr in (snake, f"service_{snake}"):
        value = _nonempty(getattr(model, attr, None))
        if value is not None:
            return value

    value = _from_env(setting_name)
    if value is not None:
        return value

    raise ImproperlyConfigured(
        f"{setting_name} is not configured. Set it through Django settings or "
        f"AgentSetting (SOMA-STD-CONFIG-001)."
    )


__all__ = ["require_service_url", "require_setting"]
