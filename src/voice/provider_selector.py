"""Factory for selecting the appropriate voice provider implementation.

Voice providers are not yet implemented. This module raises ProviderNotSupportedError
for all provider requests until real implementations are added.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import AsyncGenerator

from src.core.config.models import Config

from .exceptions import ProviderNotSupportedError


@runtime_checkable
class _BaseClient(Protocol):
    """Common protocol shared by all provider clients."""

    async def process(self, audio_stream: "AsyncGenerator[bytes, None]") -> "AsyncGenerator[object, None]":
        ...


def get_provider_client(config: Config) -> _BaseClient:
    """Return an instantiated provider client based on the global config.

    Raises
    ------
    ProviderNotSupportedError
        Voice providers are not yet implemented.
    """
    provider = config.voice.provider
    raise ProviderNotSupportedError(f"Voice provider '{provider}' not implemented")
