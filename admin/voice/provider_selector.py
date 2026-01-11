"""Factory for selecting the appropriate voice provider implementation.

Selects and instantiates either :class:`OpenAIClient` or :class:`LocalClient`
based on the ``voice.provider`` field from the global configuration model
(:class:`src.core.config.models.VoiceConfig`). All providers implement the
:class:`_BaseClient` protocol for type safety.

All errors are expressed via :class:`ProviderNotSupportedError` defined in
``src.voice.exceptions``.
"""

from __future__ import annotations

from typing import AsyncGenerator, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from admin.core.helpers.config import Config

from .exceptions import ProviderNotSupportedError

# The concrete client classes are defined in separate modules.  Importing them
# lazily avoids unnecessary heavy dependencies (e.g. websockets) when the
# provider is not selected.


@runtime_checkable
class _BaseClient(Protocol):
    """Common protocol shared by all provider clients.

    The concrete clients must implement an async ``process`` method that accepts
    an async generator of raw PCM bytes and returns an async generator yielding
    response objects (the exact type is provider‑specific).  This protocol is
    deliberately minimal to keep the provider contract focused and stable.
    """

    async def process(
        self,
        audio_stream: "AsyncGenerator[bytes, None]"
        """Execute process.

            Args:
                audio_stream: The audio_stream.
            """,
    ) -> "AsyncGenerator[object, None]": ...


def get_provider_client(config: Config) -> _BaseClient:
    """Return an instantiated provider client based on the global config.

    Parameters
    ----------
    config:
        The full application configuration.  The function reads
        ``config.voice.provider`` and constructs the matching client.

    Raises
    ------
    ProviderNotSupportedError
        If the ``provider`` value is not ``"openai"`` or ``"local"``.
    """

    provider = config.voice.provider
    if provider == "openai":
        # Local import to keep optional heavy deps out of the import path.
        from .openai_client import OpenAIClient

        return OpenAIClient(config.voice.openai)
    if provider == "local":
        from .local_client import LocalClient

        return LocalClient(config.voice.local)
    raise ProviderNotSupportedError(provider)
