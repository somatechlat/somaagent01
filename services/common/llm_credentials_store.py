"""Compatibility shim for LLM credential storage.

The original implementation stored encrypted provider keys directly using its own
Fernet handling.  For the new architecture all secret handling is centralized
in :class:`services.common.secret_manager.SecretManager`.  To avoid a massive
refactor across the codebase we keep this module as a thin wrapper that proxies
calls to the new manager.  New code should import :class:`SecretManager`
directly; this shim exists solely for backward compatibility during the
migration sprint.
"""

from __future__ import annotations

import warnings
from typing import Optional, List

from .secret_manager import SecretManager

# A singleton instance – the underlying ``SecretManager`` caches Redis and
# Fernet, so constructing it once per process is cheap.
# Initialise a singleton SecretManager. The manager lazily creates the Fernet
# instance, so importing this shim does not require the encryption key to be
# present – useful for test environments.
_manager = SecretManager()


class LlmCredentialsStore:
    """Legacy API that forwards to :class:`SecretManager`.

    The public methods mirror the original async interface so existing callers
    continue to work unchanged.  Each method emits a ``DeprecationWarning`` to
    encourage migration to the new manager.
    """

    def __init__(self, *_, **__) -> None:
        """Compatibility constructor.

        The original class accepted ``redis_url`` and ``namespace`` arguments.
        The shim ignores them because the underlying :class:`SecretManager`
        handles connection details internally. Accepting arbitrary ``*args`` and
        ``**kwargs`` ensures existing call sites remain functional.
        """
        # No state needed; the singleton manager is used for all operations.
        return None

    async def set(self, provider: str, secret: str) -> None:
        warnings.warn(
            "LlmCredentialsStore.set is deprecated – use SecretManager.set_provider_key",
            DeprecationWarning,
            stacklevel=2,
        )
        await _manager.set_provider_key(provider, secret)

    async def get(self, provider: str) -> Optional[str]:
        warnings.warn(
            "LlmCredentialsStore.get is deprecated – use SecretManager.get_provider_key",
            DeprecationWarning,
            stacklevel=2,
        )
        return await _manager.get_provider_key(provider)

    async def delete(self, provider: str) -> None:
        warnings.warn(
            "LlmCredentialsStore.delete is deprecated – use SecretManager.delete_provider_key",
            DeprecationWarning,
            stacklevel=2,
        )
        await _manager.delete_provider_key(provider)

    async def list_providers(self) -> List[str]:
        warnings.warn(
            "LlmCredentialsStore.list_providers is deprecated – use SecretManager.list_providers",
            DeprecationWarning,
            stacklevel=2,
        )
        return await _manager.list_providers()

    async def has(self, provider: str) -> bool:
        warnings.warn(
            "LlmCredentialsStore.has is deprecated – use SecretManager.has_provider_key",
            DeprecationWarning,
            stacklevel=2,
        )
        return await _manager.has_provider_key(provider)
