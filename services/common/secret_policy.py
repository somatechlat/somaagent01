"""The secret policy, in one place. VIBE Rule 164.

THE RULE
--------

    A secret exists in exactly one place: Vault.
    Anything that would hold a secret holds a *Vault path* instead — or
    holds nothing at all.

That is the whole policy. Everything else in this module is enforcement.

What this forbids, and why each one is a real failure and not a style
preference:

* **A secret in a settings store** (``AgentSetting``, ``InfrastructureConfig``,
  ``SettingsModel``). Postgres is then a second secret store. It has its own
  backup, its own access control, its own dump — and it is where a
  ``pg_dump`` or a stolen replica walks away with every credential.
* **A secret in Django settings / ``.env`` / an environment variable.** Env is
  visible in ``ps``, in ``/proc/*/environ``, in every crash dump and in the
  container inspector.
* **A secret in a capsule export.** The export is a portable file people
  email. It must describe an agent, never carry its credentials.
* **A secret-shaped key whose value is silently ``""`` or ``None``.** That is
  the failure this codebase keeps having: "cannot read the store" is reported
  as "not configured", and then something downstream either 500s far from the
  cause or — worse — works, on a default nobody chose.

What this deliberately does NOT cover:

* **User passwords.** Those are identity credentials managed by RBAC /
  Keycloak. They are not application secrets and they never enter these
  stores.
* **Topology.** Hosts, ports, URLs, database names, log levels, feature
  toggles, model names, timeouts. Not credentials. They belong in
  configuration and may live in env.

The one permitted shape for a secret anywhere in this codebase is a **Vault
path** — a string that names where the value lives, never the value::

    secret/agent/credentials/postgres_password

``is_vault_path()`` is how a consumer tells "this field names a secret" from
"this field is a secret". That distinction is the entire safety mechanism.
"""

from __future__ import annotations

import re
from typing import Any, Final

__all__ = [
    "SecretPolicyViolation",
    "VAULT_PATH_RE",
    "SECRET_KEY_RE",
    "is_secret_shaped_key",
    "is_vault_path",
    "vault_path_for",
    "assert_vault_path_or_empty",
    "assert_no_secret_value",
]


class SecretPolicyViolation(ValueError):
    """Raised when a secret would be stored outside Vault.

    Deliberately a ``ValueError`` subclass: it is a programming/config error
    that must fail the write, not an infrastructure outage and not something
    a caller may catch and continue past with a default.
    """


# ---------------------------------------------------------------------------
# What counts as a secret-shaped NAME
# ---------------------------------------------------------------------------

# A key is secret-shaped when its name says "I am a credential". Matched
# against the key only — never against the value — so a legitimate value that
# happens to look random is not caught, and a password stored under
# "notes" is still caught by the value checks below.
#
# `_fn` / `_file` / `_path` / `_url` / `_addr` / `_host` / `_port` are
# EXCLUDED on purpose: they name *where* a thing is, not *what it is*. That
# is exactly the topology/credential split. `VAULT_TOKEN_FILE` is a path.
# `POSTGRES_HOST` is a host. Neither is a secret.
_SECRET_KEY_RE: Final = re.compile(
    r"""
    (?:^|[_\-.])
    (?:
        password | passwd | pwd |
        secret | secrets |
        token | tokens |
        # Compound names may join on `_`, `-` or `.`: api_key, api-key, api.key
        api[_\-.]?key | access[_\-.]?key | secret[_\-.]?key |
        private[_\-.]?key | public[_\-.]?key |
        credential | credentials |
        authorization | auth[_\-.]?header |
        sasl[_\-.]?password | sasl[_\-.]?secret |
        session[_\-.]?key | encryption[_\-.]?key | signing[_\-.]?key |
        client[_\-.]?secret | client[_\-.]?password |
        root[_\-.]?password | root[_\-.]?token
    )
    (?:$|[_\-.])
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Names that LOOK secret-shaped but are topology or a reference. Each entry
# here has to earn its place — it is a hole in the filter.
_TOPOLOGY_EXEMPTIONS: Final = frozenset(
    {
        "vault_token_file",  # a PATH to a credential, not the credential
        "vault_addr",  # API address
        "vault_mount",  # KV mount name
        "vault_path_prefix",  # path prefix
        "postgres_password_file",  # a PATH
        "test_db_password_file",  # a PATH
        "keycloak_admin_password_file",  # a PATH
        "kc_db_password_file",  # a PATH
        "token_file",  # a PATH
        "api_keys_ref",  # a REFERENCE to Vault, not the keys
        "jwt_public_key",  # public material, not a credential
        "public_key",  # public material
        "keycloak_public_key",  # public material
    }
)

SECRET_KEY_RE: Final = _SECRET_KEY_RE

# Suffixes that demote a secret-shaped stem to a *reference*, to metadata, or
# to a *derived verifier*. The split is "where / which / what kind", not "what
# it is" — the same one `VAULT_TOKEN_FILE` draws against `VAULT_TOKEN`.
#
#   api_key_id       identifies a key        -> not the key
#   api_key_prefix   displays part of a key  -> deliberately public
#   password_file    points at a password    -> not the password
#   token_endpoint   topology                -> not the token
#   key_hash         verifier for a key      -> not the key
#
# `_hash` / `_digest` / `_checksum` are here, and that is a considered
# reversal. A one-way digest is **not** a credential: it cannot authenticate
# to anything and it is not invertible from 256-bit CSPRNG input
# (`ApiKey.key_hash` = SHA256 of `secrets.token_urlsafe(32)`, and
# `key_prefix` is display-only). Password hashes are the same story — every
# auth system stores them in a database on purpose, which is what makes a
# stored verifier work without a network hop to Vault on each request.
#
# Classifying a verifier as a secret is not conservative, it is wrong: it
# would push digests into Vault, make the auth path depend on Vault
# availability (exactly the fail-open seam Rule 164 exists to prevent), and
# teach people to ignore the scanner when it fires on a safe field.
#
# The real dependency is **generation entropy**, not storage location. If a
# `*_hash` is ever built from a low-entropy or user-chosen value it becomes a
# cracking oracle, and the fix is to raise the entropy of what goes in — not
# to reclassify the digest. The value detectors below still catch actual
# credential material wherever it is stored.
_REFERENCE_SUFFIXES: Final = (
    "_id",
    "_ids",
    "_ref",
    "_refs",
    "_name",
    "_names",
    "_file",
    "_files",
    "_path",
    "_paths",
    "_url",
    "_urls",
    "_uri",
    "_addr",
    "_address",
    "_host",
    "_port",
    "_endpoint",
    "_base",
    "_fn",
    "_func",
    "_prefix",
    "_suffix",
    "_algo",
    "_algorithm",
    "_type",
    "_kind",
    "_source",
    "_provider",
    "_enabled",
    "_required",
    "_present",
    "_configured",
    # Derived verifiers — not credentials (see the note above)
    "_hash",
    "_digest",
    "_checksum",
    "_hmac",
)


def _is_reference_suffix(normalized: str) -> bool:
    """True when the key's tail says it names/points at a credential, not holds it."""
    return any(normalized.endswith(suffix) for suffix in _REFERENCE_SUFFIXES)


def is_secret_shaped_key(key: str) -> bool:
    """True when the NAME of this key says it holds a credential.

    This is a name test. Pair it with :func:`assert_no_secret_value` for the
    value test — a secret hidden under a harmless name is still a secret.
    """
    if not key:
        return False
    normalized = key.strip().lower()
    if normalized in _TOPOLOGY_EXEMPTIONS:
        return False
    if _is_reference_suffix(normalized):
        return False
    return bool(_SECRET_KEY_RE.search(normalized))


# ---------------------------------------------------------------------------
# What counts as a Vault path
# ---------------------------------------------------------------------------

# `secret/agent/credentials/postgres_password`, `secret/agent/api_keys/openai_api_key`
VAULT_PATH_RE: Final = re.compile(r"^[\w./-]+$")


def is_vault_path(value: Any) -> bool:
    """True when this value NAMES a secret rather than BEING one.

    A Vault path is a relative KV path under the configured mount. It is
    navigable, low-entropy, and contains no credential material. The one
    shape a secret is allowed to take anywhere outside Vault.
    """
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text or len(text) > 512:
        return False
    if not VAULT_PATH_RE.match(text):
        return False
    # Must actually navigate somewhere: at least one path segment separator
    # and a plausible leading segment. A bare word like "hunter2" is not a
    # path; "agent/credentials/x" is.
    if "/" not in text:
        return False
    if text.startswith("/") or text.endswith("/"):
        return False
    if ".." in text:
        return False
    return True


def vault_path_for(key: str) -> str:
    """The canonical Vault path for a credential key.

    ``postgres_password`` -> ``secret/agent/credentials/postgres_password``
    """
    if not key or not key.strip():
        raise SecretPolicyViolation("cannot build a Vault path for an empty key")
    slug = key.strip().lower().replace("-", "_").replace(".", "_")
    return f"secret/agent/credentials/{slug}"


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------

def assert_vault_path_or_empty(key: str, value: Any, *, where: str) -> None:
    """A secret-shaped field may hold a Vault path, or hold nothing. Never a value.

    Safe to call for **any** key: keys that are not secret-shaped return
    immediately. That matters because the callers (`AgentSetting.save`,
    `capsule_export`, …) pass every row through one gate — without the name
    check inside, ordinary config like `chat_model_name = "claude-sonnet-5-5"`
    would be rejected as a stored credential.

    For a secret-shaped key, empty means "not configured", which is
    legitimate — the consumer fail-closes on the feature. A non-empty value
    must be a pointer into Vault.
    """
    if not is_secret_shaped_key(key):
        return
    if value is None:
        return
    if not isinstance(value, str):
        raise SecretPolicyViolation(
            f"{where}: field {key!r} is secret-shaped and must hold a Vault "
            f"path (e.g. {vault_path_for(key)}) or be empty. Got "
            f"{type(value).__name__}, which is a stored secret outside Vault "
            f"(VIBE Rule 164)."
        )
    text = value.strip()
    if text == "":
        return
    if is_vault_path(text):
        return
    raise SecretPolicyViolation(
        f"{where}: field {key!r} is secret-shaped and holds something that is "
        f"not a Vault path. Secrets live in Vault and this field may only "
        f"point at one — e.g. {vault_path_for(key)}. Storing the value here "
        f"makes this database a second secret store (VIBE Rule 164)."
    )


def assert_no_secret_value(key: str, value: Any, *, where: str) -> None:
    """Reject a write that would place credential material in a store.

    Two independent catches, because either one alone is bypassable:

    1. The KEY is secret-shaped -> the value must be empty or a Vault path.
    2. The VALUE looks like credential material -> rejected regardless of key.

    (2) is what stops someone storing a password under ``notes``.
    """
    assert_vault_path_or_empty(key, value, where=where)

    if value is None:
        return
    if not isinstance(value, str):
        # Non-string values under a non-secret key are ordinary config
        # (numbers, booleans, JSON). Nothing to do.
        return

    text = value.strip()
    if text == "" or is_vault_path(text):
        return

    # Value-shaped credential detectors. High-entropy blobs and literal
    # assignments both count — the point is to catch a secret that was given
    # a harmless name.
    if _LOOKS_LIKE_CREDENTIAL.search(text):
        raise SecretPolicyViolation(
            f"{where}: field {key!r} holds value that looks like credential "
            f"material, not configuration. Secrets live in Vault (VIBE Rule "
            f"164) — store them there and put the path "
            f"({vault_path_for(key)}) in this field instead."
        )


# Entropy-ish / assignment-ish credential material. Deliberately narrow so
# ordinary prose and JSON config do not trip it; deliberately present so a
# real secret cannot hide behind a friendly key name.
_LOOKS_LIKE_CREDENTIAL: Final = re.compile(
    r"""
    (?:
        # literal assignment shapes: password=hunter2, "api_key": "sk-..."
        (?:password|passwd|secret|token|api[_\-.]?key|credential)\s*[:=]\s*\S{8,}
        |
        # Anthropic / OpenAI / Stripe / GitHub / Slack style: sk-ant-…, ghp_…
        # The body may itself contain `-` (sk-ant-…), so it is not [A-Za-z0-9].
        \b(?:sk|pk|rk|ghp|gho|ghs|ghu|xox[baprs])[_-][A-Za-z0-9_-]{16,}
        |
        # AWS access key ids: AKIA + 16 chars, no separator after the prefix
        \b(?:AKIA|ASIA)[A-Z0-9]{16}\b
        |
        # PEM private key blocks
        -----BEGIN[A-Z ]*PRIVATE\ KEY-----
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
