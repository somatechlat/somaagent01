"""Capsule Import Service.

Simple. Elegant. Complete.

Imports Capsule bundles from backup or transfer, creating new Capsule
records with proper validation and conflict resolution.

IMPORTANT: Imported capsules are always created in DRAFT status and
must be re-certified before activation. This ensures cryptographic
integrity after any transfer or restore operation.

VIBE Compliance:
- Rule 82: Professional comments, zero AI slop
- Rule 84: No mocks - real Django ORM operations
- Rule 216: Django 5+ Backend Sovereignty
- Rule 245: Under 650 lines
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from django.db import transaction

from admin.core.models import (
    AgentSetting,
    Capsule,
    Capability,
    FeatureFlag,
    Prompt,
    UISetting,
)
from admin.llm.models import LLMModelConfig
from services.capsule_export import verify_export_checksum

logger = logging.getLogger(__name__)


# =============================================================================
# IMPORT RESULT CLASSES
# =============================================================================


class ImportResult:
    """Result of a capsule import operation."""

    def __init__(
        self,
        success: bool,
        capsule: Optional[Capsule] = None,
        error: Optional[str] = None,
        warnings: Optional[list] = None,
    ):
        """Initialize import result.

        Args:
            success: Whether import succeeded
            capsule: The imported Capsule (if successful)
            error: Error message (if failed)
            warnings: List of non-fatal warnings
        """
        self.success = success
        self.capsule = capsule
        self.error = error
        self.warnings = warnings or []

    def __repr__(self) -> str:
        """Return string representation."""
        if self.success:
            return f"ImportResult(success=True, capsule={self.capsule})"
        return f"ImportResult(success=False, error={self.error})"


class TenantImportResult:
    """Result of a tenant-wide import operation."""

    def __init__(self):
        """Initialize tenant import result."""
        self.successful_imports: list[ImportResult] = []
        self.failed_imports: list[ImportResult] = []
        self.related_data_imported: bool = False

    @property
    def success_count(self) -> int:
        """Return count of successful imports."""
        return len(self.successful_imports)

    @property
    def failure_count(self) -> int:
        """Return count of failed imports."""
        return len(self.failed_imports)

    @property
    def total_count(self) -> int:
        """Return total import count."""
        return self.success_count + self.failure_count


# =============================================================================
# IMPORT FUNCTIONS
# =============================================================================


def import_capsule(
    export_data: dict,
    target_tenant: Optional[str] = None,
    version_suffix: str = ".imported",
    skip_checksum: bool = False,
    import_related_data: bool = True,
) -> ImportResult:
    """Import a Capsule from an export bundle.

    Creates a new Capsule in DRAFT status. The capsule must be
    re-certified before activation (security requirement).

    Args:
        export_data: Export bundle from export_capsule()
        target_tenant: Override tenant (for cross-tenant transfer)
        version_suffix: Suffix to add to version (avoids conflicts)
        skip_checksum: Skip checksum verification (not recommended)
        import_related_data: Also import capabilities, prompts, etc.

    Returns:
        ImportResult with success status and imported capsule
    """
    warnings: list[str] = []

    # Verify checksum integrity
    if not skip_checksum:
        if not verify_export_checksum(export_data):
            return ImportResult(
                success=False,
                error="Export checksum verification failed. Data may be corrupted.",
            )

    capsule_data = export_data.get("capsule")
    if not capsule_data:
        return ImportResult(success=False, error="No capsule data in export bundle")

    logger.info(
        "Importing Capsule %s:%s from export",
        capsule_data.get("name"),
        capsule_data.get("version"),
    )

    try:
        with transaction.atomic():
            # Determine target tenant
            tenant = target_tenant or capsule_data.get("tenant", "default")

            # Generate new version to avoid conflicts
            new_version = capsule_data.get("version", "1.0.0") + version_suffix

            # Check for existing capsule with same name/version/tenant
            if Capsule.objects.filter(
                name=capsule_data.get("name"), version=new_version, tenant=tenant
            ).exists():
                # Increment version suffix
                new_version = f"{new_version}.{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
                warnings.append(f"Version conflict resolved: using {new_version}")

            # Extract soul and body data
            soul = capsule_data.get("soul", {})
            body = capsule_data.get("body", {})

            # Create new capsule in DRAFT status
            new_capsule = Capsule.objects.create(
                name=capsule_data.get("name"),
                version=new_version,
                tenant=tenant,
                description=capsule_data.get("description", ""),
                status=Capsule.STATUS_DRAFT,  # Always draft - must re-certify
                # Soul
                system_prompt=soul.get("system_prompt", ""),
                personality_traits=soul.get("personality_traits", {}),
                neuromodulator_baseline=soul.get("neuromodulator_baseline", {}),
                # Body
                capabilities_whitelist=body.get("capabilities_whitelist", []),
                resource_limits=body.get("resource_limits", {}),
                schema=body.get("schema", {}),
                config=body.get("config", {}),
                # Governance - cleared for re-certification
                constitution=None,
                constitution_ref={},
                registry_signature=None,
                certified_at=None,
            )

            logger.info(
                "Created imported capsule: %s:%s (id=%s, status=DRAFT)",
                new_capsule.name,
                new_capsule.version,
                new_capsule.id,
            )

            # Import related data if requested
            if import_related_data and export_data.get("related_data"):
                related_warnings = _import_related_data(
                    export_data["related_data"], tenant, str(new_capsule.id)
                )
                warnings.extend(related_warnings)

            return ImportResult(
                success=True,
                capsule=new_capsule,
                warnings=warnings,
            )

    except Exception as e:
        logger.error("Capsule import failed: %s", str(e))
        return ImportResult(success=False, error=str(e), warnings=warnings)


def import_tenant_capsules(
    export_data: dict,
    target_tenant: Optional[str] = None,
    import_related_data: bool = True,
) -> TenantImportResult:
    """Import all capsules from a tenant export bundle.

    Args:
        export_data: Tenant export bundle from export_tenant_capsules()
        target_tenant: Override tenant for all capsules
        import_related_data: Also import related data

    Returns:
        TenantImportResult with all import results
    """
    result = TenantImportResult()

    # Verify checksum
    if not verify_export_checksum(export_data):
        failed = ImportResult(
            success=False, error="Tenant export checksum verification failed"
        )
        result.failed_imports.append(failed)
        return result

    tenant = target_tenant or export_data.get("tenant", "default")
    capsules = export_data.get("capsules", [])

    logger.info("Importing %d capsules for tenant: %s", len(capsules), tenant)

    # Import each capsule
    for capsule_export in capsules:
        import_result = import_capsule(
            capsule_export,
            target_tenant=tenant,
            skip_checksum=True,  # Already verified at tenant level
            import_related_data=False,  # Import once below
        )

        if import_result.success:
            result.successful_imports.append(import_result)
        else:
            result.failed_imports.append(import_result)

    # Import related data once for entire tenant
    if import_related_data and export_data.get("related_data"):
        try:
            _import_tenant_related_data(export_data["related_data"], tenant)
            result.related_data_imported = True
        except Exception as e:
            logger.error("Failed to import tenant related data: %s", e)

    logger.info(
        "Tenant import complete: %d succeeded, %d failed",
        result.success_count,
        result.failure_count,
    )

    return result


# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================


def _import_related_data(
    related_data: dict, tenant: str, agent_id: str
) -> list[str]:
    """Import related data entities for a single capsule.

    Returns list of warning messages.
    """
    warnings: list[str] = []

    # Import capabilities (if they don't exist)
    for cap_data in related_data.get("capabilities", []):
        try:
            Capability.objects.get_or_create(
                name=cap_data.get("name"),
                defaults={
                    "description": cap_data.get("description", ""),
                    "category": cap_data.get("category", "general"),
                    "schema": cap_data.get("schema", {}),
                    "config": cap_data.get("config", {}),
                    "is_enabled": cap_data.get("is_enabled", True),
                },
            )
        except Exception as e:
            warnings.append(f"Failed to import capability {cap_data.get('name')}: {e}")

    # Import agent settings
    for setting_data in related_data.get("agent_settings", []):
        try:
            AgentSetting.objects.update_or_create(
                agent_id=agent_id,  # Use new capsule ID
                key=setting_data.get("key"),
                defaults={
                    "value": setting_data.get("value"),
                    "is_secret": setting_data.get("is_secret", False),
                },
            )
        except Exception as e:
            warnings.append(f"Failed to import agent setting {setting_data.get('key')}: {e}")

    return warnings


def _import_tenant_related_data(related_data: dict, tenant: str) -> None:
    """Import related data at tenant level."""
    # Import prompts
    for prompt_data in related_data.get("prompts", []):
        try:
            Prompt.objects.get_or_create(
                name=prompt_data.get("name"),
                version=prompt_data.get("version", "1.0.0"),
                tenant=tenant,
                defaults={
                    "template": prompt_data.get("template", ""),
                    "variables": prompt_data.get("variables", []),
                    "metadata": prompt_data.get("metadata", {}),
                    "is_active": prompt_data.get("is_active", True),
                },
            )
        except Exception as e:
            logger.warning("Failed to import prompt %s: %s", prompt_data.get("name"), e)

    # Import UI settings
    for setting_data in related_data.get("ui_settings", []):
        try:
            UISetting.objects.update_or_create(
                tenant=tenant,
                user_id=setting_data.get("user_id"),
                key=setting_data.get("key"),
                defaults={"value": setting_data.get("value", {})},
            )
        except Exception as e:
            logger.warning("Failed to import UI setting: %s", e)

    # Import LLM model configs (global, not tenant-specific)
    for model_data in related_data.get("models", []):
        try:
            LLMModelConfig.objects.get_or_create(
                name=model_data.get("name"),
                defaults={
                    "display_name": model_data.get("display_name", ""),
                    "model_type": model_data.get("model_type", "chat"),
                    "provider": model_data.get("provider", "openrouter"),
                    "api_base": model_data.get("api_base", ""),
                    "capabilities": model_data.get("capabilities", []),
                    "priority": model_data.get("priority", 50),
                    "cost_tier": model_data.get("cost_tier", "standard"),
                    "ctx_length": model_data.get("ctx_length", 0),
                    "is_active": model_data.get("is_active", True),
                },
            )
        except Exception as e:
            logger.warning("Failed to import model config %s: %s", model_data.get("name"), e)


__all__ = [
    "import_capsule",
    "import_tenant_capsules",
    "ImportResult",
    "TenantImportResult",
]
