"""Capsule Modules API — real registry-backed module host (WP D1).

Endpoints under ``/api/v2/modules``:
- ``GET  /``                 list modules (real DB registry, feature-state aware)
- ``GET  /hooks``            orchestrator hook registry introspection
- ``GET  /{name}``           one module
- ``POST /{name}/enable``    enable (fail-closed on disabled feature flag)
- ``POST /{name}/disable``   disable (refused for always_enabled)
- ``GET  /{name}/config``    runtime config
- ``PATCH /{name}/config``   update runtime config
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from admin.common.auth import AuthBearer
from admin.modules import hooks as hooks_module, registry as module_registry
from services.common.authorization import authorize_sync

logger = logging.getLogger(__name__)
router = Router(tags=["modules"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ModuleOut(Schema):
    """Capsule Module record."""

    id: str
    name: str
    title: str
    version: str
    description: str
    enabled: bool
    always_enabled: bool
    config: dict
    settings_sections: list
    permissions: list
    feature_flag: str
    feature_enabled: Optional[bool] = None
    manifest: dict
    source_path: str
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ModuleListOut(Schema):
    """Module list envelope."""

    modules: list[ModuleOut]
    total: int


class ConfigUpdate(Schema):
    """Runtime config patch body."""

    config: dict


# =============================================================================
# HELPERS
# =============================================================================


def _to_http_error(exc: Exception) -> HttpError:
    """Map module registry domain errors to HTTP."""

    if isinstance(exc, module_registry.ModuleNotFound):
        return HttpError(404, str(exc))
    if isinstance(exc, module_registry.FeatureDisabledError):
        return HttpError(409, str(exc))
    if isinstance(exc, module_registry.AlwaysEnabledError):
        return HttpError(409, str(exc))
    if isinstance(exc, module_registry.ModuleError):
        return HttpError(400, str(exc))
    logger.exception("unexpected module registry error")
    return HttpError(500, "module registry error")


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("", response=ModuleListOut, summary="List Capsule Modules", auth=AuthBearer())
def list_modules(
    request,
    enabled: Optional[bool] = None,
    feature_flag: Optional[str] = None,
) -> dict:
    """List Capsule Modules from the real DB registry (not a hardcoded list)."""
    authorize_sync(request, action="system:view", resource="modules")

    try:
        items = module_registry.list_modules(enabled=enabled, feature_flag=feature_flag)
    except Exception as exc:
        raise _to_http_error(exc) from exc
    return {"modules": items, "total": len(items)}


@router.get("/hooks", summary="List orchestrator hook registrations", auth=AuthBearer())
def list_hooks(request) -> dict:
    """List hook points and the handlers modules have registered."""
    authorize_sync(request, action="system:view", resource="modules")

    return {
        "hooks": {
            "known": list(hooks_module.KNOWN_HOOKS),
            "reserved": list(hooks_module.RESERVED_HOOKS),
            "registrations": hooks_module.list_registrations(),
        },
        "total": len(hooks_module.KNOWN_HOOKS),
    }


@router.get("/{name}", response=ModuleOut, summary="Get Capsule Module", auth=AuthBearer())
def get_module(request, name: str) -> dict:
    """Get one Capsule Module by name."""
    authorize_sync(request, action="system:view", resource="modules")

    try:
        return module_registry.get_module(name)
    except Exception as exc:
        raise _to_http_error(exc) from exc


@router.post("/{name}/enable", response=ModuleOut, summary="Enable module", auth=AuthBearer())
def enable_module(request, name: str) -> dict:
    """Enable a module. Fail-closed when its feature flag is disabled."""
    authorize_sync(request, action="system:configure", resource="modules")

    try:
        return module_registry.set_module_enabled(name, True)
    except Exception as exc:
        raise _to_http_error(exc) from exc


@router.post("/{name}/disable", response=ModuleOut, summary="Disable module", auth=AuthBearer())
def disable_module(request, name: str) -> dict:
    """Disable a module. Refused for always_enabled modules."""
    authorize_sync(request, action="system:configure", resource="modules")

    try:
        return module_registry.set_module_enabled(name, False)
    except Exception as exc:
        raise _to_http_error(exc) from exc


@router.get("/{name}/config", summary="Get module config", auth=AuthBearer())
def get_module_config(request, name: str) -> dict[str, Any]:
    """Get runtime config for a module."""
    authorize_sync(request, action="system:view", resource="modules")

    try:
        module = module_registry.get_module(name)
    except Exception as exc:
        raise _to_http_error(exc) from exc
    return {"name": module["name"], "config": module["config"]}


@router.patch("/{name}/config", summary="Update module config", auth=AuthBearer())
def update_module_config(request, name: str, payload: ConfigUpdate) -> dict[str, Any]:
    """Merge runtime config values for a module (real DB state)."""
    authorize_sync(request, action="system:configure", resource="modules")

    try:
        module = module_registry.update_module_config(name, payload.config)
    except Exception as exc:
        raise _to_http_error(exc) from exc
    return {"name": module["name"], "config": module["config"]}
