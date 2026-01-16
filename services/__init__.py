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


def __getattr__(name: str):  # noqa: F401
    """Lazy import to avoid Django AppRegistryNotReady errors."""
    # Capsule core operations
    if name == "verify_capsule":
        from services.capsule_core import verify_capsule

        return verify_capsule
    if name == "certify_capsule":
        from services.capsule_core import certify_capsule

        return certify_capsule
    if name == "inject_capsule":
        from services.capsule_core import inject_capsule

        return inject_capsule
    if name == "edit_capsule":
        from services.capsule_core import edit_capsule

        return edit_capsule
    if name == "archive_capsule":
        from services.capsule_core import archive_capsule

        return archive_capsule

    # Export operations
    if name == "export_capsule":
        from services.capsule_export import export_capsule

        return export_capsule
    if name == "export_tenant_capsules":
        from services.capsule_export import export_tenant_capsules

        return export_tenant_capsules
    if name == "verify_export_checksum":
        from services.capsule_export import verify_export_checksum

        return verify_export_checksum

    # Import operations
    if name == "import_capsule":
        from services.capsule_import import import_capsule

        return import_capsule
    if name == "import_tenant_capsules":
        from services.capsule_import import import_tenant_capsules

        return import_tenant_capsules
    if name == "ImportResult":
        from services.capsule_import import ImportResult

        return ImportResult
    if name == "TenantImportResult":
        from services.capsule_import import TenantImportResult

        return TenantImportResult

    # Instance management
    if name == "create_instance":
        from services.capsule_instance import create_instance

        return create_instance
    if name == "get_instance":
        from services.capsule_instance import get_instance

        return get_instance
    if name == "get_instance_by_session":
        from services.capsule_instance import get_instance_by_session

        return get_instance_by_session
    if name == "list_running_instances":
        from services.capsule_instance import list_running_instances

        return list_running_instances
    if name == "list_all_running_instances":
        from services.capsule_instance import list_all_running_instances

        return list_all_running_instances
    if name == "count_running_instances":
        from services.capsule_instance import count_running_instances

        return count_running_instances
    if name == "update_instance_state":
        from services.capsule_instance import update_instance_state

        return update_instance_state
    if name == "complete_instance":
        from services.capsule_instance import complete_instance

        return complete_instance
    if name == "terminate_instance":
        from services.capsule_instance import terminate_instance

        return terminate_instance
    if name == "cleanup_stale_instances":
        from services.capsule_instance import cleanup_stale_instances

        return cleanup_stale_instances

    raise AttributeError(f"module 'services' has no attribute '{name}'")
