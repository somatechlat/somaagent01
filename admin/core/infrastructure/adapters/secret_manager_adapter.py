"""Secret manager adapter using UnifiedSecretManager (HashiCorp Vault).

Implements SecretManagerPort from the domain layer.
"""

from __future__ import annotations

from typing import Optional

from admin.core.domain.ports.adapters import SecretManagerPort
from services.common.unified_secret_manager import get_secret_manager


class SecretManagerAdapter(SecretManagerPort):
    """Vault-based secret manager adapter."""

    def __init__(self) -> None:
        """Initialize adapter with UnifiedSecretManager."""
        self._manager = get_secret_manager()

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a credential from Vault."""
        return self._manager.get_credential(key)

    def set_secret(self, key: str, value: str) -> bool:
        """Store a credential in Vault."""
        return self._manager.set_credential(key, value)

    def delete_secret(self, key: str) -> bool:
        """Delete a credential from Vault."""
        return self._manager.delete_credential(key)
