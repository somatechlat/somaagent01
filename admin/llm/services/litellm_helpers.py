"""LiteLLM Helpers - Utility functions for LLM operations.

Extracted from litellm_client.py for 650-line compliance.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Awaitable, Callable, TYPE_CHECKING

import litellm
import openai

from admin.core.helpers.tokens import approximate_tokens


# In-memory rate limiter for per-API-key LLM call throttling.
# This is NOT the API endpoint rate limiter (see services.common.rate_limiter).
class _RateLimiter:
    """In-memory rate limiter for LLM API call throttling."""

    def __init__(self, seconds: int = 60, **limits: int):
        self.timeframe = seconds
        self.limits = {
            key: value if isinstance(value, (int, float)) else 0
            for key, value in (limits or {}).items()
        }
        self.values = {key: [] for key in self.limits.keys()}
        self._lock = asyncio.Lock()

    def add(self, **kwargs: int):
        now = time.time()
        for key, value in kwargs.items():
            if key not in self.values:
                self.values[key] = []
            self.values[key].append((now, value))

    async def cleanup(self):
        async with self._lock:
            now = time.time()
            cutoff = now - self.timeframe
            for key in self.values:
                self.values[key] = [(t, v) for t, v in self.values[key] if t > cutoff]

    async def get_total(self, key: str) -> int:
        async with self._lock:
            if key not in self.values:
                return 0
            return sum(value for _, value in self.values[key])

    async def wait(
        self,
        callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
    ):
        while True:
            await self.cleanup()
            should_wait = False
            for key, limit in self.limits.items():
                if limit <= 0:
                    continue
                total = await self.get_total(key)
                if total > limit:
                    if callback:
                        msg = f"Rate limit exceeded for {key} ({total}/{limit}), waiting..."
                        should_wait = not await callback(msg, key, total, limit)
                    else:
                        should_wait = True
                    break
            if not should_wait:
                break
            await asyncio.sleep(1)


RateLimiter = _RateLimiter

if TYPE_CHECKING:
    from admin.llm.models import ModelConfig
    from admin.llm.services.litellm_schemas import ChatChunk

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
    return isinstance(exc, transient_types + litellm_transient)  # type: ignore[arg-type]


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
    """Apply rate limiting for sync calls.

    Offloads to a dedicated thread with its own fresh event loop to avoid
    nest_asyncio patching and event-loop corruption in production.
    """
    if not model_config:
        return
    import concurrent.futures

    def _run_in_fresh_loop():
        return asyncio.run(apply_rate_limiter(model_config, input_text, rate_limiter_callback))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_run_in_fresh_loop).result()


def _parse_chunk(chunk: Any) -> "ChatChunk":
    """Parse LLM response chunk into standardized format."""

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
