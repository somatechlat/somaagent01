"""Custom exceptions for the voice subsystem.

All exceptions inherit from :class:`VoiceError`, which itself derives from
``Exception``.  This hierarchy makes it easy for callers to catch a generic
voice‑related error while still being able to handle specific cases such as a
processing failure or an unsupported provider.

These classes are deliberately tiny – they carry no hidden state – in order to
comply with the
behaviour).  Each exception has an informative docstring so that the generated
documentation is accurate (
"""

from __future__ import annotations


class VoiceError(Exception):
    """Base class for all voice‑subsystem errors.

    Subclass this for more specific error conditions.  The base class does not
    implement any custom behaviour – it exists solely for type safety and
    documentation purposes.
    """


class VoiceProcessingError(VoiceError):
    """Raised when an external binary (e.g., ``kokoro-cli`` or ``whisper-cli``)
    exits with a non‑zero status.

    The exception stores the command that was executed and the exit code to aid
    debugging.  No sensitive data (such as audio payloads) is included, satisfying
    the security requirement.
    """

    def __init__(self, command: str, exit_code: int, stderr: str | None = None) -> None:
        """Initialize the instance."""

        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"Command '{command}' failed with exit code {exit_code}")


class ProviderNotSupportedError(VoiceError):
    """Raised when the configuration requests a provider that is not available.

    This typically means the binary verification step failed or the required
    environment variable (``OPENAI_API_KEY`` for the OpenAI provider) is missing.
    """

    def __init__(self, provider: str) -> None:
        """Initialize the instance."""

        super().__init__(f"Provider '{provider}' is not supported or not configured")
