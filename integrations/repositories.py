"""
Centralized repository singleton layer for all data stores and repositories.

This module provides singleton access to all database stores and repositories.
Imports are aligned with services.common.* to avoid mismatched prior paths.
"""

from __future__ import annotations

from typing import Optional

# Import all store classes from canonical locations
from services.common.attachments_store import AttachmentsStore
from services.common.audit_store import AuditStore as _AuditStore, from_env as _audit_store_from_env
from services.common.api_key_store import ApiKeyStore
from services.common.dlq_store import DLQStore
from services.common.export_job_store import ExportJobStore
from services.common.llm_credentials_store import LlmCredentialsStore
from services.common.memory_replica_store import MemoryReplicaStore
from services.common.notifications_store import NotificationsStore
from services.common.session_repository import PostgresSessionStore
from services.common.ui_settings_store import UiSettingsStore


class RepositoryManager:
    """Singleton manager for all repository instances."""

    def __init__(self) -> None:
        self._attachments_store: Optional[AttachmentsStore] = None
        self._audit_store: Optional[_AuditStore] = None
        self._api_key_store: Optional[ApiKeyStore] = None
        self._notifications_store: Optional[NotificationsStore] = None
        self._dlq_store: Optional[DLQStore] = None
        self._replica_store: Optional[MemoryReplicaStore] = None
        self._export_job_store: Optional[ExportJobStore] = None
        self._llm_credentials_store: Optional[LlmCredentialsStore] = None
        self._ui_settings_store: Optional[UiSettingsStore] = None
        self._session_store: Optional[PostgresSessionStore] = None

    def get_attachments_store(self) -> AttachmentsStore:
        """Get singleton instance of AttachmentsStore."""
        if self._attachments_store is None:
            self._attachments_store = AttachmentsStore()
        return self._attachments_store

    def get_audit_store(self) -> _AuditStore:
        """Get singleton instance of AuditStore.

        Respects AUDIT_STORE_MODE and SA01_DB_DSN via services.common.audit_store.from_env().
        """
        if self._audit_store is None:
            self._audit_store = _audit_store_from_env()
        return self._audit_store

    def get_api_key_store(self) -> ApiKeyStore:
        """Get singleton instance of ApiKeyStore."""
        if self._api_key_store is None:
            self._api_key_store = ApiKeyStore()
        return self._api_key_store

    def get_notifications_store(self) -> NotificationsStore:
        """Get singleton instance of NotificationsStore."""
        if self._notifications_store is None:
            self._notifications_store = NotificationsStore()
        return self._notifications_store

    def get_dlq_store(self) -> DLQStore:
        """Get singleton instance of DLQStore."""
        if self._dlq_store is None:
            self._dlq_store = DLQStore()
        return self._dlq_store

    def get_replica_store(self) -> MemoryReplicaStore:
        """Get singleton instance of MemoryReplicaStore."""
        if self._replica_store is None:
            self._replica_store = MemoryReplicaStore()
        return self._replica_store

    def get_export_job_store(self) -> ExportJobStore:
        """Get singleton instance of ExportJobStore."""
        if self._export_job_store is None:
            self._export_job_store = ExportJobStore()
        return self._export_job_store

    def get_llm_credentials_store(self) -> LlmCredentialsStore:
        """Get singleton instance of LlmCredentialsStore."""
        if self._llm_credentials_store is None:
            self._llm_credentials_store = LlmCredentialsStore()
        return self._llm_credentials_store

    def get_ui_settings_store(self) -> UiSettingsStore:
        """Get singleton instance of UiSettingsStore."""
        if self._ui_settings_store is None:
            self._ui_settings_store = UiSettingsStore()
        return self._ui_settings_store

    def get_session_store(self) -> PostgresSessionStore:
        """Get singleton instance of PostgresSessionStore."""
        if self._session_store is None:
            self._session_store = PostgresSessionStore()
        return self._session_store


# Global singleton instance
_repository_manager: Optional[RepositoryManager] = None


def get_repository_manager() -> RepositoryManager:
    """Get the global repository manager singleton."""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
    return _repository_manager


# Convenience functions for direct access
def get_attachments_store() -> AttachmentsStore:
    """Get singleton instance of AttachmentsStore."""
    return get_repository_manager().get_attachments_store()


def get_audit_store() -> _AuditStore:
    """Get singleton instance of AuditStore."""
    return get_repository_manager().get_audit_store()


def get_api_key_store() -> ApiKeyStore:
    """Get singleton instance of ApiKeyStore."""
    return get_repository_manager().get_api_key_store()


def get_notifications_store() -> NotificationsStore:
    """Get singleton instance of NotificationsStore."""
    return get_repository_manager().get_notifications_store()


def get_dlq_store() -> DLQStore:
    """Get singleton instance of DLQStore."""
    return get_repository_manager().get_dlq_store()


def get_replica_store() -> MemoryReplicaStore:
    """Get singleton instance of MemoryReplicaStore."""
    return get_repository_manager().get_replica_store()


def get_export_job_store() -> ExportJobStore:
    """Get singleton instance of ExportJobStore."""
    return get_repository_manager().get_export_job_store()


def get_llm_credentials_store() -> LlmCredentialsStore:
    """Get singleton instance of LlmCredentialsStore."""
    return get_repository_manager().get_llm_credentials_store()


def get_ui_settings_store() -> UiSettingsStore:
    """Get singleton instance of UiSettingsStore."""
    return get_repository_manager().get_ui_settings_store()


def get_session_store() -> PostgresSessionStore:
    """Get singleton instance of PostgresSessionStore."""
    return get_repository_manager().get_session_store()


# Additional missing function
async def get_settings_repo():
    return get_ui_settings_store()
