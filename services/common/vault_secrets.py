"""Helpers for retrieving secrets from HashiCorp Vault."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)

try:
    import hvac  # type: ignore
except ImportError:
    raise ImportError(
        "hvac library is required for Vault integration. Install with: pip install hvac"
    )


def _ensure_hvac() -> Any:
    return hvac


def _resolve_vault_token(*, token: Optional[str], token_file: Optional[str]) -> Optional[str]:
    if token:
        return token
    if token_file:
        try:
            return Path(token_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            LOGGER.error(
                "Failed to read Vault token file",
                extra={"token_file": token_file, "error": str(exc)},
            )
            return None
    return None


def _coerce_verify(verify: Optional[str | bool]) -> str | bool:
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

    Returns ``None`` when the secret cannot be retrieved or the key is missing.
    Results are cached per unique configuration to avoid repeated round-trips.
    """

    log = logger or LOGGER

    if not path:
        return None

    try:
        hvac_mod = _ensure_hvac()
    except RuntimeError as exc:
        log.warning("Vault integration unavailable", extra={"reason": str(exc)})
        return None

    url = url or cfg.env("VAULT_ADDR")
    namespace = namespace or cfg.env("VAULT_NAMESPACE")
    token = _resolve_vault_token(
        token=token or cfg.env("VAULT_TOKEN"),
        token_file=token_file or cfg.env("VAULT_TOKEN_FILE"),
    )
    if not token:
        log.error("Vault token missing; cannot authenticate", extra={"path": path})
        return None

    if verify is None:
        if cfg.env("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = cfg.env("VAULT_CA_CERT") or True
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
        log.error(
            "Failed to read secret from Vault",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                "path": path,
                "mount_point": mount_point,
            },
        )
        return None

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

    Returns True if successful, False otherwise.
    """
    log = logger or LOGGER

    try:
        hvac_mod = _ensure_hvac()
    except RuntimeError as exc:
        log.warning("Vault integration unavailable", extra={"reason": str(exc)})
        return False

    url = url or cfg.env("VAULT_ADDR")
    namespace = namespace or cfg.env("VAULT_NAMESPACE")
    token = _resolve_vault_token(
        token=token or cfg.env("VAULT_TOKEN"),
        token_file=token_file or cfg.env("VAULT_TOKEN_FILE"),
    )
    if not token:
        log.error("Vault token missing; cannot authenticate", extra={"path": path})
        return False

    if verify is None:
        if cfg.env("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = cfg.env("VAULT_CA_CERT") or True
    else:
        verify_value = _coerce_verify(verify)

    client = hvac_mod.Client(url=url, token=token, namespace=namespace, verify=verify_value)

    try:
        client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={key: value},
            mount_point=mount_point,
        )
        log.debug("Vault secret saved", extra={"path": path, "key": key})
        # Clear cache so next read gets fresh value
        load_kv_secret.cache_clear()
        return True
    except Exception as exc:
        log.error(
            "Failed to save secret to Vault",
            extra={"error": str(exc), "path": path, "key": key, "mount_point": mount_point},
        )
        return False


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

    Returns True if successful, False otherwise.
    """
    log = logger or LOGGER

    try:
        hvac_mod = _ensure_hvac()
    except RuntimeError as exc:
        log.warning("Vault integration unavailable", extra={"reason": str(exc)})
        return False

    url = url or cfg.env("VAULT_ADDR")
    namespace = namespace or cfg.env("VAULT_NAMESPACE")
    token = _resolve_vault_token(
        token=token or cfg.env("VAULT_TOKEN"),
        token_file=token_file or cfg.env("VAULT_TOKEN_FILE"),
    )
    if not token:
        log.error("Vault token missing; cannot authenticate", extra={"path": path})
        return False

    if verify is None:
        if cfg.env("VAULT_SKIP_VERIFY", "false").lower() in {"1", "true", "yes", "on"}:
            verify_value: str | bool = False
        else:
            verify_value = cfg.env("VAULT_CA_CERT") or True
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
        log.error(
            "Failed to delete secret from Vault",
            extra={"error": str(exc), "path": path, "mount_point": mount_point},
        )
        return False
