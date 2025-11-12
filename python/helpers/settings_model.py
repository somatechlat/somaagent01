"""Pydantic ``BaseSettings`` model for Agent Zero configuration.

The original implementation used a large ``TypedDict`` (see ``settings.py``).
That approach works but provides no validation, default handling, or
environment‑variable integration.  This file introduces a ``SettingsModel``
subclass of ``pydantic.BaseSettings`` that mirrors the keys of the original
TypedDict while keeping backward‑compatible attribute access.

Only a representative subset of fields is defined explicitly – the rest are
captured via ``extra = "allow"`` so that the model can still load the full JSON
settings file without having to list every single key.  This makes the change
non‑breaking for existing code that accesses settings via ``settings["key"]``.

The model is used by ``python/helpers/settings.py`` to validate the JSON file
on load and to provide a ``SettingsModel`` instance that can be used with
attribute access (e.g. ``settings.chat_model_provider``).
"""

from __future__ import annotations

from typing import Any, Dict

from pydantic import ConfigDict

try:
    # pydantic v2+: BaseSettings was moved to pydantic-settings
    from pydantic import Field
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback for older environments
    from pydantic import BaseSettings, Field


class SettingsModel(BaseSettings):
    """Validated settings for the Agent Zero application.

    The fields below cover the most commonly used configuration options.  Any
    additional keys present in the JSON file are accepted (``extra = "allow"``)
    so the model remains compatible with the existing ``TypedDict`` schema.
    """

    # Core version information
    version: str = Field(default="0.0.0", description="Application version")

    # Chat model configuration
    chat_model_provider: str = Field(
        default="openai", description="Provider for the main chat model"
    )
    chat_model_name: str = Field(
        default="gpt-4o-mini", description="Model name for the main chat model"
    )
    chat_model_api_base: str | None = Field(
        default=None, description="Optional custom API base URL"
    )
    chat_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    chat_model_ctx_length: int = Field(default=8192)
    chat_model_ctx_history: float = Field(default=0.5)
    chat_model_vision: bool = Field(default=False)
    chat_model_rl_requests: int = Field(default=0)
    chat_model_rl_input: int = Field(default=0)
    chat_model_rl_output: int = Field(default=0)

    # Utility model configuration (mirrors chat model fields)
    util_model_provider: str = Field(default="openai", description="Provider for utility model")
    util_model_name: str = Field(default="gpt-4o-mini", description="Utility model name")
    util_model_api_base: str | None = Field(default=None)
    util_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    util_model_ctx_length: int = Field(default=4096)
    util_model_ctx_input: float = Field(default=0.5)
    util_model_rl_requests: int = Field(default=0)
    util_model_rl_input: int = Field(default=0)
    util_model_rl_output: int = Field(default=0)

    # Embedding model configuration
    embed_model_provider: str = Field(default="openai")
    embed_model_name: str = Field(default="text-embedding-3-large")
    embed_model_api_base: str | None = Field(default=None)
    embed_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    embed_model_rl_requests: int = Field(default=0)
    embed_model_rl_input: int = Field(default=0)

    # Browser model configuration
    browser_model_provider: str = Field(default="openai")
    browser_model_name: str = Field(default="gpt-4o-mini")
    browser_model_api_base: str | None = Field(default=None)
    browser_model_vision: bool = Field(default=False)
    browser_model_rl_requests: int = Field(default=0)
    browser_model_rl_input: int = Field(default=0)
    browser_model_rl_output: int = Field(default=0)
    browser_model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    browser_http_headers: Dict[str, Any] = Field(default_factory=dict)

    # Authentication / UI login
    auth_login: str = Field(default="admin")
    auth_password: str = Field(default="admin")
    root_password: str | None = Field(default=None)

    # Miscellaneous flags (kept as a generic catch‑all)
    # Enable LLM usage by default in production. The prior codebase sometimes
    # assumes LLMs are available; keep the default 'True' to avoid surprising
    # runtime errors when the settings file is missing or not yet persisted.
    USE_LLM: bool = Field(default=True)

    # Pydantic v2 config: allow unknown keys to keep backward compatibility
    model_config = ConfigDict(extra="allow")

    # Provide dict‑style access for prior code paths.
    def __getitem__(self, item: str) -> Any:  # pragma: no cover
        return getattr(self, item)

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        setattr(self, key, value)
