"""LiteLLM client wrapper.

This module provides LangChain-compatible LLM wrappers using LiteLLM.
Migrated to admin.llm.services for Django compliance.

Split into modules for 650-line compliance:
- litellm_schemas.py: ChatChunk, ChatGenerationResult
- litellm_helpers.py: Rate limiting, API keys, error detection
- litellm_client.py: Wrapper classes and factory functions (this file)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator, Awaitable, Callable, cast, Iterator, List, Optional, Tuple

# Core dependencies
import litellm
from browser_use.llm import ChatOpenRouter
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs.chat_generation import ChatGenerationChunk
from litellm import acompletion, completion, embedding

from admin.core.helpers.tokens import approximate_tokens
from admin.llm.exceptions import LLMNotConfiguredError
from admin.llm.services.litellm_helpers import (
    _adjust_call_args,
    _env_flag,
    _is_transient_litellm_error,
    _merge_provider_defaults,
    _parse_chunk,
    apply_rate_limiter,
    apply_rate_limiter_sync,
    get_api_key,
    get_retry_policy,
    inject_timeout,
    prepare_completion_kwargs,
    retry_backoff_seconds,
    run_with_retries_async,
    run_with_retries_sync,
    to_typed_error,
    turn_off_logging,
)

# Local imports from split modules
from admin.llm.services.litellm_schemas import (
    ChatChunk,
    ChatGenerationResult,
    ToolCallDeltasChunk,
    ToolCallsChunk,
)


# Lazy imports for Django models
def _get_model_config():
    """Lazy import LLMModelConfig to avoid circular imports."""
    from admin.llm.models import LLMModelConfig

    return LLMModelConfig


# Dedicated logger for LLM call tracing
llm_logger = logging.getLogger("somaagent01.llm")
if not llm_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": %(message)s}'
    )
    handler.setFormatter(formatter)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.INFO)

# Initialize
turn_off_logging()
if litellm is not None:
    try:
        litellm.modify_params = True
    except Exception:
        pass


class LiteLLMChatWrapper(SimpleChatModel):
    """LangChain-compatible chat wrapper using LiteLLM."""

    model_name: str
    provider: str
    kwargs: dict = {}

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
        validate_assignment = False

    def __init__(
        self, model: str, provider: str, model_config: Optional[Any] = None, **kwargs: Any
    ):
        """Initialize the instance."""
        # Avoid double-prefixing: if model already starts with provider/, don't add it
        if model.startswith(f"{provider}/"):
            model_value = model
        else:
            model_value = f"{provider}/{model}"
        super().__init__(model_name=model_value, provider=provider, kwargs=kwargs)  # type: ignore
        self.a0_model_conf = model_config

    @property
    def _llm_type(self) -> str:
        return "litellm-chat"

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        """Convert LangChain messages to LiteLLM format."""
        result = []
        role_mapping = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}
        for m in messages:
            role = role_mapping.get(m.type, m.type)
            message_dict = {"role": role, "content": m.content}
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                import json

                new_tool_calls = []
                for tool_call in tool_calls:
                    args = tool_call["args"]
                    args_str = json.dumps(args) if isinstance(args, dict) else str(args)
                    new_tool_calls.append(
                        {
                            "id": tool_call.get("id", ""),
                            "type": "function",
                            "function": {"name": tool_call["name"], "arguments": args_str},
                        }
                    )
                message_dict["tool_calls"] = new_tool_calls
            tool_call_id = getattr(m, "tool_call_id", None)
            if tool_call_id:
                message_dict["tool_call_id"] = tool_call_id
            result.append(message_dict)
        return result

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous completion call with timeout and bounded retries."""
        msgs = self._convert_messages(messages)
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))
        if completion is None:
            raise LLMNotConfiguredError("LiteLLM completion not available.")
        call_kwargs: dict[str, Any] = {**self.kwargs, **kwargs}
        max_retries, base_delay = get_retry_policy(call_kwargs)
        call_kwargs, _ = prepare_completion_kwargs(self.model_name, call_kwargs, stream=False)
        resp = run_with_retries_sync(
            lambda: completion(model=self.model_name, messages=msgs, stop=stop, **call_kwargs),
            max_retries=max_retries,
            base_delay=base_delay,
            model=self.model_name,
        )
        parsed = _parse_chunk(resp)
        output = ChatGenerationResult(parsed).output()
        return output["response_delta"]

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Synchronous streaming completion with timeout and bounded retries.

        Retries only apply before the first chunk is yielded; once output has
        been delivered a failure propagates rather than replaying content.
        Yields text as ChatGenerationChunk and native tool traffic as
        ToolCallDeltasChunk / ToolCallsChunk.
        """
        msgs = self._convert_messages(messages)
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))
        result = ChatGenerationResult()
        if completion is None:
            raise LLMNotConfiguredError("LiteLLM completion not available.")
        call_kwargs: dict[str, Any] = {**self.kwargs, **kwargs}
        max_retries, base_delay = get_retry_policy(call_kwargs)
        call_kwargs, use_stream = prepare_completion_kwargs(
            self.model_name, call_kwargs, stream=True
        )
        attempt = 0
        while True:
            got_any_chunk = False
            try:
                if not use_stream:
                    # Non-stream fallback (Groq + response_format): yield once.
                    resp = completion(
                        model=self.model_name, messages=msgs, stop=stop, **call_kwargs
                    )
                    parsed = _parse_chunk(resp)
                    output = result.add_chunk(parsed)
                    deltas = output.get("tool_call_deltas")
                    if deltas:
                        yield ToolCallDeltasChunk(deltas=deltas)
                    if output["response_delta"]:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=output["response_delta"])
                        )
                    if result.tool_calls:
                        yield ToolCallsChunk(tool_calls=result.tool_calls)
                    return
                for chunk in completion(
                    model=self.model_name,
                    messages=msgs,
                    stream=True,
                    stop=stop,
                    **call_kwargs,
                ):
                    got_any_chunk = True
                    parsed = _parse_chunk(chunk)
                    output = result.add_chunk(parsed)
                    deltas = output.get("tool_call_deltas")
                    if deltas:
                        yield ToolCallDeltasChunk(deltas=deltas)
                    if output["response_delta"]:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=output["response_delta"])
                        )
                if result.tool_calls:
                    yield ToolCallsChunk(tool_calls=result.tool_calls)
                return
            except Exception as e:
                if got_any_chunk:
                    typed = to_typed_error(e, model=self.model_name)
                    if typed is e:
                        raise
                    raise typed from e
                if not _is_transient_litellm_error(e) or attempt >= max_retries:
                    typed = to_typed_error(e, model=self.model_name)
                    if typed is e:
                        raise
                    raise typed from e
                attempt += 1
                time.sleep(retry_backoff_seconds(attempt, base_delay, e))

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        """Asynchronous streaming completion with timeout and bounded retries.

        Retries only apply before the first chunk is yielded; once output has
        been delivered a failure propagates rather than replaying content.
        Yields text as ChatGenerationChunk and native tool traffic as
        ToolCallDeltasChunk / ToolCallsChunk. ``tools=`` in kwargs is passed
        straight through to LiteLLM (native function calling).
        When Groq is asked for ``response_format`` while streaming, the call
        drops to a non-stream completion (single chunk out) — see
        ``prepare_completion_kwargs``.
        """
        msgs = self._convert_messages(messages)
        await apply_rate_limiter(self.a0_model_conf, str(msgs))
        result = ChatGenerationResult()
        if acompletion is None:
            raise LLMNotConfiguredError("LiteLLM acompletion not available.")
        call_kwargs: dict[str, Any] = {**self.kwargs, **kwargs}
        max_retries, base_delay = get_retry_policy(call_kwargs)
        call_kwargs, use_stream = prepare_completion_kwargs(
            self.model_name, call_kwargs, stream=True
        )
        attempt = 0
        while True:
            got_any_chunk = False
            try:
                if not use_stream:
                    # Non-stream fallback (Groq + response_format): emit once.
                    resp = await acompletion(
                        model=self.model_name, messages=msgs, stop=stop, **call_kwargs
                    )
                    parsed = _parse_chunk(resp)
                    output = result.add_chunk(parsed)
                    deltas = output.get("tool_call_deltas")
                    if deltas:
                        yield ToolCallDeltasChunk(deltas=deltas)
                    if output["response_delta"]:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=output["response_delta"])
                        )
                    if result.tool_calls:
                        yield ToolCallsChunk(tool_calls=result.tool_calls)
                    return
                response = await acompletion(
                    model=self.model_name,
                    messages=msgs,
                    stream=True,
                    stop=stop,
                    **call_kwargs,
                )
                async for chunk in response:  # type: ignore
                    got_any_chunk = True
                    parsed = _parse_chunk(chunk)
                    output = result.add_chunk(parsed)
                    deltas = output.get("tool_call_deltas")
                    if deltas:
                        yield ToolCallDeltasChunk(deltas=deltas)
                    if output["response_delta"]:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=output["response_delta"])
                        )
                if result.tool_calls:
                    yield ToolCallsChunk(tool_calls=result.tool_calls)
                return
            except Exception as e:
                if got_any_chunk:
                    typed = to_typed_error(e, model=self.model_name)
                    if typed is e:
                        raise
                    raise typed from e
                if not _is_transient_litellm_error(e) or attempt >= max_retries:
                    typed = to_typed_error(e, model=self.model_name)
                    if typed is e:
                        raise
                    raise typed from e
                attempt += 1
                await asyncio.sleep(retry_backoff_seconds(attempt, base_delay, e))

    async def unified_call(
        self,
        system_message="",
        user_message="",
        messages: List[BaseMessage] | None = None,
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
        rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
        **kwargs: Any,
    ) -> Tuple[str, str]:
        """Unified async call with callbacks for streaming.

        Retries transient errors only, with exponential backoff + jitter; a
        failure after output has started returns the partial result instead of
        replaying it. Retries/timeout policy is shared with the other call paths.
        """
        turn_off_logging()
        if not messages:
            messages = []
        if system_message:
            messages.insert(0, SystemMessage(content=system_message))
        if user_message:
            messages.append(HumanMessage(content=user_message))
        msgs_conv = self._convert_messages(messages)
        limiter = await apply_rate_limiter(
            self.a0_model_conf, str(msgs_conv), rate_limiter_callback
        )
        call_kwargs: dict[str, Any] = {**self.kwargs, **kwargs}
        max_retries, base_delay = get_retry_policy(call_kwargs)
        call_kwargs, use_stream = prepare_completion_kwargs(
            self.model_name, call_kwargs, stream=True
        )
        result = ChatGenerationResult()
        attempt = 0

        async def _emit(output: ChatChunk) -> None:
            if output["reasoning_delta"]:
                if reasoning_callback:
                    await reasoning_callback(output["reasoning_delta"], result.reasoning)
                if tokens_callback:
                    await tokens_callback(
                        output["reasoning_delta"],
                        approximate_tokens(output["reasoning_delta"]),
                    )
                if limiter:
                    limiter.add(output=approximate_tokens(output["reasoning_delta"]))
            if output["response_delta"]:
                if response_callback:
                    await response_callback(output["response_delta"], result.response)
                if tokens_callback:
                    await tokens_callback(
                        output["response_delta"],
                        approximate_tokens(output["response_delta"]),
                    )
                if limiter:
                    limiter.add(output=approximate_tokens(output["response_delta"]))

        while True:
            got_any_chunk = False
            try:
                if not use_stream:
                    # Non-stream fallback (Groq + response_format): emit once.
                    resp = await acompletion(
                        model=self.model_name, messages=msgs_conv, **call_kwargs
                    )
                    await _emit(result.add_chunk(_parse_chunk(resp)))
                    return result.response, result.reasoning
                _completion = await acompletion(
                    model=self.model_name, messages=msgs_conv, stream=True, **call_kwargs
                )
                async for chunk in _completion:  # type: ignore
                    got_any_chunk = True
                    await _emit(result.add_chunk(_parse_chunk(chunk)))
                return result.response, result.reasoning
            except Exception as e:
                if got_any_chunk and _is_transient_litellm_error(e):
                    return result.response, result.reasoning
                if not _is_transient_litellm_error(e) or attempt >= max_retries:
                    typed = to_typed_error(e, model=self.model_name)
                    if typed is e:
                        raise
                    raise typed from e
                attempt += 1
                await asyncio.sleep(retry_backoff_seconds(attempt, base_delay, e))


class AsyncAIChatReplacement:
    """Async chat replacement for browser-use compatibility."""

    class _Completions:
        def __init__(self, wrapper):
            self._wrapper = wrapper

        async def create(self, *args, **kwargs):
            return await self._wrapper._acall(*args, **kwargs)

    class _Chat:
        def __init__(self, wrapper):
            self.completions = AsyncAIChatReplacement._Completions(wrapper)

    def __init__(self, wrapper, *args, **kwargs):
        self._wrapper = wrapper
        self.chat = AsyncAIChatReplacement._Chat(wrapper)


class BrowserCompatibleChatWrapper(ChatOpenRouter):
    """Browser-agent compatible wrapper with message filtering."""

    def __init__(self, *args, **kwargs):
        turn_off_logging()
        self._wrapper = LiteLLMChatWrapper(*args, **kwargs)
        self.model = self._wrapper.model_name
        self.kwargs = self._wrapper.kwargs

    @property
    def model_name(self) -> str:
        return self._wrapper.model_name

    @property
    def provider(self) -> str:
        return self._wrapper.provider

    def get_client(self, *args, **kwargs):
        return AsyncAIChatReplacement(self, *args, **kwargs)

    async def _acall(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """Async call with Gemini compatibility, timeout and bounded retries."""
        await apply_rate_limiter(self._wrapper.a0_model_conf, str(messages))
        try:
            model = kwargs.pop("model", None)
            kwrgs = {**self._wrapper.kwargs, **kwargs}
            max_retries, base_delay = get_retry_policy(kwrgs)
            kwrgs, _ = prepare_completion_kwargs(self._wrapper.model_name, kwrgs, stream=False)
            from services.common.llm_compatibility import (
                fix_gemini_schema,
                should_apply_gemini_compat,
            )

            if (
                should_apply_gemini_compat()
                and "response_format" in kwrgs
                and "json_schema" in kwrgs["response_format"]
                and model
                and model.startswith("gemini/")
            ):
                kwrgs["response_format"]["json_schema"] = fix_gemini_schema(
                    kwrgs["response_format"]["json_schema"]
                )
            resp = await run_with_retries_async(
                lambda: acompletion(
                    model=self._wrapper.model_name, messages=messages, stop=stop, **kwrgs
                ),
                max_retries=max_retries,
                base_delay=base_delay,
                model=self._wrapper.model_name,
            )
            from services.common.llm_compatibility import clean_gemini_json_response

            try:
                msg = resp.choices[0].message  # type: ignore
                content = getattr(msg, "content", None)
                if self.provider == "gemini" and isinstance(content, str):
                    cleaned = clean_gemini_json_response(content)
                    if cleaned:
                        msg.content = cleaned
            except Exception:
                pass
        except Exception as e:
            raise e
        from services.common.llm_compatibility import clean_invalid_json, should_apply_json_cleaning

        if should_apply_json_cleaning():
            try:
                if "response_format" in kwrgs:
                    content = resp.choices[0].message.content  # type: ignore
                    if content is not None and not content.startswith("{"):
                        resp.choices[0].message.content = clean_invalid_json(content)  # type: ignore
            except Exception:
                pass
        return resp


class LiteLLMEmbeddingWrapper(Embeddings):
    """LiteLLM embedding wrapper."""

    model_name: str
    kwargs: dict = {}
    a0_model_conf: Optional[Any] = None

    def __init__(
        self, model: str, provider: str, model_config: Optional[Any] = None, **kwargs: Any
    ):
        self.model_name = f"{provider}/{model}" if provider != "openai" else model
        self.kwargs = kwargs
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))
        call_kwargs = inject_timeout(self.kwargs)
        resp = embedding(model=self.model_name, input=texts, **call_kwargs)
        return cast(
            List[List[float]],
            [
                item.get("embedding") if isinstance(item, dict) else item.embedding
                for item in resp.data
            ],
        )

    def embed_query(self, text: str) -> List[float]:
        apply_rate_limiter_sync(self.a0_model_conf, text)
        call_kwargs = inject_timeout(self.kwargs)
        resp = embedding(model=self.model_name, input=[text], **call_kwargs)
        item = resp.data[0]
        return cast(
            List[float], item.get("embedding") if isinstance(item, dict) else item.embedding
        )


class LocalSentenceTransformerWrapper(Embeddings):
    """Local wrapper for sentence-transformers models."""

    def __init__(
        self, provider: str, model: str, model_config: Optional[Any] = None, **kwargs: Any
    ):
        model = model.strip().strip('"').strip("'")
        if model.startswith("sentence-transformers/"):
            model = model[len("sentence-transformers/") :]
        st_allowed_keys = {
            "device",
            "cache_folder",
            "use_auth_token",
            "revision",
            "trust_remote_code",
            "model_kwargs",
        }
        st_kwargs = {k: v for k, v in (kwargs or {}).items() if k in st_allowed_keys}
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:
            raise ImportError(
                "sentence-transformers is required for LocalSentenceTransformerWrapper."
            ) from e
        self.model = SentenceTransformer(model, **st_kwargs)
        self.model_name = model
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))
        embeddings: Any = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        apply_rate_limiter_sync(self.a0_model_conf, text)
        embedding: Any = self.model.encode([text], convert_to_tensor=False)
        return embedding[0].tolist()


# Factory Functions


def _get_litellm_chat(
    cls, model_name: str, provider_name: str, model_config: Optional[Any] = None, **kwargs: Any
):
    """Get LiteLLM chat wrapper instance. Fail-closed on missing key/model."""
    if not provider_name or not model_name:
        raise LLMNotConfiguredError(
            f"Missing model config: provider={provider_name!r} model={model_name!r}."
        )
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)
    if api_key in ("None", "NA", None, ""):
        raise LLMNotConfiguredError(f"Invalid API key for provider '{provider_name}'.")
    if api_key:
        kwargs["api_key"] = api_key
    provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
    return cls(provider=provider_name, model=model_name, model_config=model_config, **kwargs)


def _get_litellm_embedding(
    model_name: str, provider_name: str, model_config: Optional[Any] = None, **kwargs: Any
):
    """Get LiteLLM embedding wrapper instance. Fail-closed on missing key/model."""
    if not provider_name or not model_name:
        raise LLMNotConfiguredError(
            f"Missing model config: provider={provider_name!r} model={model_name!r}."
        )
    if provider_name == "huggingface" and model_name.startswith("sentence-transformers/"):
        provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
        return LocalSentenceTransformerWrapper(
            provider=provider_name, model=model_name, model_config=model_config, **kwargs
        )
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)
    if api_key in ("None", "NA", None, ""):
        raise LLMNotConfiguredError(f"Invalid API key for embedding provider '{provider_name}'.")
    if api_key:
        kwargs["api_key"] = api_key
    provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
    return LiteLLMEmbeddingWrapper(
        model=model_name, provider=provider_name, model_config=model_config, **kwargs
    )


def get_chat_model(
    provider: str, name: str, model_config: Optional[Any] = None, **kwargs: Any
) -> LiteLLMChatWrapper:
    """Get a chat model for the specified provider and model name."""
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    use_llm = _env_flag("SA01_USE_LLM", True)
    api_key = kwargs.get("api_key")
    if not use_llm:
        raise LLMNotConfiguredError(
            f"LLM disabled. Set USE_LLM=true for provider '{provider_name}'."
        )
    if provider_name == "openai" and (not api_key or api_key in ("None", "NA")):
        raise LLMNotConfiguredError(f"Invalid OpenAI API key for provider '{provider_name}'.")
    return _get_litellm_chat(LiteLLMChatWrapper, name, provider_name, model_config, **kwargs)


def get_browser_model(
    provider: str, name: str, model_config: Optional[Any] = None, **kwargs: Any
) -> BrowserCompatibleChatWrapper:
    """Get a browser-compatible chat model."""
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    return _get_litellm_chat(
        BrowserCompatibleChatWrapper, name, provider_name, model_config, **kwargs
    )


def get_embedding_model(
    provider: str, name: str, model_config: Optional[Any] = None, **kwargs: Any
):
    """Get an embedding model for the specified provider."""
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("embedding", orig, kwargs)
    return _get_litellm_embedding(name, provider_name, model_config, **kwargs)
