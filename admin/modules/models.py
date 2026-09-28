"""Capsule Module model — real persisted registry state (WP D1).

A Module row is the database-backed registry entry for a Capsule Module
(WhatsApp/Telegram/Email bridges, MCP, skills, …). Built-in manifests are
synced into this table by :mod:`admin.modules.registry`; enable/disable and
runtime config are real state stored here — never a hardcoded list.
"""

from __future__ import annotations

import uuid

from django.db import models


class Module(models.Model):
    """One Capsule Module install (global or tenant-scoped).

    Field contract (parity doc §6.1 + work package D1):
    - ``name``: stable module id (e.g. ``mod_whatsapp``)
    - ``title`` / ``version``: human label and semver from ``module.yaml``
    - ``enabled``: real toggle state (respecting ``always_enabled``)
    - ``config``: runtime config JSON (defaults from ``module.config.json``)
    - ``settings_sections``: UI sections the module contributes
    - ``always_enabled``: core modules that cannot be disabled
    - ``tenant``: optional tenant binding; NULL = available platform-wide
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Stable module id from module.yaml (e.g. mod_whatsapp)",
    )
    title = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default="1.0.0")
    description = models.TextField(blank=True)

    enabled = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Real toggle state; always_enabled modules are forced on",
    )
    always_enabled = models.BooleanField(
        default=False,
        help_text="Core modules that cannot be disabled through the API",
    )

    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Runtime module.config.json values (Capsule overrides in persona_config)",
    )
    settings_sections = models.JSONField(
        default=list,
        blank=True,
        help_text="UI sections contributed: agent|external|developer|mcp|backup|file-browser|skills",
    )
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="Declared permissions from module.yaml",
    )
    feature_flag = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="FeatureRegistry key required before this module can be enabled",
    )
    manifest = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full parsed module.yaml snapshot",
    )
    source_path = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Filesystem directory of the module (built-in path or install path)",
    )

    tenant = models.ForeignKey(
        "aaas.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="capsule_modules",
        help_text="Optional tenant binding; NULL = platform-wide module",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capsule_modules"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["enabled"]),
            models.Index(fields=["tenant", "name"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        state = "on" if self.enabled else "off"
        return f"Module({self.name} v{self.version}:{state})"
