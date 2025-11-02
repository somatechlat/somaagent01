import types

import pytest

from services.common import vault_secrets


@pytest.fixture(autouse=True)
def clear_cache():
    vault_secrets.refresh_cached_secrets()
    yield
    vault_secrets.refresh_cached_secrets()


class _DummyKVv2:
    def __init__(self, data):
        self._data = data

    def read_secret_version(self, path, mount_point):  # noqa: D401 - mimic hvac
        return {"data": {"data": self._data}}


class _DummySecrets:
    def __init__(self, data):
        self.kv = types.SimpleNamespace(v2=_DummyKVv2(data))


class _DummyClient:
    def __init__(self, *, data, **kwargs):
        self.secrets = _DummySecrets(data)


def _inject_hvac(monkeypatch, data):
    dummy_module = types.SimpleNamespace(Client=lambda **kwargs: _DummyClient(data=data, **kwargs))
    monkeypatch.setattr(vault_secrets, "hvac", dummy_module)


def test_load_kv_secret_returns_value(monkeypatch):
    _inject_hvac(monkeypatch, {"jwt": "super-secret"})
    monkeypatch.setenv("VAULT_TOKEN", "dummy")

    secret = vault_secrets.load_kv_secret(path="secret/data/jwt", key="jwt")
    assert secret == "super-secret"


def test_load_kv_secret_missing_key(monkeypatch, caplog):
    _inject_hvac(monkeypatch, {"other": "value"})
    monkeypatch.setenv("VAULT_TOKEN", "dummy")

    secret = vault_secrets.load_kv_secret(path="secret/data/jwt", key="jwt")
    assert secret is None
    assert any("Secret key missing" in message for message in caplog.messages)


def test_load_kv_secret_missing_token(monkeypatch, caplog):
    _inject_hvac(monkeypatch, {"jwt": "ignored"})

    secret = vault_secrets.load_kv_secret(path="secret/data/jwt", key="jwt")
    assert secret is None
    assert any("Vault token missing" in message for message in caplog.messages)


def test_load_kv_secret_handles_hvac_errors(monkeypatch, caplog):
    class _BrokenClient:
        def __init__(self, **kwargs):  # noqa: D401
            raise RuntimeError("boom")

    dummy_module = types.SimpleNamespace(Client=_BrokenClient)
    monkeypatch.setattr(vault_secrets, "hvac", dummy_module)
    monkeypatch.setenv("VAULT_TOKEN", "dummy")

    secret = vault_secrets.load_kv_secret(path="secret/data/jwt", key="jwt")
    assert secret is None
    assert any("Failed to read secret" in message for message in caplog.messages)


def test_gateway_hydrates_secret_from_vault(monkeypatch):
    import services.gateway.main as gateway_main

    vault_secrets.refresh_cached_secrets()

    def fake_load_kv_secret(*, path, key, mount_point, logger):  # noqa: D401
        assert path == "secret/data/jwt"
        assert key == "vaultKey"
        assert mount_point == "kv"
        logger.info("fake vault load")
        return "vault-secret" if key == "vaultKey" else None

    monkeypatch.setenv("GATEWAY_JWT_VAULT_PATH", "secret/data/jwt")
    monkeypatch.setenv("GATEWAY_JWT_VAULT_MOUNT", "kv")
    monkeypatch.setenv("GATEWAY_JWT_VAULT_SECRET_KEY", "vaultKey")
    monkeypatch.delenv("GATEWAY_JWT_SECRET", raising=False)

    original_secret = gateway_main.JWT_SECRET
    monkeypatch.setattr(gateway_main, "load_kv_secret", fake_load_kv_secret)
    monkeypatch.setattr(gateway_main, "JWT_SECRET", None, raising=False)

    gateway_main._hydrate_jwt_credentials_from_vault()
    assert gateway_main.JWT_SECRET == "vault-secret"

    if original_secret is not None:
        monkeypatch.setattr(gateway_main, "JWT_SECRET", original_secret, raising=False)
