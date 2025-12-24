"""Secret manager adapter wrapping SecretManager.

This adapter implements SecretManagerPort by delegating ALL operations
to the existing production SecretManager implementation.
"""

from typing import List, Optional

from services.common.secret_manager import SecretManager


class SecretManagerAdapter(SecretManagerPort):
    """Implements SecretManagerPort using existing SecretManager.

    Delegates ALL operations to services.common.secret_manager.SecretManager.
    """

    def __init__(self, manager: Optional[SecretManager] = None):
        """Initialize adapter with existing manager or create new one.

        Args:
            manager: Existing SecretManager instance (preferred)
        """
        self._manager = manager or SecretManager()

    async def set_provider_key(self, provider: str, api_key: str) -> None:
        await self._manager.set_provider_key(provider, api_key)

    async def get_provider_key(self, provider: str) -> Optional[str]:
        return await self._manager.get_provider_key(provider)

    async def delete_provider_key(self, provider: str) -> None:
        await self._manager.delete_provider_key(provider)

    async def list_providers(self) -> List[str]:
        return await self._manager.list_providers()

    async def set_internal_token(self, token: str) -> None:
        await self._manager.set_internal_token(token)

    async def get_internal_token(self) -> Optional[str]:
        return await self._manager.get_internal_token()

    async def has_provider_key(self, provider: str) -> bool:
        return await self._manager.has_provider_key(provider)

    async def has_internal_token(self) -> bool:
        return await self._manager.has_internal_token()
