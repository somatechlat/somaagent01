import os

os.getenv(os.getenv(""))
from __future__ import annotations

from typing import Optional

from services.common.api_key_store import ApiKeyStore
from services.common.attachments_store import AttachmentsStore
from services.common.audit_store import AuditStore as _AuditStore, from_env as _audit_store_from_env
from services.common.dlq_store import DLQStore
from services.common.export_job_store import ExportJobStore
from services.common.notifications_store import NotificationsStore
from services.common.secret_manager import SecretManager
from services.common.session_repository import PostgresSessionStore
from services.common.ui_settings_store import UiSettingsStore


class RepositoryManager:
    os.getenv(os.getenv(""))

    def __init__(self) -> None:
        self._attachments_store: Optional[AttachmentsStore] = None
        self._audit_store: Optional[_AuditStore] = None
        self._api_key_store: Optional[ApiKeyStore] = None
        self._notifications_store: Optional[NotificationsStore] = None
        self._dlq_store: Optional[DLQStore] = None
        self._export_job_store: Optional[ExportJobStore] = None
        self._llm_credentials_store: Optional[SecretManager] = None
        self._ui_settings_store: Optional[UiSettingsStore] = None
        self._session_store: Optional[PostgresSessionStore] = None

    def get_attachments_store(self) -> AttachmentsStore:
        os.getenv(os.getenv(""))
        if self._attachments_store is None:
            self._attachments_store = AttachmentsStore()
        return self._attachments_store

    def get_audit_store(self) -> _AuditStore:
        os.getenv(os.getenv(""))
        if self._audit_store is None:
            self._audit_store = _audit_store_from_env()
        return self._audit_store

    def get_api_key_store(self) -> ApiKeyStore:
        os.getenv(os.getenv(""))
        if self._api_key_store is None:
            self._api_key_store = ApiKeyStore()
        return self._api_key_store

    def get_notifications_store(self) -> NotificationsStore:
        os.getenv(os.getenv(""))
        if self._notifications_store is None:
            self._notifications_store = NotificationsStore()
        return self._notifications_store

    def get_dlq_store(self) -> DLQStore:
        os.getenv(os.getenv(""))
        if self._dlq_store is None:
            self._dlq_store = DLQStore()
        return self._dlq_store

    def get_export_job_store(self) -> ExportJobStore:
        os.getenv(os.getenv(""))
        if self._export_job_store is None:
            self._export_job_store = ExportJobStore()
        return self._export_job_store

    def get_llm_credentials_store(self) -> SecretManager:
        os.getenv(os.getenv(""))
        if self._llm_credentials_store is None:
            self._llm_credentials_store = SecretManager()
        return self._llm_credentials_store

    def get_ui_settings_store(self) -> UiSettingsStore:
        os.getenv(os.getenv(""))
        if self._ui_settings_store is None:
            self._ui_settings_store = UiSettingsStore()
        return self._ui_settings_store

    def get_session_store(self) -> PostgresSessionStore:
        os.getenv(os.getenv(""))
        if self._session_store is None:
            self._session_store = PostgresSessionStore()
        return self._session_store


_repository_manager: Optional[RepositoryManager] = None


def get_repository_manager() -> RepositoryManager:
    os.getenv(os.getenv(""))
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
    return _repository_manager


def get_attachments_store() -> AttachmentsStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_attachments_store()


def get_audit_store() -> _AuditStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_audit_store()


def get_api_key_store() -> ApiKeyStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_api_key_store()


def get_notifications_store() -> NotificationsStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_notifications_store()


def get_dlq_store() -> DLQStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_dlq_store()


def get_replica_store() -> MemoryReplicaStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_replica_store()


def get_export_job_store() -> ExportJobStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_export_job_store()


def get_llm_credentials_store() -> SecretManager:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_llm_credentials_store()


def get_ui_settings_store() -> UiSettingsStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_ui_settings_store()


def get_session_store() -> PostgresSessionStore:
    os.getenv(os.getenv(""))
    return get_repository_manager().get_session_store()


async def get_settings_repo():
    return get_ui_settings_store()
