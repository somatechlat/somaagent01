"""Service implementations for SomaAgent01.

Capsule Management:
- capsule_core: Core operations (verify, certify, inject, edit)
- capsule_export: Export capsules for backup/transfer
- capsule_import: Import capsules from backup
- capsule_instance: Multi-instance lifecycle management

NOTE: Imports are lazy to avoid Django AppRegistryNotReady errors.
Use: from services.capsule_export import export_capsule
"""

# Lazy imports - do NOT import Django models at module level
# This avoids AppRegistryNotReady errors during Django bootstrap

__all__ = [
    # Core operations (from capsule_core)
    "verify_capsule",
    "certify_capsule",
    "inject_capsule",
    "edit_capsule",
    "archive_capsule",
    # Export (from capsule_export)
    "export_capsule",
    "export_tenant_capsules",
    "verify_export_checksum",
    # Import (from capsule_import)
    "import_capsule",
    "import_tenant_capsules",
    "ImportResult",
    "TenantImportResult",
    # Instance management (from capsule_instance)
    "create_instance",
    "get_instance",
    "get_instance_by_session",
    "list_running_instances",
    "list_all_running_instances",
    "count_running_instances",
    "update_instance_state",
    "complete_instance",
    "terminate_instance",
    "cleanup_stale_instances",
]


def __getattr__(name: str):
    """Lazy import to avoid Django AppRegistryNotReady errors."""
    if name in (
        "verify_capsule",
        "certify_capsule",
        "inject_capsule",
        "edit_capsule",
        "archive_capsule",
    ):
        from services.capsule_core import (
            archive_capsule,
            certify_capsule,
            edit_capsule,
            inject_capsule,
            verify_capsule,
        )

        return locals()[name]

    if name in ("export_capsule", "export_tenant_capsules", "verify_export_checksum"):
        from services.capsule_export import (
            export_capsule,
            export_tenant_capsules,
            verify_export_checksum,
        )

        return locals()[name]

    if name in ("import_capsule", "import_tenant_capsules", "ImportResult", "TenantImportResult"):
        from services.capsule_import import (
            ImportResult,
            TenantImportResult,
            import_capsule,
            import_tenant_capsules,
        )

        return locals()[name]

    if name in (
        "create_instance",
        "get_instance",
        "get_instance_by_session",
        "list_running_instances",
        "list_all_running_instances",
        "count_running_instances",
        "update_instance_state",
        "complete_instance",
        "terminate_instance",
        "cleanup_stale_instances",
    ):
        from services.capsule_instance import (
            cleanup_stale_instances,
            complete_instance,
            count_running_instances,
            create_instance,
            get_instance,
            get_instance_by_session,
            list_all_running_instances,
            list_running_instances,
            terminate_instance,
            update_instance_state,
        )

        return locals()[name]

    raise AttributeError(f"module 'services' has no attribute '{name}'")
