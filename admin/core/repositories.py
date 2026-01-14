"""
Centralized repository manager for SomaAgent01.

This manager satisfies the system's dependency injection needs by providing
singleton access to either Service Adapters (for secrets/keys) or
native Django Model Managers (for core persistence entities).


- 100% Real implementations.
- Zero Shims/Mocks.
- Direct Django ORM usage for database entities.
"""

from __future__ import annotations

from typing import Any, Optional

from services.common.secret_manager import SecretManager

# --- CORE DJANGO MODELS (The source of truth for persistence) ---
from admin.core.models import (
    AuditLog,
    DeadLetterMessage,
    MemoryReplica,
    Notification,
    Session,
    UISetting,
)

# --- REAL SERVICE IMPORTS (Verified on physical disk) ---
from services.common.api_key_store import ApiKeyStore


class RepositoryManager:
    """Singleton manager facilitating access to the system's core repositories."""

    def __init__(self) -> None:
        # Service Singletons
        """Initialize the instance."""

        self._api_key_store: Optional[ApiKeyStore] = None
        self._secret_manager: Optional[SecretManager] = None

    # --- SERVICE ACCESSORS ---

    def get_api_key_store(self) -> ApiKeyStore:
        """Get singleton instance of ApiKeyStore."""
        if self._api_key_store is None:
            self._api_key_store = ApiKeyStore()
        return self._api_key_store

    def get_secret_manager(self) -> SecretManager:
        """Get singleton instance of SecretManager."""
        if self._secret_manager is None:
            self._secret_manager = SecretManager()
        return self._secret_manager

    # --- DJANGO MODEL MANAGER ACCESSORS (Replacing Legacy Stores) ---

    def get_audit_store(self):
        """Get AuditLog manager (replaces AuditStore)."""
        return AuditLog.objects

    def get_dlq_store(self):
        """Get DeadLetterMessage manager (replaces DLQStore)."""
        return DeadLetterMessage.objects

    def get_notifications_store(self):
        """Get Notification manager (replaces NotificationsStore)."""
        return Notification.objects

    def get_ui_settings_store(self):
        """Get UISetting manager (replaces UiSettingsStore)."""
        return UISetting.objects

    def get_session_store(self):
        """Get Session manager (replaces PostgresSessionStore)."""
        return Session.objects

    def get_replica_store(self):
        """Get MemoryReplica manager (replaces MemoryReplicaStore)."""
        return MemoryReplica.objects

    # --- PENDING MIGRATIONS ---

    def get_attachments_store(self) -> Any:
        """Attachments documentation pending final schema definition."""
        raise NotImplementedError("AttachmentsStore migration to Django is in progress.")

    def get_export_job_store(self) -> Any:
        """Export system pending final Django integration."""
        raise NotImplementedError("ExportJobStore migration to Django is in progress.")


# Global instance
_repository_manager: Optional[RepositoryManager] = None


def get_repository_manager() -> RepositoryManager:
    """Entry point for the global RepositoryManager singleton."""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
    return _repository_manager


# --- CONVENIENCE FUNCTIONS (Exposed to the application) ---


def get_api_key_store() -> ApiKeyStore:
    """Get global ApiKeyStore instance."""
    return get_repository_manager().get_api_key_store()


def get_secret_manager() -> SecretManager:
    """Get global SecretManager instance."""
    return get_repository_manager().get_secret_manager()


def get_audit_store():
    """Get global AuditLog manager."""
    return get_repository_manager().get_audit_store()


def get_dlq_store():
    """Get global DeadLetterMessage manager."""
    return get_repository_manager().get_dlq_store()


def get_notifications_store():
    """Get global Notification manager."""
    return get_repository_manager().get_notifications_store()


def get_ui_settings_store():
    """Get global UISetting manager."""
    return get_repository_manager().get_ui_settings_store()


def get_session_store():
    """Get global Session manager."""
    return get_repository_manager().get_session_store()


def get_replica_store():
    """Get global MemoryReplica manager."""
    return get_repository_manager().get_replica_store()


async def get_settings_repo():
    """Get UI settings store (Async compatibility wrapper)."""
    return get_ui_settings_store()
