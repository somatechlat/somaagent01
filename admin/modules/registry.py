"""Capsule Module registry — built-ins, DB sync, and feature-flag gating (WP D1).

Built-in first-wave modules come from SOMA-A0-PARITY-001 §6.2. Their manifests
are synced into the ``capsule_modules`` table so list/enable/disable operate on
real DB state. ``module.yaml`` files on disk (see :mod:`admin.modules.manifest`)
override/extend the built-in defaults when present.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from admin.modules.manifest import (
    ModuleManifest,
    discover_module_dirs,
    load_default_config,
    load_module_dir,
    parse_manifest,
)

logger = logging.getLogger(__name__)

# Built-in module directory root (convention: admin/modules/<name>/module.yaml).
BUILTIN_MODULES_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class BuiltinModule:
    """Declarative first-wave module (§6.2) before filesystem manifest merge."""

    name: str
    title: str
    version: str
    description: str
    settings_sections: tuple[str, ...]
    always_enabled: bool
    feature_flag: str
    enabled_by_default: bool = False
    permissions: tuple[str, ...] = ()


# §6.2 Built-in Capsule Modules (first wave).
BUILTIN_MODULES: tuple[BuiltinModule, ...] = (
    BuiltinModule(
        name="mod_whatsapp",
        title="WhatsApp Channel",
        version="1.0.0",
        description="WhatsApp bridge Capsule (Channel, QR pairing, group/DM context)",
        settings_sections=("agent", "external"),
        always_enabled=False,
        feature_flag="bridge_whatsapp",
        permissions=("network", "vault:read"),
    ),
    BuiltinModule(
        name="mod_telegram",
        title="Telegram Channel",
        version="1.0.0",
        description="Telegram bridge Capsule (bot token, webhook/poll, draft typing)",
        settings_sections=("agent", "external"),
        always_enabled=False,
        feature_flag="bridge_telegram",
        permissions=("network", "vault:read"),
    ),
    BuiltinModule(
        name="mod_email",
        title="Email Channel",
        version="1.0.0",
        description="Email bridge Capsule (IMAP poll, SMTP send, thread context)",
        settings_sections=("agent", "external"),
        always_enabled=False,
        feature_flag="bridge_email",
        permissions=("network", "vault:read"),
    ),
    BuiltinModule(
        name="mod_mcp",
        title="MCP Client/Server",
        version="1.0.0",
        description="Model Context Protocol client/server capabilities",
        settings_sections=("mcp",),
        always_enabled=False,
        feature_flag="mcp",
    ),
    BuiltinModule(
        name="mod_skills",
        title="Skills",
        version="1.0.0",
        description="Skill packages for Capsules",
        settings_sections=("skills",),
        always_enabled=False,
        feature_flag="skills",
    ),
    BuiltinModule(
        name="mod_knowledge",
        title="Knowledge/RAG",
        version="1.0.0",
        description="Knowledge ingestion and retrieval",
        settings_sections=("agent",),
        always_enabled=False,
        feature_flag="knowledge",
    ),
    BuiltinModule(
        name="mod_memory_dashboard",
        title="Memory Dashboard",
        version="1.0.0",
        description="Memory triad observability dashboard",
        settings_sections=("agent",),
        always_enabled=True,
        feature_flag="",
    ),
    BuiltinModule(
        name="mod_backup",
        title="Backup & Restore",
        version="1.0.0",
        description="Capsule and workspace backup",
        settings_sections=("backup",),
        always_enabled=False,
        feature_flag="backup",
    ),
    BuiltinModule(
        name="mod_voice",
        title="Voice STT/TTS",
        version="1.0.0",
        description="Speech-to-text and text-to-speech",
        settings_sections=("agent", "external"),
        always_enabled=False,
        feature_flag="voice",
    ),
    BuiltinModule(
        name="mod_browser",
        title="Browser Tool",
        version="1.0.0",
        description="Browser automation tool for Capsules",
        settings_sections=("agent",),
        always_enabled=False,
        feature_flag="browser_use",
    ),
    BuiltinModule(
        name="mod_code",
        title="Code Execution",
        version="1.0.0",
        description="Sandboxed code execution capability",
        settings_sections=("developer",),
        always_enabled=True,
        feature_flag="",
    ),
    BuiltinModule(
        name="mod_scheduler",
        title="Scheduler",
        version="1.0.0",
        description="Job scheduling and recurring tasks",
        settings_sections=("developer",),
        always_enabled=False,
        feature_flag="scheduler",
    ),
)


class ModuleError(Exception):
    """Domain error for module registry operations."""


class ModuleNotFound(ModuleError):
    """No Module row with the given name."""


class FeatureDisabledError(ModuleError):
    """Module's feature flag is disabled — enable refused (fail-closed)."""


class AlwaysEnabledError(ModuleError):
    """Attempt to disable an always_enabled module."""


def _builtin_to_manifest(builtin: BuiltinModule) -> ModuleManifest:
    return ModuleManifest(
        name=builtin.name,
        title=builtin.title,
        version=builtin.version,
        description=builtin.description,
        settings_sections=builtin.settings_sections,
        permissions=builtin.permissions,
        always_enabled=builtin.always_enabled,
        feature_flag=builtin.feature_flag,
    )


def _load_disk_manifest(builtin: BuiltinModule) -> Optional[ModuleManifest]:
    """Load admin/modules/<name>/module.yaml when present (overrides built-in)."""

    module_dir = BUILTIN_MODULES_ROOT / builtin.name
    try:
        return load_module_dir(module_dir)
    except FileNotFoundError:
        return None
    except Exception:
        logger.exception("failed to load module.yaml for %s", builtin.name)
        return None


def feature_state(feature_flag: str) -> Optional[bool]:
    """Resolve a FeatureRegistry key → True/False, or None when no flag is set.

    Uses the enterprise FeatureRegistry (services.common.features). Unknown keys
    are treated as disabled (fail-closed) so a typo can never open a bridge.
    """

    if not feature_flag:
        return None
    try:
        from services.common.features import build_default_registry

        registry = build_default_registry()
        descriptor_keys = {d.key for d in registry.describe()}
        if feature_flag not in descriptor_keys:
            logger.warning("unknown feature flag '%s' treated as disabled", feature_flag)
            return False
        return bool(registry.is_enabled(feature_flag))
    except Exception:
        logger.exception("feature flag lookup failed for '%s'", feature_flag)
        return False


def _merge_manifest(builtin: BuiltinModule) -> tuple[ModuleManifest, dict[str, Any], str]:
    """Return (manifest, default_config, source_path) for a built-in module."""

    manifest = _builtin_to_manifest(builtin)
    defaults: dict[str, Any] = {}
    source_path = ""
    module_dir = BUILTIN_MODULES_ROOT / builtin.name
    disk = _load_disk_manifest(builtin)
    if disk is not None:
        manifest = disk
        source_path = str(module_dir)
        try:
            defaults = load_default_config(module_dir)
        except Exception:
            logger.exception("failed to load default config for %s", builtin.name)
    return manifest, defaults, source_path


def sync_builtin_modules() -> int:
    """Upsert built-in module manifests into the Module table. Returns count.

    Disk ``module.yaml`` wins over the in-code built-in defaults. Toggle state
    is preserved across syncs; ``always_enabled`` rows are forced enabled.
    """

    from admin.modules.models import Module

    synced = 0
    for builtin in BUILTIN_MODULES:
        manifest, defaults, source_path = _merge_manifest(builtin)
        defaults = dict(defaults)
        obj, created = Module.objects.get_or_create(
            name=manifest.name,
            defaults={
                "title": manifest.title,
                "version": manifest.version,
                "description": manifest.description,
                "enabled": bool(builtin.enabled_by_default or manifest.always_enabled),
                "always_enabled": manifest.always_enabled,
                "config": defaults,
                "settings_sections": list(manifest.settings_sections),
                "permissions": list(manifest.permissions),
                "feature_flag": manifest.feature_flag,
                "manifest": manifest.to_dict(),
                "source_path": source_path,
            },
        )
        if not created:
            # Refresh contract fields from manifest; never clobber toggle/config.
            obj.title = manifest.title
            obj.version = manifest.version
            obj.description = manifest.description
            obj.always_enabled = manifest.always_enabled
            obj.settings_sections = list(manifest.settings_sections)
            obj.permissions = list(manifest.permissions)
            obj.feature_flag = manifest.feature_flag
            obj.manifest = manifest.to_dict()
            if source_path:
                obj.source_path = source_path
            if obj.always_enabled and not obj.enabled:
                obj.enabled = True
            obj.save()
        synced += 1
    return synced


def ensure_registry() -> None:
    """Best-effort sync on read paths so list endpoints see built-ins."""

    from admin.modules.models import Module

    if Module.objects.count() == 0:
        try:
            sync_builtin_modules()
        except Exception:
            logger.exception("module registry sync failed")


def list_modules(
    *,
    enabled: Optional[bool] = None,
    feature_flag: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return module rows (real DB) with resolved feature state."""

    from admin.modules.models import Module

    ensure_registry()
    qs = Module.objects.all().order_by("name")
    if enabled is not None:
        qs = qs.filter(enabled=enabled)
    if feature_flag:
        qs = qs.filter(feature_flag=feature_flag)

    items: list[dict[str, Any]] = []
    for obj in qs:
        items.append(module_to_dict(obj))
    return items


def module_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a Module row for API responses."""

    flag_state = feature_state(obj.feature_flag)
    return {
        "id": str(obj.id),
        "name": obj.name,
        "title": obj.title,
        "version": obj.version,
        "description": obj.description,
        "enabled": obj.enabled,
        "always_enabled": obj.always_enabled,
        "config": obj.config or {},
        "settings_sections": obj.settings_sections or [],
        "permissions": obj.permissions or [],
        "feature_flag": obj.feature_flag or "",
        "feature_enabled": flag_state,
        "manifest": obj.manifest or {},
        "source_path": obj.source_path or "",
        "tenant_id": str(obj.tenant_id) if obj.tenant_id else None,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
    }


def get_module(name: str) -> dict[str, Any]:
    """Fetch one module by name (raises ModuleNotFound)."""

    from admin.modules.models import Module

    ensure_registry()
    try:
        obj = Module.objects.get(name=name)
    except Module.DoesNotExist as exc:
        raise ModuleNotFound(f"module '{name}' not found") from exc
    return module_to_dict(obj)


def set_module_enabled(name: str, enabled: bool) -> dict[str, Any]:
    """Enable/disable a module with real state persistence.

    Fail-closed rules:
    - unknown module → ModuleNotFound
    - feature_flag set and disabled → FeatureDisabledError (cannot enable)
    - always_enabled=True → AlwaysEnabledError (cannot disable)
    """

    from admin.modules.models import Module

    ensure_registry()
    try:
        obj = Module.objects.get(name=name)
    except Module.DoesNotExist as exc:
        raise ModuleNotFound(f"module '{name}' not found") from exc

    if obj.always_enabled and not enabled:
        raise AlwaysEnabledError(f"module '{name}' is always_enabled and cannot be disabled")

    if enabled:
        flag_state = feature_state(obj.feature_flag)
        if flag_state is False:
            raise FeatureDisabledError(
                f"feature flag '{obj.feature_flag}' is disabled; cannot enable '{name}'"
            )
        obj.enabled = True
    else:
        obj.enabled = False

    obj.save(update_fields=["enabled", "updated_at"])
    logger.info("module %s -> enabled=%s", name, obj.enabled)
    return module_to_dict(obj)


def update_module_config(name: str, config: dict[str, Any]) -> dict[str, Any]:
    """Replace/merge runtime config for a module (real DB state)."""

    from admin.modules.models import Module

    ensure_registry()
    try:
        obj = Module.objects.get(name=name)
    except Module.DoesNotExist as exc:
        raise ModuleNotFound(f"module '{name}' not found") from exc
    merged = dict(obj.config or {})
    merged.update(config or {})
    obj.config = merged
    obj.save(update_fields=["config", "updated_at"])
    return module_to_dict(obj)


def register_disk_modules(extra_roots: Iterable[str | Path] = ()) -> list[str]:
    """Discover and upsert modules from ``module.yaml`` dirs under extra roots.

    Used for the future install path (``usr/modules``). Built-in modules are
    synced via :func:`sync_builtin_modules`.
    """

    from admin.modules.models import Module

    names: list[str] = []
    for root in extra_roots:
        for module_dir in discover_module_dirs(root):
            try:
                manifest = load_module_dir(module_dir)
                defaults = load_default_config(module_dir)
            except Exception:
                logger.exception("skipping invalid module dir %s", module_dir)
                continue
            obj, _ = Module.objects.update_or_create(
                name=manifest.name,
                defaults={
                    "title": manifest.title,
                    "version": manifest.version,
                    "description": manifest.description,
                    "always_enabled": manifest.always_enabled,
                    "config": defaults,
                    "settings_sections": list(manifest.settings_sections),
                    "permissions": list(manifest.permissions),
                    "feature_flag": manifest.feature_flag,
                    "manifest": manifest.to_dict(),
                    "source_path": str(module_dir),
                },
            )
            names.append(obj.name)
    return names


__all__ = [
    "BuiltinModule",
    "BUILTIN_MODULES",
    "ModuleError",
    "ModuleNotFound",
    "FeatureDisabledError",
    "AlwaysEnabledError",
    "feature_state",
    "sync_builtin_modules",
    "ensure_registry",
    "list_modules",
    "get_module",
    "set_module_enabled",
    "update_module_config",
    "module_to_dict",
    "register_disk_modules",
    "parse_manifest",
]
