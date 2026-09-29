"""Helpers for retrieving secrets from HashiCorp Vault."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)

try:
    import hvac  # type: ignore
except ImportError:
    raise ImportError(
        "hvac library is required for Vault integration. Install with: pip install hvac"
    )


def _ensure_hvac() -> Any:
    """Execute ensure hvac."""

    return hvac


class VaultAuthError(RuntimeError):
    """Vault could not be authenticated to.

    This is an infrastructure failure, NOT a missing secret. It must never be
    reported as ``None``: a caller that cannot reach Vault has no idea whether
    the secret exists, and returning ``None`` turns "I cannot tell" into
    "it is absent" — which then looks like a legitimately optional secret
    (VIBE Rule 91 / Rule 164).
    """


# Token is a FILE, never an environment variable (VIBE Rule 164). A path is
# topology; the credential it names is not. There is deliberately no
# ``VAULT_TOKEN`` env read anywhere in this module — exporting a token into a
# shell leaves it in ``ps``, in ``/proc/*/environ`` and in every crash dump.
DEFAULT_TOKEN_FILE_ENV = "VAULT_TOKEN_FILE"


def _resolve_vault_token(*, token: Optional[str], token_file: Optional[str]) -> str:
    """Return the Vault token, or raise ``VaultAuthError``.

    Resolution order:

    1. ``token_file`` argument (explicit)
    2. ``VAULT_TOKEN_FILE`` environment variable — a PATH, not a credential
    3. ``token`` argument — only what a caller read from its own secret store

    A missing, unreadable or empty token is fatal. It is never treated as
    "no secrets available".
    """
    candidates: list[tuple[str, Optional[str]]] = [
        ("token_file argument", token_file),
        (DEFAULT_TOKEN_FILE_ENV, os.environ.get(DEFAULT_TOKEN_FILE_ENV)),
    ]
    for source, path in candidates:
        if not path:
            continue
        try:
            resolved = Path(path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise VaultAuthError(
                f"VIBE Rule 164 VIOLATION: cannot read the Vault token file "
                f"named by {source} at {path!r}: {exc.strerror or exc}. The "
                f"token is a credential and is delivered as a file — fix the "
                f"path or the file's permissions (0600); it is never read from "
                f"the environment."
            ) from None
        if resolved:
            return resolved
        raise VaultAuthError(
            f"VIBE Rule 164 VIOLATION: the Vault token file named by "
            f"{source} at {path!r} is empty. An empty token is not a valid "
            f"credential and must not be treated as 'no secrets'."
        )

    if token:
        return token

    raise VaultAuthError(
        f"VIBE Rule 164 VIOLATION: no Vault token available. Point "
        f"{DEFAULT_TOKEN_FILE_ENV} at a file containing the token (for local "
        f"stacks that is infra/standalone/secrets/vault_root_token, or an "
        f"app-scoped token file in production). The token is never taken from "
        f"the environment and there is no fallback — without it Vault cannot "
        f"be read at all, which is not the same as a secret being absent."
    )


def _coerce_verify(verify: Optional[str | bool]) -> str | bool:
    """Execute coerce verify.

    Args:
        verify: The verify.
    """

    if isinstance(verify, bool) or verify is None:
        return True if verify is None else verify
    verify_str = str(verify).strip()
    lowered = verify_str.lower()
    if lowered in {"false", "0", "no", "off"}:
        return False
    return verify_str


@lru_cache(maxsize=32)
def load_kv_secret(
    *,
    path: str,
    key: str,
    mount_point: str = "secret",
    url: Optional[str] = None,
    namespace: Optional[str] = None,
    token: Optional[str] = None,
    token_file: Optional[str] = None,
    verify: Optional[str | bool] = None,
    logger: Optional[logging.Logger] = None,
) -> Optional[str]:
    """Fetch a KV v2 secret from Vault.

    Returns ``None`` only when Vault answered and the key is genuinely absent —
    the legitimate state of an optional secret. Any failure to *reach or
    authenticate to* Vault raises ``VaultAuthError`` instead, because "I could
    not look" must not be reported as "it is not there".

    Results are cached per unique configuration to avoid repeated round-trips.
    """

    log = logger or LOGGER

    if not path:
        return None

    hvac_mod = _ensure_hvac()

    url = url or os.environ.get("VAULT_ADDR")
    if not url:
        raise VaultAuthError(
            "VIBE Rule 164 VIOLATION: VAULT_ADDR is not set. Point it at the "
            "running Vault's API address (topology, not a credential)."
        )
    namespace = namespace or os.environ.get("VAULT_NAMESPACE")
    token = _resolve_vault_token(token=token, token_file=token_file)

    if verify is None:
        if os.environ.get("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = os.environ.get("VAULT_CA_CERT") or True
    else:
        verify_value = _coerce_verify(verify)

    try:
        client = hvac_mod.Client(
            url=url,
            namespace=namespace,
            token=token,
            verify=verify_value,
        )
        response = client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=mount_point,
        )
    except Exception as exc:
        # 404 / InvalidPath means Vault answered and the document is not
        # there — a real "absent", so None is correct. Everything else
        # (sealed, unreachable, bad token, TLS, timeout) means we could not
        # look, and that must not be reported as absent.
        exc_name = type(exc).__name__
        if exc_name in {"InvalidPath", "NotFound"}:
            log.debug(
                "Vault path absent",
                extra={"path": path, "mount_point": mount_point},
            )
            return None
        raise VaultAuthError(
            f"VIBE Rule 164 VIOLATION: cannot read {mount_point}/{path} from "
            f"Vault at {url}: {exc_name}. The secret's presence is unknown, so "
            f"this is not a missing key. Bring Vault up and unsealed, and check "
            f"the token file — there is no local copy to fall back on."
        ) from None

    data = response.get("data", {}) if isinstance(response, dict) else {}
    nested = data.get("data") if isinstance(data, dict) else None
    if isinstance(nested, dict):
        value = nested.get(key)
        if value is not None:
            return str(value)
    else:
        log.warning(
            "Unexpected Vault response payload",
            extra={"path": path, "payload_type": type(response).__name__},
        )
    log.warning(
        "Secret key missing in Vault response",
        extra={"path": path, "key": key, "mount_point": mount_point},
    )
    return None


def refresh_cached_secrets() -> None:
    """Clear cached Vault reads (used in tests)."""
    load_kv_secret.cache_clear()


def save_kv_secret(
    path: str,
    key: str,
    value: str,
    *,
    mount_point: str = "secret",
    url: Optional[str] = None,
    namespace: Optional[str] = None,
    token: Optional[str] = None,
    token_file: Optional[str] = None,
    verify: Optional[str | bool] = None,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Save a KV v2 secret to Vault.

    Returns True on success. Auth/transport failure raises ``VaultAuthError``;
    a refused write raises ``RuntimeError``. Neither is a soft ``False`` — a
    caller that is told ``False`` cannot tell "already there" from "silently
    dropped", and a dropped secret is how credentials end up quietly missing.
    """
    log = logger or LOGGER

    hvac_mod = _ensure_hvac()

    url = url or os.environ.get("VAULT_ADDR")
    if not url:
        raise VaultAuthError(
            "VIBE Rule 164 VIOLATION: VAULT_ADDR is not set. Point it at the "
            "running Vault's API address (topology, not a credential)."
        )
    namespace = namespace or os.environ.get("VAULT_NAMESPACE")
    token = _resolve_vault_token(token=token, token_file=token_file)

    if verify is None:
        if os.environ.get("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = os.environ.get("VAULT_CA_CERT") or True
    else:
        verify_value = _coerce_verify(verify)

    client = hvac_mod.Client(url=url, token=token, namespace=namespace, verify=verify_value)

    try:
        # KV v2 stores ONE map per path and a write REPLACES it. Writing
        # {key: value} alone would silently destroy every other key already
        # stored alongside it at that path. Read-modify-write the whole map.
        try:
            existing = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=mount_point
            )
            document = dict(
                ((existing.get("data") or {}).get("data") or {})
                if isinstance(existing, dict)
                else {}
            )
        except Exception as exc:
            if type(exc).__name__ not in {"InvalidPath", "NotFound"}:
                raise
            document = {}

        document[key] = value
        client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=document,
            mount_point=mount_point,
        )
        log.debug("Vault secret saved", extra={"path": path, "key": key})
        # Clear cache so next read gets fresh value
        load_kv_secret.cache_clear()
        return True
    except Exception as exc:
        raise RuntimeError(
            f"Vault refused the write at {mount_point}/{path} [{key}]: "
            f"{type(exc).__name__}. The value was not logged. A secret that "
            f"fails to save is NOT saved — do not carry on as if it were."
        ) from None


def delete_kv_secret(
    path: str,
    *,
    mount_point: str = "secret",
    url: Optional[str] = None,
    namespace: Optional[str] = None,
    token: Optional[str] = None,
    token_file: Optional[str] = None,
    verify: Optional[str | bool] = None,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Delete a KV v2 secret from Vault.

    Returns True on success. Auth/transport failure raises ``VaultAuthError``.
    """
    log = logger or LOGGER

    hvac_mod = _ensure_hvac()

    url = url or os.environ.get("VAULT_ADDR")
    if not url:
        raise VaultAuthError(
            "VIBE Rule 164 VIOLATION: VAULT_ADDR is not set. Point it at the "
            "running Vault's API address (topology, not a credential)."
        )
    namespace = namespace or os.environ.get("VAULT_NAMESPACE")
    token = _resolve_vault_token(token=token, token_file=token_file)

    if verify is None:
        if os.environ.get("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = os.environ.get("VAULT_CA_CERT") or True
    else:
        verify_value = _coerce_verify(verify)

    client = hvac_mod.Client(url=url, token=token, namespace=namespace, verify=verify_value)

    try:
        client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path,
            mount_point=mount_point,
        )
        log.debug("Vault secret deleted", extra={"path": path})
        load_kv_secret.cache_clear()
        return True
    except Exception as exc:
        raise RuntimeError(
            f"Vault refused the delete at {mount_point}/{path}: "
            f"{type(exc).__name__}. The key was NOT deleted — do not carry on "
            f"as if it were."
        ) from None
