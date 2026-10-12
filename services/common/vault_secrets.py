"""Helpers for retrieving secrets from HashiCorp Vault."""

from __future__ import annotations

import logging
import os
import threading
import time
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


# Token is a FILE PATH into the RAM tmpfs custodian (T0_DIR), never an
# environment variable (VIBE Rule 164). A path is topology; the credential it
# names is not. There is deliberately no ``VAULT_TOKEN`` env read anywhere in
# this module — exporting a token into a shell leaves it in ``ps``, in
# ``/proc/*/environ`` and in every crash dump.
#
# The file is the SCOPED runtime token (``agent_runtime_token``), never the
# root token. F-10: when this lease expires the caller must stop cleanly —
# never widen policy, re-mint as root, or read a backup file.
DEFAULT_TOKEN_FILE_ENV = "VAULT_TOKEN_FILE"
SCOPED_TOKEN_ACCOUNT = "agent_runtime_token"
_ROOT_ACCOUNT_NAMES = frozenset({"vault_root_token", "root_token", "vault_root"})

# ---------------------------------------------------------------------------
# F-22: TTL-bounded secret cache.
#
# ``functools.lru_cache`` never expires. A rotated secret would be served from
# cache forever — the one failure mode a secret store must not have. This
# cache is time-bounded (default 300 s), size-bounded, and thread-safe.
# Set ``VAULT_CACHE_TTL_SECONDS=0`` to disable caching entirely (every read
# hits Vault). An unparseable or negative value is fatal (Rule 91: refuse,
# never guess a cache lifetime).
# ---------------------------------------------------------------------------
DEFAULT_CACHE_TTL_SECONDS = 300.0
CACHE_MAXSIZE = 32

_cache_lock = threading.Lock()
_cache: dict[tuple[Any, ...], tuple[float, Optional[str]]] = {}


def _cache_ttl_seconds() -> float:
    """Return the configured cache TTL in seconds. Fail-closed on garbage."""
    raw = os.environ.get("VAULT_CACHE_TTL_SECONDS", "").strip()
    if not raw:
        return DEFAULT_CACHE_TTL_SECONDS
    try:
        value = float(raw)
    except ValueError:
        raise VaultAuthError(
            f"VAULT_CACHE_TTL_SECONDS must be a number of seconds, got {raw!r}. "
            f"Refusing to guess a cache lifetime (VIBE Rule 91)."
        ) from None
    if value < 0:
        raise VaultAuthError(
            f"VAULT_CACHE_TTL_SECONDS must be >= 0, got {value}. A negative "
            f"TTL is not a policy, it is a defect (VIBE Rule 91)."
        )
    return value


def _cache_get(key: tuple[Any, ...]) -> tuple[bool, Optional[str]]:
    """Return ``(hit, value)``. Expired entries are evicted on access."""
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return False, None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del _cache[key]
            return False, None
        return True, value


def _cache_set(key: tuple[Any, ...], value: Optional[str]) -> None:
    """Store ``value`` with the configured TTL. Evicts oldest when full.

    Never cache an absence (None): a pre-seed / pre-policy read must not pin
    "missing" for the TTL after the key is written (security-reviewer F-cache).
    """
    if value is None:
        return
    ttl = _cache_ttl_seconds()
    if ttl <= 0:
        return
    with _cache_lock:
        if len(_cache) >= CACHE_MAXSIZE:
            oldest = min(_cache, key=lambda k: _cache[k][0])
            del _cache[oldest]
        _cache[key] = (time.monotonic() + ttl, value)


def refresh_cached_secrets() -> None:
    """Clear every cached Vault read.

    Called after a write/delete so a rotated secret is visible immediately,
    and available as the production/ops refresh hook.
    """
    with _cache_lock:
        _cache.clear()


def _resolve_vault_token(*, token: Optional[str], token_file: Optional[str]) -> str:
    """Return the Vault token, or raise ``VaultAuthError``.

    Resolution order:

    1. ``token`` argument — only what a caller read from its own secret store
    2. ``token_file`` argument (explicit path)
    3. ``T0_DIR`` RAM tmpfs custodian account ``agent_runtime_token``
    4. ``VAULT_TOKEN_FILE`` environment variable — a PATH, not a credential

    A root token is refused on every path (R-SEC-01 / F-10). A missing,
    unreadable or empty token is fatal. It is never treated as "no secrets
    available".
    """
    if token:
        return token

    candidates: list[tuple[str, Optional[str]]] = [
        ("token_file argument", token_file),
        (
            "T0_DIR custodian",
            (
                str(Path(os.environ["T0_DIR"]) / SCOPED_TOKEN_ACCOUNT)
                if os.environ.get("T0_DIR")
                else None
            ),
        ),
        (DEFAULT_TOKEN_FILE_ENV, os.environ.get(DEFAULT_TOKEN_FILE_ENV)),
    ]
    for source, path in candidates:
        if not path:
            continue
        name = Path(path).name
        if name in _ROOT_ACCOUNT_NAMES:
            raise VaultAuthError(
                f"R-SEC-01 / SOMA-STD-BOOTSTRAP-001 F-10: refusing to use "
                f"{name!r} named by {source} at {path!r}. Long-running app and "
                f"test processes hold only the scoped TTL token "
                f"({SCOPED_TOKEN_ACCOUNT}) from the RAM tmpfs custodian. Root "
                f"is for unseal and policy one-shots only — never mounted, "
                f"never a backup file."
            )
        try:
            resolved = Path(path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise VaultAuthError(
                f"VIBE Rule 164: cannot read the scoped Vault token file "
                f"named by {source} at {path!r}: {exc.strerror or exc}. The "
                f"token is delivered via the RAM tmpfs custodian (T0_DIR) — "
                f"fix the path or the file's permissions (0600); it is never "
                f"read from the environment and never from a repo file."
            ) from None
        if resolved:
            return resolved
        raise VaultAuthError(
            f"VIBE Rule 164: the Vault token file named by "
            f"{source} at {path!r} is empty. An empty token is not a valid "
            f"credential and must not be treated as 'no secrets'."
        )

    raise VaultAuthError(
        f"VIBE Rule 164: no scoped Vault token available. Point "
        f"{DEFAULT_TOKEN_FILE_ENV} at the T0_DIR custodian account "
        f"{SCOPED_TOKEN_ACCOUNT} (compose: /run/t0/agent_runtime_token, "
        f"minted by vault_scoped_tokens.py). Never vault_root_token and never "
        f"a file under the repo. The token is not taken from the environment "
        f"and there is no fallback — without it Vault cannot be read at all, "
        f"which is not the same as a secret being absent. On lease expiry "
        f"(F-10) stop cleanly; do not re-mint as root or read a backup file."
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

    Results are cached with a TTL (F-22, default 300 s) per unique
    configuration to avoid repeated round-trips while still honouring
    rotation. Set ``VAULT_CACHE_TTL_SECONDS=0`` to force a live read.
    """

    log = logger or LOGGER

    if not path:
        return None

    cache_key = (
        path,
        key,
        mount_point,
        url,
        namespace,
        token,
        token_file,
        verify,
    )
    hit, cached = _cache_get(cache_key)
    if hit:
        return cached

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
            _cache_set(cache_key, None)
            return None
        # F-11: a policy denial is NOT a missing secret. Vault answered 403;
        # fail closed naming the path so the operator can fix the grant.
        # Never omit the secret and start anyway.
        status = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "response", None), "status_code", None
        )
        if exc_name in {"Forbidden", "InvalidToken", "Unauthorized"} or status in (401, 403):
            raise VaultAuthError(
                f"SOMA-STD-BOOTSTRAP-001 F-11: policy denied read of "
                f"{mount_point}/{path} (key={key}) from Vault at {url} "
                f"[{exc_name}]. The service token is expired or lacks this "
                f"path. Stop cleanly (F-10) — do not widen policy, re-mint as "
                f"root, omit the secret, or fall back to a backup file."
            ) from None
        raise VaultAuthError(
            f"VIBE Rule 164 VIOLATION: cannot read {mount_point}/{path} from "
            f"Vault at {url}: {exc_name}. The secret's presence is unknown, so "
            f"this is not a missing key. Bring Vault up and unsealed, and check "
            f"the scoped token file — there is no local copy to fall back on."
        ) from None

    data = response.get("data", {}) if isinstance(response, dict) else {}
    nested = data.get("data") if isinstance(data, dict) else None
    if isinstance(nested, dict):
        value = nested.get(key)
        if value is not None:
            result = str(value)
            _cache_set(cache_key, result)
            return result
    else:
        log.warning(
            "Unexpected Vault response payload",
            extra={"path": path, "payload_type": type(response).__name__},
        )
    log.warning(
        "Secret key missing in Vault response",
        extra={"path": path, "key": key, "mount_point": mount_point},
    )
    _cache_set(cache_key, None)
    return None


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
        refresh_cached_secrets()
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
    key: Optional[str] = None,
    mount_point: str = "secret",
    url: Optional[str] = None,
    namespace: Optional[str] = None,
    token: Optional[str] = None,
    token_file: Optional[str] = None,
    verify: Optional[str | bool] = None,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Delete a secret, or one key of a secret, from Vault.

    ``save_kv_secret`` writes a *key into* the document at ``path``. Without a
    matching key-level delete, the two operations address different places:
    saving ``minio_access_key`` puts it in ``agent/credentials``, while a bare
    delete of ``agent/credentials/minio_access_key`` removes a document that
    was never written. ``delete_credential`` used to do exactly that, return
    ``True``, and leave the credential readable — a revocation that does not
    revoke.

    Args:
        path: the KV v2 document path.
        key: when given, remove this key from the document at ``path`` and
            leave the rest of the document alone. When omitted, delete the
            whole document at ``path`` including all versions.

    Returns:
        True on success. Auth/transport failure raises ``VaultAuthError``.
        A refused write raises ``RuntimeError`` — never a soft ``False``.

    Note:
        A key-level delete rewrites the live document without that key. Vault
        KV v2 keeps prior versions of the document, so an old value may still
        be recoverable from history until those versions are destroyed. That
        is Vault's versioning model, not a fallback in this code; destroying
        versions is a separate, deliberate operation because it affects every
        key that shares the document.
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
        if key is None:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point,
            )
            log.debug("Vault secret deleted", extra={"path": path})
        else:
            # Same read-modify-write as save_kv_secret: KV v2 stores ONE map
            # per path and a write REPLACES it, so dropping a key means
            # rewriting the document without it.
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

            if key not in document:
                # Nothing to remove. Still true — the key is not there.
                log.debug(
                    "Vault key already absent",
                    extra={"path": path, "key": key},
                )
                refresh_cached_secrets()
                return True

            del document[key]
            client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=document,
                mount_point=mount_point,
            )
            log.debug("Vault secret key deleted", extra={"path": path, "key": key})

        refresh_cached_secrets()
        return True
    except Exception as exc:
        raise RuntimeError(
            f"Vault refused the delete at {mount_point}/{path}"
            f"{'' if key is None else f' [{key}]'}: "
            f"{type(exc).__name__}. The key was NOT deleted — do not carry on "
            f"as if it were."
        ) from None
