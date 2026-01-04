"""LLM exceptions - migrated from models.py."""


class LLMNotConfiguredError(RuntimeError):
    """Raised when LLM is not properly configured for production use."""

    pass
