"""Capsule Module manifest (``module.yaml``) loader.

Loader convention (Agent Zero ``plugin.yaml`` → Soma ``module.yaml``)
====================================================================

A Capsule Module lives in a directory under ``admin/modules/<name>/`` (built-in)
or under the install path (future: ``usr/modules/<name>/``) and is discovered
by its manifest file ``module.yaml``::

    admin/modules/
      mod_whatsapp/
        module.yaml          # required manifest (this module's contract)
        module.config.json   # optional default runtime config (JSON)
        services/            # optional helpers (importable Python package)
        hooks.py             # optional: registers orchestrator hooks on import
        api.py               # optional: Ninja router mounted at /api/v2/modules/<name>/
        prompts/             # optional: prompt fragments merged into Capsule system_prompt

``module.yaml`` schema (parity with A0 ``plugin.yaml``, Annex D.1)::

    name: mod_whatsapp                 # unique module id (stable)
    title: WhatsApp Channel            # human label
    description: ...                   # optional
    version: 1.0.0                     # semver string
    settings_sections: [agent, external]  # UI sections: agent|external|developer|
                                         # mcp|backup|file-browser|skills
    permissions: [network, vault:read]    # declared capability permissions
    always_enabled: false              # if true, cannot be disabled via API
    feature_flag: bridge_whatsapp      # optional FeatureRegistry key that must be
                                       # enabled before this module can be enabled
    config_schema: {}                  # optional JSON schema for module.config.json

Toggle state and runtime config are stored on the ``Module`` row in the database
(``enabled``, ``config``) — not in the filesystem — so enable/disable is real
state and survives restarts. Capsule-level overrides live in
``Capsule.persona_config.modules.<name>``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Sections accepted in ``settings_sections`` (Annex D.1).
VALID_SETTINGS_SECTIONS = frozenset(
    {"agent", "external", "developer", "mcp", "backup", "file-browser", "skills"}
)

MANIFEST_FILENAME = "module.yaml"
CONFIG_DEFAULTS_FILENAME = "module.config.json"


class ManifestError(ValueError):
    """Raised when a ``module.yaml`` is missing required fields or malformed."""


@dataclass(frozen=True)
class ModuleManifest:
    """Parsed ``module.yaml`` contract (immutable source of truth for a module)."""

    name: str
    title: str
    version: str
    description: str = ""
    settings_sections: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    always_enabled: bool = False
    feature_flag: str = ""
    config_schema: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the Module model ``manifest`` JSON column."""

        return {
            "name": self.name,
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "settings_sections": list(self.settings_sections),
            "permissions": list(self.permissions),
            "always_enabled": self.always_enabled,
            "feature_flag": self.feature_flag,
            "config_schema": self.config_schema,
        }


def parse_manifest(data: dict[str, Any]) -> ModuleManifest:
    """Validate raw manifest data into a :class:`ModuleManifest`."""

    if not isinstance(data, dict):
        raise ManifestError("module.yaml must be a mapping")
    name = str(data.get("name") or "").strip()
    if not name:
        raise ManifestError("module.yaml requires a non-empty 'name'")
    title = str(data.get("title") or name).strip()
    version = str(data.get("version") or "0.0.0").strip()

    sections_raw = data.get("settings_sections") or []
    if not isinstance(sections_raw, list):
        raise ManifestError("settings_sections must be a list")
    sections = tuple(str(s) for s in sections_raw)
    unknown = set(sections) - VALID_SETTINGS_SECTIONS
    if unknown:
        raise ManifestError(f"unknown settings_sections: {sorted(unknown)}")

    permissions_raw = data.get("permissions") or []
    if not isinstance(permissions_raw, list):
        raise ManifestError("permissions must be a list")

    feature_flag = str(data.get("feature_flag") or "").strip()
    always_enabled = bool(data.get("always_enabled", False))
    config_schema = data.get("config_schema") or {}
    if not isinstance(config_schema, dict):
        raise ManifestError("config_schema must be a mapping")

    return ModuleManifest(
        name=name,
        title=title,
        version=version,
        description=str(data.get("description") or ""),
        settings_sections=sections,
        permissions=tuple(str(p) for p in permissions_raw),
        always_enabled=always_enabled,
        feature_flag=feature_flag,
        config_schema=config_schema,
        raw=dict(data),
    )


def load_module_yaml(path: str | Path) -> ModuleManifest:
    """Load and validate a single ``module.yaml`` file."""

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ManifestError(f"module.yaml not found: {manifest_path}")
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML in {manifest_path}: {exc}") from exc
    return parse_manifest(data)


def load_module_dir(module_dir: str | Path) -> ModuleManifest:
    """Load the manifest (and default config) for a module directory."""

    directory = Path(module_dir)
    return load_module_yaml(directory / MANIFEST_FILENAME)


def load_default_config(module_dir: str | Path) -> dict[str, Any]:
    """Load optional ``module.config.json`` defaults from a module directory."""

    config_path = Path(module_dir) / CONFIG_DEFAULTS_FILENAME
    if not config_path.is_file():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ManifestError(f"invalid {CONFIG_DEFAULTS_FILENAME} in {module_dir}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{CONFIG_DEFAULTS_FILENAME} must be a JSON object")
    return data


def discover_module_dirs(root: str | Path) -> list[Path]:
    """Return immediate subdirectories of ``root`` that contain ``module.yaml``."""

    base = Path(root)
    if not base.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(base.iterdir()):
        if child.is_dir() and (child / MANIFEST_FILENAME).is_file():
            found.append(child)
    return found
