"""Plugins API — legacy surface delegated to the Capsule Module host (WP D1).

The real module host lives in ``admin.modules`` and is served under
``/api/v2/modules``. These endpoints are kept as a compatibility layer over
the same DB-backed registry so clients hitting ``/api/v2/plugins`` observe the
same real state (no hardcoded lists). Install/marketplace remain 501 — there is
no remote plugin registry.
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.modules import hooks as hooks_module, registry as module_registry

router = Router(tags=["plugins"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Plugin(BaseModel):
    """Plugin definition (mapped from Capsule Module rows)."""

    plugin_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: str
    category: str  # tools, memory, output, input
    status: str  # installed, enabled, disabled, error
    permissions: list[str]
    installed_at: str


class PluginManifest(BaseModel):
    """Plugin manifest for installation."""

    name: str
    version: str
    description: str
    author: str
    category: str
    entry_point: str
    permissions: list[str]
    dependencies: Optional[list[str]] = None


class PluginHook(BaseModel):
    """Plugin hook point."""

    hook_id: str
    name: str
    description: str
    parameters: dict


def _module_to_plugin(module: dict) -> dict:
    """Map a Module dict onto the legacy Plugin schema."""

    status = "enabled" if module.get("enabled") else "disabled"
    return {
        "plugin_id": module["name"],
        "name": module["title"],
        "version": module["version"],
        "description": module.get("description") or None,
        "author": "soma",
        "category": "tools",
        "status": status,
        "permissions": module.get("permissions") or [],
        "installed_at": module.get("created_at") or "",
    }


# =============================================================================
# ENDPOINTS - Plugin Management
# =============================================================================


@router.get(
    "",
    summary="List plugins",
    auth=AuthBearer(),
)
async def list_plugins(
    request,
    status: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """List installed plugins (delegates to Capsule Module registry)."""

    try:
        modules = module_registry.list_modules()
    except Exception as exc:
        logger.exception("plugin list failed")
        raise HttpError(500, f"plugin registry error: {exc}") from exc

    items = []
    for module in modules:
        plugin = _module_to_plugin(module)
        if status and plugin["status"] != status:
            continue
        items.append(plugin)
    return {"plugins": items, "total": len(items)}


@router.post(
    "/install",
    summary="Install plugin",
    auth=AuthBearer(),
)
async def install_plugin(
    request,
    source: str,  # URL or registry name
) -> dict:
    """Install a plugin from source.

    Security Auditor: Validate and sandbox.
    """
    raise HttpError(501, "Plugin install is not implemented: no plugin registry host.")


@router.get(
    "/{plugin_id}",
    response=Plugin,
    summary="Get plugin",
    auth=AuthBearer(),
)
async def get_plugin(request, plugin_id: str) -> Plugin:
    """Get plugin details."""
    try:
        module = module_registry.get_module(plugin_id)
    except module_registry.ModuleNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    return Plugin(**_module_to_plugin(module))


@router.post(
    "/{plugin_id}/enable",
    summary="Enable plugin",
    auth=AuthBearer(),
)
async def enable_plugin(request, plugin_id: str) -> dict:
    """Enable a plugin (real module registry state)."""

    try:
        module = module_registry.set_module_enabled(plugin_id, True)
    except module_registry.FeatureDisabledError as exc:
        raise HttpError(409, str(exc)) from exc
    except module_registry.AlwaysEnabledError as exc:
        raise HttpError(409, str(exc)) from exc
    except module_registry.ModuleNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    return {"plugin_id": plugin_id, "enabled": module["enabled"]}


@router.post(
    "/{plugin_id}/disable",
    summary="Disable plugin",
    auth=AuthBearer(),
)
async def disable_plugin(request, plugin_id: str) -> dict:
    """Disable a plugin (real module registry state)."""

    try:
        module = module_registry.set_module_enabled(plugin_id, False)
    except module_registry.AlwaysEnabledError as exc:
        raise HttpError(409, str(exc)) from exc
    except module_registry.ModuleNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    return {"plugin_id": plugin_id, "enabled": module["enabled"]}


@router.delete(
    "/{plugin_id}",
    summary="Uninstall plugin",
    auth=AuthBearer(),
)
async def uninstall_plugin(request, plugin_id: str) -> dict:
    """Uninstall a plugin.

    Security Auditor: Clean removal, revoke permissions.
    """
    raise HttpError(501, "Plugin uninstall is not implemented: no plugin registry host.")


# =============================================================================
# ENDPOINTS - Plugin Configuration
# =============================================================================


@router.get(
    "/{plugin_id}/config",
    summary="Get plugin config",
    auth=AuthBearer(),
)
async def get_plugin_config(request, plugin_id: str) -> dict:
    """Get plugin configuration (from the Module registry)."""

    try:
        module = module_registry.get_module(plugin_id)
    except module_registry.ModuleNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    return {"name": module["name"], "config": module["config"]}


@router.patch(
    "/{plugin_id}/config",
    summary="Update plugin config",
    auth=AuthBearer(),
)
async def update_plugin_config(
    request,
    plugin_id: str,
    config: dict,
) -> dict:
    """Update plugin configuration (from the Module registry)."""

    try:
        module = module_registry.update_module_config(plugin_id, config)
    except module_registry.ModuleNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    return {"name": module["name"], "config": module["config"]}


# =============================================================================
# ENDPOINTS - Hooks
# =============================================================================


@router.get(
    "/hooks",
    summary="List available hooks",
    auth=AuthBearer(),
)
async def list_hooks(request) -> dict:
    """List available plugin hooks (orchestrator hook registry)."""

    return {
        "hooks": {
            "known": list(hooks_module.KNOWN_HOOKS),
            "reserved": list(hooks_module.RESERVED_HOOKS),
            "registrations": hooks_module.list_registrations(),
        },
        "total": len(hooks_module.KNOWN_HOOKS),
    }


# =============================================================================
# ENDPOINTS - Marketplace
# =============================================================================


@router.get(
    "/marketplace",
    summary="Browse marketplace",
)
async def browse_marketplace(
    request,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """Browse plugin marketplace.

    PM: Discover new plugins.
    """
    raise HttpError(501, "Plugin marketplace is not implemented: no real registry.")
