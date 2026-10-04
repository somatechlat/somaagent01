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

import asyncio
from typing import Any, Dict, Optional

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError


# The operator's layer, read once and held. InfrastructureConfig rows are
# deployment topology: they change when an administrator edits them, not on
# every request. Holding them means the request path does a dict read instead
# of an ORM query — which is the latency answer at millions of transactions,
# and it is also what makes this resolver correct from both sync and async
# code.
#
# The previous implementation called sync_to_async and then
# loop.run_until_complete from inside the resolver. On the request path a loop
# is already running, so run_until_complete raised "This event loop is already
# running", the bare except swallowed it, and the layer silently returned None —
# the operator layer existed but never applied. It also created an un-awaited
# coroutine. There is no ORM call on the read path now, so neither can happen.
_INFRA_CACHE: Dict[str, str] = {}
_INFRA_CACHE_LOADED = False
_INFRA_CACHE_BOUND = 2048


def _nonempty(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def invalidate_infraconfig_cache() -> None:
    """Drop the held operator layer so the next read sees a fresh edit.

    Wired to InfrastructureConfig save/delete. An administrator who points the
    agent at another SomaBrain must not wait for a process restart.
    """
    global _INFRA_CACHE_LOADED
    _INFRA_CACHE.clear()
    _INFRA_CACHE_LOADED = False


def _load_infraconfig() -> None:
    """Fill the cache from InfrastructureConfig. Sync ORM only.

    Raises when Django's ORM is unavailable (a worker without Django, a
    migration in flight) rather than guessing a host. The caller decides
    whether that is fatal.
    """
    global _INFRA_CACHE_LOADED
    from admin.core.infrastructure.models import InfrastructureConfig

    rows = InfrastructureConfig.objects.filter(key__isnull=False).values_list(
        "key", "value"
    )
    loaded: Dict[str, str] = {}
    for key, value in rows:
        if len(loaded) >= _INFRA_CACHE_BOUND:
            break
        text = _nonempty(value)
        if text is not None:
            loaded[str(key)] = text
    _INFRA_CACHE.clear()
    _INFRA_CACHE.update(loaded)
    _INFRA_CACHE_LOADED = True


def warm_infraconfig_cache() -> bool:
    """Populate the operator layer (boot, management commands, first request).

    Returns True when the cache is populated. Never raises: a deployment that
    cannot reach the ORM yet still boots, and the first request that needs a
    service URL refuses with a named setting rather than a guessed host.

    When an event loop is already running (ASGI import under uvicorn), the ORM
    load is handed to a worker thread so Django's async safety is satisfied and
    the operator layer is actually warm before the first request.
    """
    global _INFRA_CACHE_LOADED
    if _INFRA_CACHE_LOADED:
        return True

    def _run() -> bool:
        try:
            _load_infraconfig()
        except (
            RuntimeError,          # apps not ready
            ImportError,           # app not installed in a bare worker
            ImproperlyConfigured,  # settings not loaded
        ):
            return False
        except DatabaseError:
            return False
        return True

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run()

    # A loop is running: sync ORM here would raise SynchronousOnlyOperation.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        try:
            return pool.submit(_run).result()
        except Exception:
            return False


def _from_infraconfig(setting_name: str) -> Optional[str]:
    """The operator's layer: InfrastructureConfig, edited from the admin UI.

    Rows are (service, key, value). A service endpoint is stored as a plain
    key on its service row. A secret-shaped key is never a value here - it may
    hold a Vault path and nothing else (the model enforces that on save).
    """
    if not _INFRA_CACHE_LOADED:
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No event loop: synchronous ORM is legal here.
            if not warm_infraconfig_cache():
                return None
        else:
            # On the request path the cache is already warm (warmed at boot and
            # invalidated on write). Doing ORM work here would mean blocking the
            # event loop or spawning a coroutine nobody awaits. Refuse instead:
            # a cold cache on a live request is a deployment fault, and the
            # next layer or the final raise says so honestly.
            return None
    return _INFRA_CACHE.get(setting_name)


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

    # The operator's layer is not URL-specific. A tunable an administrator
    # sets on an InfrastructureConfig row outranks the schema default, whether
    # or not its value looks like an endpoint.
    value = _from_infraconfig(setting_name)
    if value is not None:
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


__all__ = [
    "invalidate_infraconfig_cache",
    "require_service_url",
    "require_setting",
    "warm_infraconfig_cache",
]
