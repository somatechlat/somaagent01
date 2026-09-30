"""Phase C — MinIO object store is real, and fail-closed on configuration.

Two contracts are on trial:

* **Credentials come from Vault only**, at the paths below, and a missing or
  empty secret refuses to start the store and names the path. There is no ENV
  fallback, no empty default and no vendor-default credential shim.

* **Endpoint and bucket are required topology** (VIBE Rule 91). A missing
  configuration value raises; it is never replaced by a guess such as
  ``http://minio:9000``. A guessed endpoint is a silent fallback under another
  name, and it points at a host the operator never chose.

This suite reads the real Vault. It does not install a stand-in secret manager:
a test that replaces the gate with a recorder cannot tell you whether the gate
holds — it can only tell you that the recorder agrees with its author.

**It does not write to Vault either.** Mutating ``agent/credentials`` to
fabricate "present" or "empty" states would mean a test that fails mid-run
leaves the credential store different from how it found it. The credential
claims are made against whatever the real store actually holds:

* if both keys are absent, the fail-closed claim is exercised for real;
* if they are present, the build claim is exercised for real.

Claims that would require a write (partially-present, empty-string) are not
here. They are covered by the same fail-closed branch the absence case drives:
``if not access_key or not secret_key`` treats ``None`` and ``""`` identically.

The Vault paths below are written out longhand rather than imported from
``services.common.object_store`` on purpose. They are the published contract
(``SOMA-SETTINGS-MODEL-001``), so a test that merely echoed the production
constant would follow a silent path change instead of catching one.

Run:
    pytest tests/unit/test_minio_object_store.py -v

Requires a reachable Vault for the credential tests. Nothing is stubbed and
nothing is written.
"""

from __future__ import annotations

import pytest

ACCESS_PATH = "secret/agent/credentials/minio_access_key"
SECRET_PATH = "secret/agent/credentials/minio_secret_key"

ACCESS_KEY_SECRET = "minio_access_key"
SECRET_KEY_SECRET = "minio_secret_key"


@pytest.fixture
def vault():
    """The real secret manager. No stand-in, no recorder."""
    from services.common.unified_secret_manager import get_secret_manager

    manager = get_secret_manager()
    if not manager._is_available():
        pytest.skip("Vault is not available in this environment")
    return manager


@pytest.fixture
def real_minio_state(vault):
    """What Vault actually holds for the MinIO pair, read live.

    Returning the truth rather than arranging it is the point: the fail-closed
    claim is interesting exactly when the secrets are really missing, and the
    build claim is interesting exactly when they are really there.
    """
    return {
        ACCESS_KEY_SECRET: vault.get_credential(ACCESS_KEY_SECRET),
        SECRET_KEY_SECRET: vault.get_credential(SECRET_KEY_SECRET),
    }


# ---------------------------------------------------------------------------
# Fail-closed on credentials — read-only against the real store
# ---------------------------------------------------------------------------


class TestCredentialResolution:
    """Vault is the only credential source; missing secrets fail closed."""

    def test_no_env_fallback_when_vault_holds_nothing(
        self, monkeypatch, real_minio_state
    ):
        """ENV credentials must never be used, even if present.

        This is the load-bearing anti-shim claim: a ``MINIO_ACCESS_KEY`` in the
        environment is topology drift, not a credential source. If Vault has
        nothing, the store must refuse to start even with these set.
        """
        monkeypatch.setenv("MINIO_ACCESS_KEY", "from-env")
        monkeypatch.setenv("MINIO_SECRET_KEY", "from-env")

        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        if real_minio_state[ACCESS_KEY_SECRET] and real_minio_state[SECRET_KEY_SECRET]:
            pytest.skip("both MinIO credentials are provisioned in Vault")

        with pytest.raises(ObjectStoreUnavailable):
            get_object_store()

    def test_absent_credentials_refuse_to_start_and_name_the_paths(
        self, real_minio_state
    ):
        """Whatever is missing must be named. A caller who is told "no" with
        no path cannot tell which secret to provision."""
        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        access = real_minio_state[ACCESS_KEY_SECRET]
        secret = real_minio_state[SECRET_KEY_SECRET]

        if access and secret:
            pytest.skip("both MinIO credentials are provisioned in Vault")

        with pytest.raises(ObjectStoreUnavailable) as exc:
            get_object_store()

        msg = str(exc.value)
        if not access:
            assert ACCESS_PATH in msg
        if not secret:
            assert SECRET_PATH in msg

    def test_a_default_credential_is_never_invented(self, real_minio_state):
        """The anti-shim claim in its sharpest form.

        "minioadmin" is the well-known MinIO default. If the fail-closed check
        ever weakens to ``access_key or "minioadmin"``, a deployment with no
        Vault secrets would come up with credentials an attacker can guess.
        """
        from services.common.object_store import get_object_store, ObjectStoreUnavailable

        if real_minio_state[ACCESS_KEY_SECRET] and real_minio_state[SECRET_KEY_SECRET]:
            pytest.skip("both MinIO credentials are provisioned in Vault")

        with pytest.raises(ObjectStoreUnavailable) as exc:
            get_object_store()
        assert "minioadmin" not in str(exc.value)

    def test_present_credentials_build_the_store(self, monkeypatch, real_minio_state):
        """When Vault really holds the pair, the store really builds.

        Topology is supplied here the way an operator supplies it —
        ``MINIO_ENDPOINT`` and ``MINIO_BUCKET`` are required configuration and
        the deployment is expected to set them. That is ordinary config, not a
        stand-in: the MinIO client is lazy and this test never opens a socket.
        Credentials still come from Vault and nowhere else.
        """
        from services.common.object_store import get_object_store

        if not (
            real_minio_state[ACCESS_KEY_SECRET] and real_minio_state[SECRET_KEY_SECRET]
        ):
            pytest.skip("MinIO credentials are not provisioned in Vault")

        monkeypatch.setenv("MINIO_ENDPOINT", "http://minio.internal:9000")
        monkeypatch.setenv("MINIO_BUCKET", "unit-test-artefacts")

        store = get_object_store()
        assert store is not None
        assert store.bucket == "unit-test-artefacts"
        assert store.endpoint == "minio.internal:9000"
        for method in ("put_bytes", "get_bytes", "delete", "exists", "list_keys"):
            assert callable(getattr(store, method)), f"missing {method}"


# ---------------------------------------------------------------------------
# Topology is required — Rule 91
# ---------------------------------------------------------------------------


def _clear_topology(monkeypatch, *names: str) -> None:
    """Remove a topology value from both places ``_topology`` looks."""
    from django.conf import settings as dj_settings

    for name in names:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(dj_settings, name, None, raising=False)


class TestTopologyIsRequired:
    """VIBE Rule 91 — missing config raises; it is never defaulted.

    ``get_object_store`` used to call ``_topology("MINIO_ENDPOINT",
    "http://minio:9000")`` and ``_topology("MINIO_BUCKET", "soma-artefacts")``.
    Those guesses name a host the operator never chose and a bucket nobody
    declared — and in the Standalone topology no MinIO container is even
    started, so the default was a destination that did not exist. A guessed
    endpoint is a silent fallback under another name.
    """

    def test_a_missing_minio_endpoint_is_refused_not_defaulted(self, monkeypatch):
        _clear_topology(monkeypatch, "MINIO_ENDPOINT")

        from services.common.object_store import _topology, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            _topology("MINIO_ENDPOINT")

        assert "MINIO_ENDPOINT" in str(exc.value)

    def test_a_missing_minio_bucket_is_refused_not_defaulted(self, monkeypatch):
        _clear_topology(monkeypatch, "MINIO_BUCKET")

        from services.common.object_store import _topology, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            _topology("MINIO_BUCKET")

        assert "MINIO_BUCKET" in str(exc.value)

    def test_the_refusal_never_names_a_guessed_host(self, monkeypatch):
        """The error must tell the operator what to set, not what was assumed.

        A message that quotes the old default would read like the value came
        from somewhere and invites the operator to trust a host they never set.
        """
        _clear_topology(monkeypatch, "MINIO_ENDPOINT")

        from services.common.object_store import _topology, ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable) as exc:
            _topology("MINIO_ENDPOINT")

        assert "minio:9000" not in str(exc.value)


# ---------------------------------------------------------------------------
# Endpoint parsing is pure
# ---------------------------------------------------------------------------


class TestEndpointTopology:
    """Endpoint parsing needs no server and no fake — just the real function."""

    def _normalize(self, raw: str):
        from services.common.object_store import _normalize_endpoint

        return _normalize_endpoint(raw)

    def test_host_port_without_scheme_is_insecure(self):
        assert self._normalize("minio:9000") == ("minio:9000", False)

    def test_https_marks_the_connection_secure(self):
        assert self._normalize("https://minio.internal:9000") == (
            "minio.internal:9000",
            True,
        )

    def test_http_is_insecure(self):
        assert self._normalize("http://minio.internal:9000") == (
            "minio.internal:9000",
            False,
        )

    def test_a_path_on_the_endpoint_is_refused(self):
        """A bucket smuggled into the endpoint would silently target the wrong
        place. The bucket belongs in MINIO_BUCKET."""
        from services.common.object_store import ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable):
            self._normalize("http://minio:9000/some-bucket")

    def test_a_scheme_with_no_host_is_refused(self):
        from services.common.object_store import ObjectStoreUnavailable

        with pytest.raises(ObjectStoreUnavailable):
            self._normalize("http://")

    def test_endpoint_is_read_from_configuration(self, monkeypatch):
        """The endpoint is non-secret topology: settings/env, never Vault."""
        from django.conf import settings as dj_settings

        monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
        monkeypatch.setattr(dj_settings, "MINIO_ENDPOINT", None, raising=False)
        monkeypatch.setenv("MINIO_ENDPOINT", "http://minio.internal:9000")

        from services.common.object_store import _normalize_endpoint, _topology

        assert _normalize_endpoint(_topology("MINIO_ENDPOINT")) == (
            "minio.internal:9000",
            False,
        )
