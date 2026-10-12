"""Redaction vocabulary for log output.

This is NOT a secret store. Secrets live in Vault (VIBE Rule 164) and are
read through ``services.common.unified_secret_manager``. This module's only
job is to know which string values must be masked before anything reaches a
log or a print — its one consumer is ``admin.core.helpers.print_style``.

There is no secrets file. There is no ``tmp/secrets.env``. There is no
``SECRETS_DIR``. The file-backed store is deleted; values for masking are
loaded from Vault only.
"""

from __future__ import annotations

import re
import threading
from typing import Dict, List, Optional, Set

# Alias-based placeholder format §§secret(KEY)
ALIAS_PATTERN = r"§§secret\(([A-Za-z_][A-Za-z0-9_]*)\)"


def alias_for_key(key: str, placeholder: str = "§§secret({key})") -> str:
    key = key.upper()
    return placeholder.format(key=key)


class StreamingSecretsFilter:
    """Stateful streaming filter that masks secrets on the fly.

    - Replaces full secret values with placeholders §§secret(KEY) when detected.
    - Holds the longest suffix of the current buffer that matches any secret prefix
      (with minimum trigger length of 3) to avoid leaking partial secrets across chunks.
    - On finalize(), any unresolved partial is masked with '***'.
    """

    def __init__(self, key_to_value: Dict[str, str], min_trigger: int = 3):
        self.min_trigger = max(1, int(min_trigger))
        self.value_to_key: Dict[str, str] = {
            v: k for k, v in key_to_value.items() if isinstance(v, str) and v
        }
        self.secret_values: List[str] = [v for v in self.value_to_key.keys() if v]
        self.prefixes: Set[str] = set()
        for v in self.secret_values:
            for i in range(self.min_trigger, len(v) + 1):
                self.prefixes.add(v[:i])
        self.max_len: int = max((len(v) for v in self.secret_values), default=0)
        self.pending: str = ""

    def _replace_full_values(self, text: str) -> str:
        for val in sorted(self.secret_values, key=len, reverse=True):
            if not val:
                continue
            key = self.value_to_key.get(val, "")
            if key:
                text = text.replace(val, alias_for_key(key))
        return text

    def _longest_suffix_prefix(self, text: str) -> int:
        max_check = min(len(text), self.max_len)
        for length in range(max_check, self.min_trigger - 1, -1):
            suffix = text[-length:]
            if suffix in self.prefixes:
                return length
        return 0

    def process_chunk(self, chunk: str) -> str:
        if not chunk:
            return ""
        self.pending += chunk
        self.pending = self._replace_full_values(self.pending)
        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            emit = self.pending[:-hold_len]
            self.pending = self.pending[-hold_len:]
        else:
            emit = self.pending
            self.pending = ""
        return emit

    def finalize(self) -> str:
        if not self.pending:
            return ""
        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            safe = self.pending[:-hold_len]
            result = safe + "***"
        else:
            result = self.pending
        self.pending = ""
        return result


# Logical credential names the app reads via UnifiedSecretManager.get_credential().
# Keep in sync with infra/standalone/init_vault.py CREDENTIAL_KEYS.
_CREDENTIAL_KEYS = (
    "django_secret_key",
    "postgres_password",
    "test_db_password",
    "soma_api_token",
    "somabrain_memory_http_token",
    "somabrain_jwt_secret",
    "keycloak_client_secret",
    "keycloak_admin_password",
    "minio_access_key",
    "minio_secret_key",
    "supervisor_http_pass",
)

_API_KEY_PROVIDERS = ("groq", "openai", "elevenlabs", "anthropic")


class SecretsManager:
    """Vault-backed redaction vocabulary. Never reads or writes a secrets file."""

    PLACEHOLDER_PATTERN = ALIAS_PATTERN
    MASK_VALUE = "***"

    _instance: Optional["SecretsManager"] = None
    _secrets_cache: Optional[Dict[str, str]] = None

    @classmethod
    def get_instance(cls) -> "SecretsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._lock = threading.RLock()

    def load_secrets(self) -> Dict[str, str]:
        """Load redaction values from Vault only. No file fallback."""
        with self._lock:
            if self._secrets_cache is not None:
                return self._secrets_cache

            secrets: Dict[str, str] = {}
            try:
                from services.common.unified_secret_manager import get_secret_manager

                mgr = get_secret_manager()
                for key in _CREDENTIAL_KEYS:
                    value = mgr.get_credential(key)
                    if value:
                        secrets[key.upper()] = value
                for provider in _API_KEY_PROVIDERS:
                    value = mgr.get_provider_key(provider)
                    if value:
                        secrets[f"{provider.upper()}_API_KEY"] = value
            except Exception:
                # Vault down: mask nothing rather than fall back to a file.
                secrets = {}

            self._secrets_cache = secrets
            return secrets

    def get_keys(self) -> List[str]:
        return list(self.load_secrets().keys())

    def create_streaming_filter(self) -> "StreamingSecretsFilter":
        return StreamingSecretsFilter(self.load_secrets())

    def mask_values(
        self, text: str, min_length: int = 4, placeholder: str = "§§secret({key})"
    ) -> str:
        """Replace actual secret values with placeholders in text."""
        if not text:
            return text

        secrets = self.load_secrets()
        result = text
        for key, value in sorted(secrets.items(), key=lambda x: len(x[1]), reverse=True):
            if value and len(value.strip()) >= min_length:
                result = result.replace(value, alias_for_key(key, placeholder))
        return result

    def clear_cache(self):
        with self._lock:
            self._secrets_cache = None
