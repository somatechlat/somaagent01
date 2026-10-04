"""Fail-closed resolution of deployment service endpoints.

A service endpoint that is not configured **raises**. There is no guessed
host, no ``getattr(settings, X, "http://localhost…")``, and no silent
substitute. A URL a caller invents is a URL an operator cannot change and a
reviewer cannot see (VIBE Rule 91 / SOMA-STD-CONFIG-001).

Resolution chain (highest wins) — identical to every other tunable:

    Capsule.persona_config["settings"][CATEGORY][UPPER_NAME]
        → AgentSetting ORM (agent_id, UPPER_NAME)
            → InfrastructureConfig ORM   <- the OPERATOR'S layer
                → SettingsModel / Django settings
                    → schema default (empty for every deployment URL)

``InfrastructureConfig`` is where an administrator edits a service
endpoint from the UI. A URL is configuration an operator owns, not a
contract with a container: pointing the agent at another SomaBrain must
not require an ``.env`` edit or a container recreate.

**Process environment is NOT in this chain.** It carries bootstrap only -
how to reach the settings themselves (``SA01_DEPLOYMENT_MODE``,
``VAULT_ADDR``/``VAULT_TOKEN_FILE``, the database host/port). Once those
exist the database is the authority. A value sourced from ENV is a value
an operator cannot edit and an auditor cannot see.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from django.core.exceptions import ImproperlyConfigured



def _nonempty(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _from_infraconfig(setting_name: str) -> Optional[str]:
    """The operator's layer: InfrastructureConfig, edited from the admin UI.

    Rows are (service, key, value). A service endpoint is stored as a plain
    key on its service row. A secret-shaped key is never a value here - it may
    hold a Vault path and nothing else (the model enforces that on save).
    """
    try:
        from asgiref.sync import sync_to_async

        from admin.core.infrastructure.models import InfrastructureConfig

        def _lookup() -> Optional[str]:
            rows = InfrastructureConfig.objects.filter(key=setting_name)
            for row in rows:
                value = _nonempty(getattr(row, "value", None))
                if value is not None:
                    return value
            return None

        # This resolver is called from sync code (settings import, management
        # commands) and from async code (the request path). sync_to_async is
        # only correct in the second case; in the first it returns a coroutine
        # nobody awaits and the value is silently lost. Detect the loop.
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No event loop: plain synchronous ORM is legal here.
            return _lookup()
        return asyncio.get_event_loop().run_until_complete(sync_to_async(_lookup)())
    except Exception:
        # The ORM is unavailable (a worker without Django, a migration in
        # flight). That is not permission to guess a host - fall through to the
        # next layer and ultimately refuse.
        return None


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

    # The operator's layer. An administrator edits a service endpoint here
    # from the UI; it outranks the schema default.
    value = _from_infraconfig(setting_name)
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

    raise ImproperlyConfigured(
        f"{setting_name} is not configured. Set it through Django settings or "
        f"AgentSetting (SOMA-STD-CONFIG-001)."
    )


__all__ = ["require_service_url", "require_setting"]
