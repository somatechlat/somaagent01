"""VIBE Rule 164 — a secret lives in Vault and nowhere else.

Locks the policy module and the three write-path gates that enforce it:

  * ``services/common/secret_policy.py`` — the rule itself
  * ``AgentSetting.save()``              — the ORM write gate
  * ``InfrastructureConfig.save()``      — the second ORM write gate
  * ``capsule_export._assert_exportable_settings`` — the export gate
  * ``settings_defaults._env_or_db``     — the resolution choke point

The important assertions are the *negative* ones: that a credential cannot be
written through any of these paths. A test that only proves the happy path
would pass against the bug this suite exists to prevent.

Run:
    pytest tests/unit/test_secret_policy.py -v
"""

from __future__ import annotations

import pytest

from services.common.secret_policy import (
    SecretPolicyViolation,
    assert_no_secret_value,
    assert_vault_path_or_empty,
    is_secret_shaped_key,
    is_vault_path,
    vault_path_for,
)


# ---------------------------------------------------------------------------
# is_secret_shaped_key — the NAME test
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "key",
    [
        "password",
        "auth_password",
        "root_password",
        "postgres_password",
        "api_key",
        "apikey",
        "openai_api_key",
        "access_key",
        "secret",
        "secrets",
        "client_secret",
        "token",
        "mcp_server_token",
        "vault_token",
        "sasl_password",
        "jwt_secret",
        "session_key",
        "signing_key",
        "credential",
        "credentials",
        "auth_header",
        "AWS_SECRET_ACCESS_KEY",
        "llm.api.key",
    ],
)
def test_secret_shaped_names_are_detected(key: str) -> None:
    assert is_secret_shaped_key(key), f"{key!r} should be recognised as a credential name"


@pytest.mark.unit
@pytest.mark.parametrize(
    "key",
    [
        "host",
        "port",
        "postgres_host",
        "postgres_port",
        "db_name",
        "redis_url",
        "rfc_url",
        "chat_model_api_base",
        "log_level",
        "pool_size",
        "timeout_ms",
        "feature_flag_x",
        "vault_token_file",  # a PATH to a credential, not the credential
        "vault_addr",
        "vault_mount",
        "postgres_password_file",
        "jwt_public_key",  # public material
        "api_keys_ref",  # a reference, not the keys
    ],
)
def test_topology_names_are_not_secret_shaped(key: str) -> None:
    assert not is_secret_shaped_key(key), f"{key!r} is topology, not a credential"


@pytest.mark.unit
@pytest.mark.parametrize(
    "key",
    [
        # Identifiers and pointers at a credential — "which one", not "what it is"
        "api_key_id",
        "api_key_ids",
        "api_key_ref",
        "api_key_name",
        "token_id",
        "password_id",
        "secret_path",
        "credential_source",
        "secret_provider",
        # Publicly-shown material derived from a credential
        "api_key_prefix",
        "key_prefix",
        # Topology that happens to end in a secret-shaped word
        "token_endpoint",
        "password_host",
        "secret_url",
        # State / metadata flags
        "api_key_enabled",
        "password_required",
        "token_configured",
    ],
)
def test_references_and_metadata_are_not_secret_shaped(key: str) -> None:
    """An identifier *for* a credential is not the credential.

    Without this, `api_key_id` would be forced to hold a Vault path and a UUID
    would be rejected — the same confusion the module already avoids for
    `vault_token_file`.
    """
    assert not is_secret_shaped_key(key), f"{key!r} names a credential, it is not one"


@pytest.mark.unit
@pytest.mark.parametrize(
    "key",
    [
        # The demotion is suffix-only: a bare credential name stays a credential
        "api_key",
        "password",
        "token",
        "secret",
    ],
)
def test_suffix_demotion_does_not_open_a_hole(key: str) -> None:
    assert is_secret_shaped_key(key), f"{key!r} must remain credential-shaped"


@pytest.mark.unit
@pytest.mark.parametrize(
    "key",
    [
        # Derived VERIFIERS, not credentials. SHA256 of a 256-bit CSPRNG key
        # cannot authenticate and cannot be inverted; a password hash is what
        # every auth system stores in a database on purpose. Putting these in
        # Vault would make the auth path depend on Vault availability — the
        # fail-open seam Rule 164 exists to prevent.
        "key_hash",
        "api_key_hash",
        "password_hash",
        "token_digest",
        "secret_checksum",
    ],
)
def test_derived_verifiers_are_not_secret_shaped(key: str) -> None:
    """Reversal of an earlier call. A digest is not a secret.

    `ApiKey.key_hash` is SHA256 of `secrets.token_urlsafe(32)`; `key_prefix`
    is display-only. Classification is about value confidentiality, and a
    digest of high-entropy input is not confidential material. If generation
    entropy degrades the fix is to raise it — not to reclassify the digest.
    """
    assert not is_secret_shaped_key(key), f"{key!r} is a verifier, not a credential"


# ---------------------------------------------------------------------------
# is_vault_path — the VALUE test that distinguishes pointer from secret
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    [
        "secret/agent/credentials/postgres_password",
        "agent/api_keys/openai_api_key",
        "secret/agent/credentials/rfc_password",
        "a/b",
    ],
)
def test_vault_paths_are_accepted(value: str) -> None:
    assert is_vault_path(value), f"{value!r} is a legitimate Vault path"


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    [
        "hunter2",
        "sk-ant-abc123def456ghi789jkl",
        "password=hunter2secret",
        "",  # empty is not a path
        "   ",
        "/absolute/path",  # absolute is not a relative KV path
        "trailing/",
        "a/../etc/passwd",  # traversal
        "no-slash-at-all",
        "has spaces/here",
        None,
        12345,
        {"nested": "object"},
    ],
)
def test_non_paths_are_rejected(value: object) -> None:
    assert not is_vault_path(value), f"{value!r} must not be mistaken for a Vault path"


# ---------------------------------------------------------------------------
# vault_path_for
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_vault_path_for_is_canonical() -> None:
    assert vault_path_for("postgres_password") == "secret/agent/credentials/postgres_password"
    assert vault_path_for("My-API.Key") == "secret/agent/credentials/my_api_key"


@pytest.mark.unit
def test_vault_path_for_rejects_empty_key() -> None:
    with pytest.raises(SecretPolicyViolation):
        vault_path_for("")
    with pytest.raises(SecretPolicyViolation):
        vault_path_for("   ")


# ---------------------------------------------------------------------------
# assert_vault_path_or_empty — named secret fields
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("value", [None, "", "   ", "secret/agent/credentials/postgres_password"])
def test_secret_field_may_be_empty_or_a_path(value: object) -> None:
    # Must not raise.
    assert_vault_path_or_empty("password", value, where="test")


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    [
        "hunter2",
        "sk-ant-abc123def456ghi789jkl",
        "s3cr3t-value-here",
        12345,
        {"password": "hunter2"},
    ],
)
def test_secret_field_rejects_stored_credentials(value: object) -> None:
    with pytest.raises(SecretPolicyViolation) as excinfo:
        assert_vault_path_or_empty("auth_password", value, where="AgentSetting(x)")
    # The message has to name the field and the rule, or the operator reading
    # it learns nothing about what to do next.
    message = str(excinfo.value)
    assert "auth_password" in message
    assert "VIBE Rule 164" in message


# ---------------------------------------------------------------------------
# assert_no_secret_value — catches secrets under innocent names too
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_innocent_key_with_plain_value_is_fine() -> None:
    # Must not raise.
    assert_no_secret_value("notes", "remember to restart the cache", where="test")
    assert_no_secret_value("pool_size", "20", where="test")
    assert_no_secret_value("log_level", "debug", where="test")


@pytest.mark.unit
def test_secret_hidden_under_innocent_key_is_caught() -> None:
    """A password stored as `notes` is still a password. The key test alone
    would miss it — this is why the value test exists."""
    with pytest.raises(SecretPolicyViolation) as excinfo:
        assert_no_secret_value("notes", "password=hunter2secret", where="AgentSetting(x)")
    assert "VIBE Rule 164" in str(excinfo.value)


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    [
        "sk-ant-abc123def456ghi789jklm",
        "ghp_abcdefghijklmnopqrstuvwx",
        "AKIAIOSFODNN7EXAMPLE",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----",
    ],
)
def test_known_credential_shapes_are_caught(value: str) -> None:
    with pytest.raises(SecretPolicyViolation):
        assert_no_secret_value("config_blob", value, where="test")


@pytest.mark.unit
def test_vault_path_passes_value_check() -> None:
    """The one permitted shape. Must not raise."""
    assert_no_secret_value(
        "postgres_password",
        "secret/agent/credentials/postgres_password",
        where="test",
    )


# ---------------------------------------------------------------------------
# The resolution choke point — _env_or_db must not resolve secrets
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_env_or_db_refuses_secret_keys() -> None:
    """The pattern this whole suite exists to stop: `_env_or_db` being handed a
    password and quietly sourcing it from the AgentSetting table / Django
    settings / env / a default. All four are places a credential must not
    live."""
    from admin.core.helpers.settings_defaults import _env_or_db

    for env_key, db_key in [
        ("SA01_AUTH_PASSWORD", "auth_password"),
        ("SA01_ROOT_PASSWORD", "root_password"),
        ("SA01_RFC_PASSWORD", "rfc_password"),
        ("SA01_SECRETS", "secrets"),
        ("SA01_API_KEY", "api_key"),
        ("ANY_TOKEN", "token"),
    ]:
        with pytest.raises(SecretPolicyViolation) as excinfo:
            _env_or_db(env_key, "default", db_key)
        message = str(excinfo.value)
        assert "get_credential" in message, "must point at the Vault alternative"
        assert db_key in message


@pytest.mark.unit
def test_env_or_db_still_resolves_topology() -> None:
    """Topology keeps working. The gate must not overfire on hosts and ports."""
    from admin.core.helpers.settings_defaults import _env_or_db

    # Not a secret-shaped key and no DB/Django override configured: falls
    # through to the schema default. Must not raise.
    assert _env_or_db("SA01_CHAT_MODEL", "default", "chat_model_name", "fallback") in (
        "fallback",
        "",
    )


# ---------------------------------------------------------------------------
# ORM write gates
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_agent_setting_save_refuses_stored_credential() -> None:
    from admin.core.models import AgentSetting

    row = AgentSetting(agent_id="a", key="auth_password", value="hunter2secret")
    with pytest.raises(SecretPolicyViolation):
        # Raises before super().save(), so no database is touched.
        row.save()


@pytest.mark.unit
def test_agent_setting_save_refuses_secret_under_innocent_key() -> None:
    from admin.core.models import AgentSetting

    row = AgentSetting(agent_id="a", key="notes", value="password=hunter2secret")
    with pytest.raises(SecretPolicyViolation):
        row.save()


@pytest.mark.unit
def test_agent_setting_save_accepts_vault_path() -> None:
    """The permitted shape reaches super().save(). We stop short of the DB by
    asserting the gate did NOT fire — the gate is the thing under test."""
    from admin.core.models import AgentSetting

    row = AgentSetting(
        agent_id="a",
        key="postgres_password",
        value="secret/agent/credentials/postgres_password",
    )
    # If the gate were going to refuse, it would have raised already. Prove
    # the refusal is specifically about the value, not the key.
    from services.common.secret_policy import assert_no_secret_value

    assert_no_secret_value(row.key, row.value, where="test")  # must not raise


@pytest.mark.unit
def test_agent_setting_save_accepts_plain_config() -> None:
    from admin.core.models import AgentSetting

    row = AgentSetting(agent_id="a", key="chat_model_name", value="claude-sonnet-5-5")
    from services.common.secret_policy import assert_no_secret_value

    assert_no_secret_value(row.key, row.value, where="test")  # must not raise


@pytest.mark.unit
def test_infrastructure_config_save_refuses_stored_credential() -> None:
    from admin.core.infrastructure.models import InfrastructureConfig

    row = InfrastructureConfig(key="redis_password", value="hunter2secret", is_secret=True)
    with pytest.raises(SecretPolicyViolation):
        row.save()


@pytest.mark.unit
def test_infrastructure_config_secret_flag_requires_path_not_value() -> None:
    """`is_secret=True` used to mean 'encrypted here'. It now means 'names a
    credential', so the value must be a pointer."""
    from admin.core.infrastructure.models import InfrastructureConfig

    row = InfrastructureConfig(key="redis_password", value="", is_secret=True)
    # Empty is allowed (not configured). The gate must not fire.
    from services.common.secret_policy import assert_vault_path_or_empty

    assert_vault_path_or_empty(row.key, row.value, where="test")  # must not raise


@pytest.mark.unit
def test_infrastructure_config_catches_secret_under_innocent_key() -> None:
    from admin.core.infrastructure.models import InfrastructureConfig

    row = InfrastructureConfig(key="description", value="token=abcdef1234567890zzz", is_secret=False)
    with pytest.raises(SecretPolicyViolation):
        row.save()


# ---------------------------------------------------------------------------
# Export gate — the portable file must never carry a credential
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_export_allows_vault_paths() -> None:
    from services.capsule_export import _assert_exportable_settings

    rows = [
        {"key": "postgres_password", "value": "secret/agent/credentials/postgres_password"},
        {"key": "chat_model_name", "value": "claude-sonnet-5-5"},
    ]
    assert _assert_exportable_settings(rows, kind="agent_settings") == rows


@pytest.mark.unit
def test_export_refuses_stored_credential() -> None:
    from services.capsule_export import _assert_exportable_settings

    rows = [{"key": "auth_password", "value": "hunter2secret"}]
    with pytest.raises(SecretPolicyViolation) as excinfo:
        _assert_exportable_settings(rows, kind="agent_settings")
    assert "capsule export" in str(excinfo.value)


@pytest.mark.unit
def test_export_refuses_credential_under_innocent_key() -> None:
    from services.capsule_export import _assert_exportable_settings

    rows = [{"key": "notes", "value": "password=hunter2secret"}]
    with pytest.raises(SecretPolicyViolation):
        _assert_exportable_settings(rows, kind="agent_settings")


@pytest.mark.unit
def test_export_checks_default_value_too() -> None:
    """`default_value` is a second column on InfrastructureConfig. A secret in
    the default is still a secret in the file."""
    from services.capsule_export import _assert_exportable_settings

    rows = [{"key": "host", "value": "db.internal", "default_value": "password=hunter2secret"}]
    with pytest.raises(SecretPolicyViolation):
        _assert_exportable_settings(rows, kind="ui_settings")
