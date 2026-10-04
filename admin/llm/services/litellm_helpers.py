"""LiteLLM Helpers - Utility functions for LLM operations.

Extracted from litellm_client.py for 650-line compliance.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from typing import Any, Awaitable, Callable, TYPE_CHECKING

import httpx
import litellm
import openai

from admin.core.helpers.tokens import approximate_tokens
from admin.llm.exceptions import LLMNotConfiguredError
from admin.core.helpers.vendor_api_bases import SOMA_GITHUB_REPOSITORY_URL
from admin.llm.services.litellm_schemas import (
    ChatChunk,
    LLMCallError,
    LLMNonRetryableError,
    LLMTimeoutError,
    LLMTransientError,
)


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
    from admin.llm.models import LLMModelConfig

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
    """Get API key from Vault (single source of truth). Fail-closed on missing key."""
    key = _get_secret_manager().get_provider_key(service.lower())
    if not key:
        raise LLMNotConfiguredError(f"Missing API key for provider '{service}' in secret manager")
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


# --- Timeout / retry / Groq compat policy (single place for all call paths) ---
# Production interactive chat: never stall a user turn for tens of seconds.
# Django settings is the authority (config.settings / services.gateway.settings);
# env is the 12-factor override. These names are only last-resort schema defaults.

DEFAULT_CONNECT_TIMEOUT_S = 5.0
DEFAULT_READ_TIMEOUT_S = 15.0
DEFAULT_MAX_RETRIES = 1
DEFAULT_RETRY_BASE_DELAY_S = 0.4
RETRY_BACKOFF_CAP_S = 2.0
RETRY_AFTER_CAP_S = 3.0


def _django_setting(name: str) -> Any:
    """Read one tunable from Django settings (authority), else None."""
    try:
        from django.conf import settings as django_settings

        return getattr(django_settings, name, None)
    except Exception:
        return None


def _env_float(name: str) -> float | None:
    """Read a float from an environment variable, or None if unset/invalid."""
    raw = os.environ.get(name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _positive_or(value: Any, default: float) -> float:
    """Coerce to a positive float, else return the default."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def get_timeout_settings() -> tuple[float, float]:
    """Resolve (connect_s, read_s) timeouts.

    Precedence: Django settings LLM_CONNECT_TIMEOUT_S / LLM_READ_TIMEOUT_S,
    then SA01_LLM_CONNECT_TIMEOUT / SA01_LLM_READ_TIMEOUT env vars,
    then optional settings model ``llm_connect_timeout`` / ``llm_read_timeout``.
    """
    connect = _env_float("SA01_LLM_CONNECT_TIMEOUT")
    read = _env_float("SA01_LLM_READ_TIMEOUT")
    dj_connect = _django_setting("LLM_CONNECT_TIMEOUT_S")
    dj_read = _django_setting("LLM_READ_TIMEOUT_S")
    if dj_connect is not None:
        connect = float(dj_connect)
    if dj_read is not None:
        read = float(dj_read)
    if connect is None or read is None:
        try:
            from admin.core.helpers.settings import get_settings

            stg = get_settings()
            if connect is None:
                connect = getattr(stg, "llm_connect_timeout", None)
            if read is None:
                read = getattr(stg, "llm_read_timeout", None)
        except Exception:
            pass
    return (
        _positive_or(connect, DEFAULT_CONNECT_TIMEOUT_S),
        _positive_or(read, DEFAULT_READ_TIMEOUT_S),
    )


def build_timeout() -> "httpx.Timeout":
    """Build an httpx timeout with separate connect/read bounds.

    The read bound caps the gap between streamed chunks, so a stalled stream
    can never hang the caller forever.
    """
    connect, read = get_timeout_settings()
    return httpx.Timeout(connect=connect, read=read, write=read, pool=connect)


def inject_timeout(kwargs: dict) -> dict:
    """Return kwargs with a connect/read timeout set (an explicit timeout wins)."""
    out = dict(kwargs or {})
    if out.get("timeout") is None:
        out["timeout"] = build_timeout()
    return out


def _is_groq_model(model: str) -> bool:
    """True for Groq-routed model strings (three-segment 'groq/...' form)."""
    return (model or "").split("/", 1)[0].lower() == "groq"


def _requests_tools_or_json(kwargs: dict) -> bool:
    """True when the request uses tools or JSON/structured output."""
    return bool(
        kwargs.get("tools")
        or kwargs.get("tool_choice")
        or kwargs.get("functions")
        or kwargs.get("response_format")
    )


def apply_reasoning_format(model: str, kwargs: dict) -> None:
    """Force Groq ``reasoning_format="hidden"`` when tools or JSON are requested.

    Groq returns HTTP 400 for ``reasoning_format:"raw"`` combined with tools or
    JSON output, so 'hidden' is forced in that case; otherwise the caller's
    choice is left untouched. This is the single enforcement point for all
    call paths so the rule cannot drift.
    """
    if not _is_groq_model(model) or not _requests_tools_or_json(kwargs):
        return
    kwargs["reasoning_format"] = "hidden"


def prepare_completion_kwargs(model: str, kwargs: dict, *, stream: bool) -> tuple[dict, bool]:
    """Single place for timeout injection, reasoning_format and Groq stream limits.

    Returns ``(call_kwargs, effective_stream)``. When a Groq model requests both
    ``response_format`` and streaming, streaming is dropped: Groq rejects
    ``response_format`` while streaming (HTTP 400), and stripping ``response_format``
    would silently break the caller's structured-output contract. A single
    non-stream call preserves it (LiteLLM's fake-stream workaround is version
    dependent; the explicit fallback is not).
    """
    call_kwargs = inject_timeout(kwargs)
    apply_reasoning_format(model, call_kwargs)
    if stream and _is_groq_model(model) and call_kwargs.get("response_format"):
        return call_kwargs, False
    return call_kwargs, stream


def get_retry_policy(kwargs: dict) -> tuple[int, float]:
    """Pop retry overrides from call kwargs; returns (max_retries, base_delay_s).

    Honors the legacy ``a0_retry_attempts`` / ``a0_retry_delay_seconds`` kwargs.
    """
    raw_retries = kwargs.pop("a0_retry_attempts", DEFAULT_MAX_RETRIES)
    raw_delay = kwargs.pop("a0_retry_delay_seconds", DEFAULT_RETRY_BASE_DELAY_S)
    try:
        max_retries = max(0, int(raw_retries))
    except (TypeError, ValueError):
        max_retries = DEFAULT_MAX_RETRIES
    try:
        base_delay = max(0.0, float(raw_delay))
    except (TypeError, ValueError):
        base_delay = DEFAULT_RETRY_BASE_DELAY_S
    return max_retries, base_delay


def _retry_after_seconds(exc: Exception | None) -> float | None:
    """Extract a Retry-After header value (seconds) from a provider exception."""
    headers = getattr(getattr(exc, "response", None), "headers", None)
    if headers is None or not hasattr(headers, "get"):
        return None
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None


def retry_backoff_seconds(attempt: int, base_delay: float, exc: Exception | None = None) -> float:
    """Exponential backoff with jitter for a 1-based retry attempt.

    Jitter is 50-100% of the nominal delay so retries never stampede a
    rate-limited provider (e.g. Groq free tier 30 RPM). Retry-After, when
    present, is honored up to RETRY_AFTER_CAP_S.
    """
    nominal = min(RETRY_BACKOFF_CAP_S, base_delay * (2 ** (attempt - 1)))
    delay = nominal * (0.5 + 0.5 * random.random())
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        delay = max(delay, min(retry_after, RETRY_AFTER_CAP_S))
    return delay


def _is_timeout_error(exc: Exception) -> bool:
    """True when the exception represents a timeout."""
    if isinstance(exc, TimeoutError):
        return True
    if getattr(exc, "status_code", None) == 408:
        return True
    timeout_types = tuple(
        filter(
            None,
            (
                getattr(openai, "APITimeoutError", None),
                getattr(litellm_exceptions, "Timeout", None),
            ),
        )
    )
    return bool(timeout_types) and isinstance(exc, timeout_types)


def _is_provider_exception(exc: Exception) -> bool:
    """True when the exception originates from openai/litellm rather than our code."""
    if getattr(exc, "status_code", None) is not None:
        return True
    bases = tuple(
        filter(
            None,
            (
                getattr(openai, "APIError", None),
                getattr(litellm_exceptions, "APIError", None),
                getattr(litellm_exceptions, "GroqException", None),
            ),
        )
    )
    return bool(bases) and isinstance(exc, bases)


def to_typed_error(exc: Exception, *, model: str = "") -> Exception:
    """Map a provider exception to a clear typed error.

    Timeouts are always typed (they are call-path failures, not bugs). Other
    unknown (non-provider) exceptions are returned unchanged so genuine bugs
    are never masked as API failures.
    """
    if isinstance(exc, LLMCallError):
        return exc
    where = f" (model '{model}')" if model else ""
    if _is_timeout_error(exc):
        return LLMTimeoutError(f"LLM call timed out{where}: {exc}")
    status = getattr(exc, "status_code", None)
    if not (isinstance(status, int) or _is_provider_exception(exc)):
        return exc
    if _is_transient_litellm_error(exc):
        return LLMTransientError(f"LLM transient error{where}: {exc}")
    return LLMNonRetryableError(
        f"LLM request rejected{where}: {exc}",
        status_code=status if isinstance(status, int) else None,
    )


def run_with_retries_sync(
    fn: Callable[[], Any], *, max_retries: int, base_delay: float, model: str = ""
) -> Any:
    """Run fn() with bounded retries on transient errors only."""
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as e:
            if not _is_transient_litellm_error(e) or attempt >= max_retries:
                typed = to_typed_error(e, model=model)
                if typed is e:
                    raise
                raise typed from e
            attempt += 1
            time.sleep(retry_backoff_seconds(attempt, base_delay, e))


async def run_with_retries_async(
    fn: Callable[[], Awaitable[Any]], *, max_retries: int, base_delay: float, model: str = ""
) -> Any:
    """Await fn() with bounded retries on transient errors only."""
    attempt = 0
    while True:
        try:
            return await fn()
        except Exception as e:
            if not _is_transient_litellm_error(e) or attempt >= max_retries:
                typed = to_typed_error(e, model=model)
                if typed is e:
                    raise
                raise typed from e
            attempt += 1
            await asyncio.sleep(retry_backoff_seconds(attempt, base_delay, e))


async def apply_rate_limiter(
    model_config: "LLMModelConfig | None",
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
    model_config: "LLMModelConfig | None",
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


def _get_field(obj: Any, name: str) -> Any:
    """Read ``name`` from a dict- or object-style provider payload."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _extract_tool_call_deltas(delta: Any, message: Any) -> list[Any]:
    """Normalize native tool_call fragments from a stream delta or full message.

    Streaming deltas carry partial ``function.arguments`` JSON fragments keyed
    by ``index``; non-stream messages carry complete calls. Never regex-parses
    tool calls out of model text (VIBE: native function calling only).
    """
    raw = _get_field(delta, "tool_calls")
    if not raw:
        raw = _get_field(message, "tool_calls")
    if not raw:
        return []
    from admin.llm.services.litellm_schemas import ToolCallDelta

    out: list[Any] = []
    for i, item in enumerate(raw):
        fn = _get_field(item, "function")
        index = _get_field(item, "index")
        try:
            parsed_index = int(index) if index is not None else i
        except (TypeError, ValueError):
            parsed_index = i
        out.append(
            ToolCallDelta(
                index=parsed_index,
                id=str(_get_field(item, "id") or ""),
                name=str(_get_field(fn, "name") or ""),
                arguments=str(_get_field(fn, "arguments") or ""),
            )
        )
    return out


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

    parsed: "ChatChunk" = ChatChunk(reasoning_delta=reasoning_delta, response_delta=response_delta)
    tool_call_deltas = _extract_tool_call_deltas(delta, message)
    if tool_call_deltas:
        parsed["tool_call_deltas"] = tool_call_deltas
    return parsed


def _adjust_call_args(provider_name: str, model_name: str, kwargs: dict):
    """Adjust call arguments for specific providers."""
    if provider_name == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": SOMA_GITHUB_REPOSITORY_URL,
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
