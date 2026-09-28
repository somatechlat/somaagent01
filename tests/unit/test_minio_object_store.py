"""Phase C — MinIO object store is real, and fail-closed on credentials.

MinIO credentials come from Vault only:

    secret/agent/credentials/minio_access_key
    secret/agent/credentials/minio_secret_key

Resolved through UnifiedSecretManager.get_credential(). There is NO ENV
fallback, NO empty default, NO "minioadmin" shim — if either secret is missing
or Vault is unreachable, the object store does not start and the error names
the exact missing Vault path.

Run:
    pytest tests/unit/test_minio_object_store.py -v
"""

from __future__ import annotations

import pytest

ACCESS_PATH = "secret/agent/credentials/minio_access_key"
SECRET_PATH = "secret/agent/credentials/minio_secret_key"


class RecordingSecretManager:
    """Recording stand-in for UnifiedSecretManager (Vault-backed)."""

    def __init__(self, values: dict[str, str | None], error: Exception | None = None):
        self.values = values
        self.error = error
        self.requested: list[str] = []

    def get_credential(self, key: str):
        self.requested.append(key)
        if self.error is not None:
            raise self.error
        return self.values.get(key)


def _install_secrets(monkeypatch, manager: RecordingSecretManager) -> None:
    import services.common.object_store as os_mod

    monkeypatch.setattr(os_mod, "get_secret_manager", lambda: manager)


class TestCredentialResolution:
    """Vault is the only credential source; missing secrets fail closed."""

    def test_missing_access_key_names_vault_path(self, monkeypatch):
        _install_secrets(monkeypatch, RecordingSecretManager({"minio_secret_key": "s"}))

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            get_object_store()
        assert ACCESS_PATH in str(exc.value)

    def test_missing_secret_key_names_vault_path(self, monkeypatch):
        _install_secrets(monkeypatch, RecordingSecretManager({"minio_access_key": "a"}))

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            get_object_store()
        assert SECRET_PATH in str(exc.value)

    def test_vault_unreachable_names_both_paths(self, monkeypatch):
        _install_secrets(
            monkeypatch, RecordingSecretManager({}, error=ConnectionError("vault down"))
        )

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            get_object_store()
        msg = str(exc.value)
        assert ACCESS_PATH in msg and SECRET_PATH in msg

    def test_no_env_fallback_when_vault_missing(self, monkeypatch):
        """ENV credentials must never be used, even if present."""
        monkeypatch.setenv("MINIO_ACCESS_KEY", "from-env")
        monkeypatch.setenv("MINIO_SECRET_KEY", "from-env")
        _install_secrets(monkeypatch, RecordingSecretManager({}))

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable):
            get_object_store()

    def test_no_minioadmin_default(self, monkeypatch):
        """An empty/unset Vault secret must not become minioadmin."""
        _install_secrets(
            monkeypatch,
            RecordingSecretManager({"minio_access_key": "", "minio_secret_key": ""}),
        )

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable):
            get_object_store()

    def test_reads_both_credential_keys_from_vault(self, monkeypatch):
        manager = RecordingSecretManager({"minio_access_key": "AKIA", "minio_secret_key": "SECRET"})
        _install_secrets(monkeypatch, manager)

        from services.common.object_store import get_object_store

        store = get_object_store()
        assert set(manager.requested) == {"minio_access_key", "minio_secret_key"}
        assert store is not None


class TestObjectStoreSurface:
    """The store is real object storage — put/get/exists against a bucket."""

    def _store(self, monkeypatch):
        _install_secrets(
            monkeypatch,
            RecordingSecretManager({"minio_access_key": "AKIA", "minio_secret_key": "SECRET"}),
        )
        from services.common.object_store import get_object_store

        return get_object_store()

    def test_exposes_put_get_delete_surface(self, monkeypatch):
        store = self._store(monkeypatch)
        for method in ("put_bytes", "get_bytes", "delete", "exists", "list_keys"):
            assert callable(getattr(store, method)), f"missing {method}"

    def test_endpoint_comes_from_settings_not_secrets(self, monkeypatch):
        """Endpoint is non-secret topology — env/settings, never Vault."""
        monkeypatch.setenv("MINIO_ENDPOINT", "http://minio.internal:9000")
        store = self._store(monkeypatch)
        assert store.endpoint == "minio.internal:9000"
        assert store.secure is False

    def test_bucket_namespace_is_auditable(self, monkeypatch):
        store = self._store(monkeypatch)
        assert store.bucket, "object store must declare its bucket"
