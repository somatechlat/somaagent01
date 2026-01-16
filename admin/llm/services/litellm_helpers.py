"""LiteLLM Helpers - Utility functions for LLM operations.

Extracted from litellm_client.py for 650-line compliance.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable, TYPE_CHECKING

import litellm
import openai

from admin.core.helpers.rate_limiter import RateLimiter
from admin.core.helpers.tokens import approximate_tokens

if TYPE_CHECKING:
    from admin.llm.models import ModelConfig

# Module-level state
rate_limiters: dict[str, RateLimiter] = {}
api_keys_round_robin: dict[str, int] = {}
_secret_manager = None

litellm_exceptions = getattr(litellm, "exceptions", None)


def turn_off_logging():
    """Disable LiteLLM verbose logging."""
    os.environ["LITELLM_LOG"] = "ERROR"
    if litellm is not None:
        try:
            litellm.suppress_debug_info = True
        except Exception:
            pass
    for name in logging.Logger.manager.loggerDict:
        if name.lower().startswith("litellm"):
            logging.getLogger(name).setLevel(logging.ERROR)


def _env_flag(name: str, default: bool = True) -> bool:
    """Get boolean flag from environment variable."""
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _json_env(name: str):
    """Get JSON-parsed value from environment variable."""
    import json

    raw = os.environ.get(name)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _get_secret_manager():
    """Get UnifiedSecretManager singleton."""
    global _secret_manager
    if _secret_manager is None:
        from services.common.unified_secret_manager import get_secret_manager

        _secret_manager = get_secret_manager()
    return _secret_manager


def get_api_key(service: str) -> str:
    """Get API key from Vault (single source of truth)."""
    key = _get_secret_manager().get_provider_key(service.lower())
    if not key:
        raise RuntimeError(f"Missing API key for provider '{service}' in secret manager")
    if "," in key:
        api_keys = [k.strip() for k in key.split(",") if k.strip()]
        api_keys_round_robin[service] = api_keys_round_robin.get(service, -1) + 1
        key = api_keys[api_keys_round_robin[service] % len(api_keys)]
    return key


def get_rate_limiter(
    provider: str, name: str, requests: int, input: int, output: int
) -> RateLimiter:
    """Get or create rate limiter for provider/model combination."""
    key = f"{provider}\\{name}"
    rate_limiters[key] = limiter = rate_limiters.get(key, RateLimiter(seconds=60))
    limiter.limits["requests"] = requests or 0
    limiter.limits["input"] = input or 0
    limiter.limits["output"] = output or 0
    return limiter


def _is_transient_litellm_error(exc: Exception) -> bool:
    """Check if exception is transient and retriable."""
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        if status_code in (408, 429, 500, 502, 503, 504):
            return True
        if status_code >= 500:
            return True
        return False

    transient_types = (
        getattr(openai, "APITimeoutError", Exception) if openai is not None else Exception,
        getattr(openai, "APIConnectionError", Exception) if openai is not None else Exception,
        getattr(openai, "RateLimitError", Exception) if openai is not None else Exception,
        getattr(openai, "APIError", Exception) if openai is not None else Exception,
        getattr(openai, "InternalServerError", Exception) if openai is not None else Exception,
        getattr(openai, "APIStatusError", Exception) if openai is not None else Exception,
    )
    litellm_transient = tuple(
        getattr(litellm_exceptions, name)
        for name in (
            "APIConnectionError",
            "ServiceUnavailableError",
            "Timeout",
            "InternalServerError",
            "BadGatewayError",
            "GatewayTimeoutError",
            "RateLimitError",
            "GroqException",
        )
        if hasattr(litellm_exceptions, name)
    )
    return isinstance(exc, transient_types + litellm_transient)


async def apply_rate_limiter(
    model_config: "ModelConfig | None",
    input_text: str,
    rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
):
    """Apply rate limiting for async calls."""
    if not model_config:
        return
    limiter = get_rate_limiter(
        model_config.provider,
        model_config.name,
        model_config.limit_requests,
        model_config.limit_input,
        model_config.limit_output,
    )
    limiter.add(input=approximate_tokens(input_text))
    limiter.add(requests=1)
    await limiter.wait(rate_limiter_callback)
    return limiter


def apply_rate_limiter_sync(
    model_config: "ModelConfig | None",
    input_text: str,
    rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
):
    """Apply rate limiting for sync calls."""
    if not model_config:
        return
    import asyncio

    import nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(apply_rate_limiter(model_config, input_text, rate_limiter_callback))


def _parse_chunk(chunk: Any) -> dict:
    """Parse LLM response chunk into standardized format."""
    from admin.llm.services.litellm_schemas import ChatChunk

    delta = chunk["choices"][0].get("delta", {})
    message = chunk["choices"][0].get("message", {}) or chunk["choices"][0].get(
        "model_extra", {}
    ).get("message", {})
    response_delta = (
        delta.get("content", "") if isinstance(delta, dict) else getattr(delta, "content", "")
    ) or (
        message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
    )
    reasoning_delta = (
        delta.get("reasoning_content", "")
        if isinstance(delta, dict)
        else getattr(delta, "reasoning_content", "")
    )

    return ChatChunk(reasoning_delta=reasoning_delta, response_delta=response_delta)


def _adjust_call_args(provider_name: str, model_name: str, kwargs: dict):
    """Adjust call arguments for specific providers."""
    if provider_name == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://github.com/somatechlat/somaAgent01",
            "X-Title": "SomaAgent01",
        }
    if provider_name == "other":
        provider_name = "openai"
    return provider_name, model_name, kwargs


def _merge_provider_defaults(
    provider_type: str, original_provider: str, kwargs: dict
) -> tuple[str, dict]:
    """Merge provider-specific defaults into kwargs."""
    from admin.core.helpers.providers import get_provider_config

    def _normalize_values(values: dict) -> dict:
        result: dict[str, Any] = {}
        for k, v in values.items():
            if isinstance(v, str):
                try:
                    result[k] = int(v)
                except ValueError:
                    try:
                        result[k] = float(v)
                    except ValueError:
                        result[k] = v
            else:
                result[k] = v
        return result

    provider_name = original_provider
    cfg = get_provider_config(provider_type, original_provider)
    if cfg:
        provider_name = cfg.get("litellm_provider", original_provider).lower()
        extra_kwargs = cfg.get("kwargs") if isinstance(cfg, dict) else None
        if isinstance(extra_kwargs, dict):
            for k, v in extra_kwargs.items():
                kwargs.setdefault(k, v)

    if "api_key" not in kwargs:
        key = get_api_key(original_provider)
        if key and key not in ("None", "NA"):
            kwargs["api_key"] = key

    global_kwargs = _json_env("SA01_LITELLM_GLOBAL_KWARGS")
    if isinstance(global_kwargs, dict):
        for k, v in _normalize_values(global_kwargs).items():
            kwargs.setdefault(k, v)

    return provider_name, kwargs
