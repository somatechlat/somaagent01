"""Compatibility shim for legacy ``LlmCredentialsStore``.

The original codebase referenced a ``LlmCredentialsStore`` class that was
responsible for storing LLM provider API keys.  During the refactor the
implementation was moved to :pymod:`services.common.secret_manager`
under the name :class:`SecretManager`.  Several modules – e.g.
``services/common/settings_registry.py`` and ``integrations/repositories.py`` –
still import ``LlmCredentialsStore`` directly, causing import errors during
test collection.

This file provides a thin wrapper that mirrors the old public API while
delegating to :class:`SecretManager`.  Only the methods required by the test
suite are implemented:

* ``list_providers`` – return a list of stored provider names.
* ``get_provider_key`` – retrieve a stored API key.
* ``set_provider_key`` – store a new API key.
* ``delete_provider_key`` – remove a stored key.

All methods are ``async`` to match the original interface.  The wrapper is
lightweight and does not introduce any new dependencies, preserving the
single‑source‑of‑truth principle of the VIBE coding rules.
"""

from __future__ import annotations

from typing import List, Optional

from services.common.secret_manager import SecretManager

__all__ = ["LlmCredentialsStore"]


class LlmCredentialsStore:
    """Legacy façade delegating to :class:`services.common.secret_manager.SecretManager`.

    The class is deliberately minimal – it only implements the methods used in
    the current codebase and test suite.  Each call creates a fresh
    ``SecretManager`` instance; the underlying manager caches the Redis client
    and Fernet key, so the overhead is negligible.
    """

    def __init__(self) -> None:
        self._manager = SecretManager()

    async def list_providers(self) -> List[str]:
        """Return the list of provider names that have stored keys."""
        return await self._manager.list_providers()

    async def get_provider_key(self, provider: str) -> Optional[str]:
        """Retrieve the API key for *provider* if it exists."""
        return await self._manager.get_provider_key(provider)

    async def set_provider_key(self, provider: str, api_key: str) -> None:
        """Store *api_key* for *provider*.

        This mirrors the original ``set_provider_key`` signature used by the
        gateway when handling credential updates.
        """
        await self._manager.set_provider_key(provider, api_key)

    async def delete_provider_key(self, provider: str) -> None:
        """Delete the stored key for *provider* if present."""
        await self._manager.delete_provider_key(provider)

    # Backwards-compatibility aliases (legacy code expects `.get` / `.set` / `.delete`)
    async def get(self, provider: str):
        return await self.get_provider_key(provider)

    async def set(self, provider: str, api_key: str):
        await self.set_provider_key(provider, api_key)

    async def delete(self, provider: str):
        await self.delete_provider_key(provider)
