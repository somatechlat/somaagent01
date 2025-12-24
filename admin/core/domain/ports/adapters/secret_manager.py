"""Secret manager port interface.

This port defines the contract for encrypted secret storage.
The interface matches the existing SecretManager methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.common.secret_manager.SecretManager
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class SecretManagerPort(ABC):
    """Abstract interface for encrypted secret storage.

    This port wraps the existing SecretManager implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def set_provider_key(self, provider: str, api_key: str) -> None:
        """Store the API key for a given LLM provider.

        Args:
            provider: Provider name (e.g., 'groq', 'openai')
            api_key: The API key to store (will be encrypted)
        """
        ...

    @abstractmethod
    async def get_provider_key(self, provider: str) -> Optional[str]:
        """Get the API key for a given LLM provider.

        Args:
            provider: Provider name

        Returns:
            Decrypted API key or None if not found
        """
        ...

    @abstractmethod
    async def delete_provider_key(self, provider: str) -> None:
        """Delete the API key for a given LLM provider.

        Args:
            provider: Provider name
        """
        ...

    @abstractmethod
    async def list_providers(self) -> List[str]:
        """List all providers that have stored keys.

        Returns:
            List of provider names
        """
        ...

    @abstractmethod
    async def set_internal_token(self, token: str) -> None:
        """Store the internal service-to-service token.

        Args:
            token: The token to store (will be encrypted)
        """
        ...

    @abstractmethod
    async def get_internal_token(self) -> Optional[str]:
        """Get the internal service-to-service token.

        Returns:
            Decrypted token or None if not found
        """
        ...

    @abstractmethod
    async def has_provider_key(self, provider: str) -> bool:
        """Check if a provider key exists.

        Args:
            provider: Provider name

        Returns:
            True if key exists, False otherwise
        """
        ...

    @abstractmethod
    async def has_internal_token(self) -> bool:
        """Check if internal token exists.

        Returns:
            True if token exists, False otherwise
        """
        ...
