"""Unified secret management using HashiCorp Vault.

Single source of truth for all secrets:
- API keys → Vault at secret/agent/api_keys/{provider}
- Credentials → Vault at secret/agent/credentials/{key}

No Redis, no .env files.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from admin.common.messages import ErrorCode, get_message
from services.common.vault_secrets import (
    delete_kv_secret,
    load_kv_secret,
    save_kv_secret,
)

LOGGER = logging.getLogger(__name__)

# Vault path configuration
VAULT_API_KEYS_PATH = "agent/api_keys"
VAULT_CREDENTIALS_PATH = "agent/credentials"


class UnifiedSecretManager:
    """Vault-based secret storage."""

    def __init__(self) -> None:
        """Initialize the instance."""

        self._vault_addr = os.environ.get("VAULT_ADDR")
        deployment_mode = os.environ.get("SA01_DEPLOYMENT_MODE", "DEV").upper()
        is_prod = deployment_mode in ("PROD", "PRODUCTION", "STANDALONE")

        if not self._vault_addr:
            if is_prod:
                raise RuntimeError(
                    f"VIBE Rule 164 VIOLATION: {get_message(ErrorCode.VAULT_ADDR_MISSING)}"
                )
            LOGGER.warning(
                "VAULT_ADDR not configured - secrets will not be available. "
                "In production, this is a FATAL error."
            )
            return

        if is_prod and not self._check_vault_reachable():
            raise RuntimeError(
                f"VIBE Rule 164 VIOLATION: {get_message(ErrorCode.VAULT_UNREACHABLE, addr=self._vault_addr)}"
            )

    def _check_vault_reachable(self) -> bool:
        """Check if Vault server is responding."""
        if not self._vault_addr:
            return False
        try:
            import urllib.request

            req = urllib.request.Request(
                f"{self._vault_addr}/v1/sys/health", method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                # Vault returns 200, 429, 472, 473 for various healthy/reachable states
                return resp.status in (200, 429, 472, 473)
        except Exception as exc:
            LOGGER.warning("Vault health check failed: %s", exc)
            return False

    def _is_available(self) -> bool:
        """Check if Vault is configured."""
        return bool(self._vault_addr)

    # -------------------------------------------------------------------------
    # API Keys (LLM providers)
    # -------------------------------------------------------------------------
    def get_provider_key(self, provider: str) -> Optional[str]:
        """Get API key for LLM provider from Vault."""
        if not self._is_available():
            return None
        return load_kv_secret(
            path=VAULT_API_KEYS_PATH,
            key=f"{provider.lower()}_api_key",
            logger=LOGGER,
        )

    def set_provider_key(self, provider: str, api_key: str) -> bool:
        """Save API key for LLM provider to Vault."""
        if not self._is_available():
            LOGGER.error("Cannot save provider key - Vault not configured")
            return False
        return save_kv_secret(
            path=VAULT_API_KEYS_PATH,
            key=f"{provider.lower()}_api_key",
            value=api_key,
            logger=LOGGER,
        )

    def delete_provider_key(self, provider: str) -> bool:
        """Delete API key for LLM provider from Vault."""
        if not self._is_available():
            return False
        return delete_kv_secret(
            path=f"{VAULT_API_KEYS_PATH}/{provider.lower()}",
            logger=LOGGER,
        )

    def list_providers(self) -> List[str]:
        """List providers with stored API keys."""
        if not self._is_available():
            return []
        # Check common providers
        providers = ["openai", "groq", "anthropic", "openrouter", "ollama", "fireworks"]
        return [p for p in providers if self.get_provider_key(p)]

    # -------------------------------------------------------------------------
    # Credentials (auth passwords, tokens)
    # -------------------------------------------------------------------------
    def get_credential(self, key: str) -> Optional[str]:
        """Get credential from Vault."""
        if not self._is_available():
            return None
        return load_kv_secret(
            path=VAULT_CREDENTIALS_PATH,
            key=key,
            logger=LOGGER,
        )

    def set_credential(self, key: str, value: str) -> bool:
        """Save credential to Vault."""
        if not self._is_available():
            LOGGER.error("Cannot save credential - Vault not configured")
            return False
        return save_kv_secret(
            path=VAULT_CREDENTIALS_PATH,
            key=key,
            value=value,
            logger=LOGGER,
        )

    def delete_credential(self, key: str) -> bool:
        """Delete credential from Vault."""
        if not self._is_available():
            return False
        return delete_kv_secret(
            path=f"{VAULT_CREDENTIALS_PATH}/{key}",
            logger=LOGGER,
        )


# Singleton
_manager: Optional[UnifiedSecretManager] = None


def get_secret_manager() -> UnifiedSecretManager:
    """Get singleton UnifiedSecretManager instance."""
    global _manager
    if _manager is None:
        _manager = UnifiedSecretManager()
    return _manager
