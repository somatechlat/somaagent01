"""Secret manager port for domain layer.

Port interface for secret storage operations.
"""

from __future__ import annotations

from typing import Optional, Protocol


class SecretManagerPort(Protocol):
    """Port interface for secret management."""

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key."""
        ...

    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret. Returns True on success."""
        ...

    def delete_secret(self, key: str) -> bool:
        """Delete a secret. Returns True on success."""
        ...
