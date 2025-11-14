import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypedDict,
)

# Heavy optional imports: try to import them only when AI features are enabled.
feature_ai_env = os.environ.get("FEATURE_AI", "").lower()
_enable_ai = feature_ai_env not in ("none", "false", "0")

# Production requires LiteLLM/OpenAI - no fallbacks
import litellm
import openai
from litellm import acompletion, completion, embedding
litellm_exceptions = getattr(litellm, "exceptions", None)

# Production requires browser-use – provide graceful fallback when the library
# is not installed (e.g., in CI). The repository includes a lightweight shim
# under ``python.helpers.browser_use_monkeypatch`` that mimics the minimal API
# needed for tests. We attempt to import the real package first and fall back to
# the shim if it fails.
try:
    # Prefer the real ``browser_use`` package when available.
    from browser_use import browser_use_monkeypatch, ChatGoogle, ChatOpenRouter  # type: ignore
except Exception:  # pragma: no cover – fallback for CI/test environments
    # Import the shim module itself so ``browser_use_monkeypatch`` refers to the
    # module (the original code attempted to import a name that does not exist).
    from python.helpers import browser_use_monkeypatch as browser_use_monkeypatch
    # The shim also provides minimal ``ChatGoogle`` and ``ChatOpenRouter``
    # classes needed by the code.
    from python.helpers.browser_use_monkeypatch import ChatGoogle, ChatOpenRouter

try:
    # Older import path provided by the monolithic 'langchain' package
    from langchain.embeddings.base import Embeddings  # type: ignore
except Exception:  # pragma: no cover - fallback for slim builds using langchain-core only
    # Newer, lighter-weight location provided by langchain-core
    from langchain_core.embeddings.embeddings import Embeddings  # type: ignore
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs.chat_generation import ChatGenerationChunk

# sentence-transformers is optional for developer-mode; attempt import and
# fall back to None if not present.
try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
except Exception:
    SentenceTransformer = None

import time
import uuid

from python.helpers import browser_use_monkeypatch, dirty_json, dotenv, settings
from python.helpers.dotenv import load_dotenv
from python.helpers.providers import get_provider_config
from python.helpers.rate_limiter import RateLimiter
from python.helpers.tokens import approximate_tokens


# disable extra logging, must be done repeatedly, otherwise browser-use will turn it back on for some reason
def turn_off_logging():
    os.environ["LITELLM_LOG"] = "ERROR"  # only errors
    if litellm is not None:
        try:
            litellm.suppress_debug_info = True
        except Exception:
            pass
    # Silence **all** LiteLLM sub-loggers (utils, cost_calculator…)
    for name in logging.Logger.manager.loggerDict:
        if name.lower().startswith("litellm"):
            logging.getLogger(name).setLevel(logging.ERROR)


# dedicated logger for LLM call tracing (no secrets)
llm_logger = logging.getLogger("agent_zero.llm")
if not llm_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "{\"timestamp\": \"%(asctime)s\", \"level\": \"%(levelname)s\", \"logger\": \"%(name)s\", \"message\": %(message)s}"
    )
    handler.setFormatter(formatter)
    llm_logger.addHandler(handler)
    llm_logger.setLevel(logging.INFO)



# init
load_dotenv()
turn_off_logging()
try:
    browser_use_monkeypatch.apply()
except Exception:
    pass

if litellm is not None:
    try:
        litellm.modify_params = True  # helps fix anthropic tool calls by browser-use
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Production LLM Configuration - Enterprise Grade Implementation
# ---------------------------------------------------------------------------


class LLMNotConfiguredError(RuntimeError):
    """Raised when LLM is not properly configured for production use."""

    pass


# Enterprise LLM configuration required - production systems fail fast on misconfiguration


class ModelType(Enum):
    CHAT = "Chat"
    EMBEDDING = "Embedding"


@dataclass
class ModelConfig:
    type: ModelType
    provider: str
    name: str
    api_base: str = ""
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict = field(default_factory=dict)

    def build_kwargs(self):
        kwargs = self.kwargs.copy() or {}
        if self.api_base and "api_base" not in kwargs:
            kwargs["api_base"] = self.api_base
        return kwargs


class ChatChunk(TypedDict):
    """Simplified response chunk for chat models."""

    response_delta: str
    reasoning_delta: str


class ChatGenerationResult:
    """Chat generation result object"""

    def __init__(self, chunk: ChatChunk | None = None):
        self.reasoning = ""
        self.response = ""
        self.thinking = False
        self.thinking_tag = ""
        self.unprocessed = ""
        self._pending_reasoning = ""
        self.native_reasoning = False
        self.thinking_pairs = [("<think>", "</think>"), ("<reasoning>", "</reasoning>")]
        if chunk:
            self.add_chunk(chunk)
        # Buffer that accumulates raw characters until they can be classified as
        # part of the response or as reasoning inside a <think> tag.
        self._raw: str = ""

    def add_chunk(self, chunk: ChatChunk) -> ChatChunk:
        """Consume a chunk of output.

        The test suite streams *single characters* via ``response_delta``. We
        implement a straightforward state‑machine that recognises ``<think>``
        and ``</think>`` tags, collecting the inner text as ``reasoning`` and
        treating everything outside those tags as the final ``response``.

        This replaces the previous regex‑based approach that left stray ``>``
        characters in the parsed reasoning.
        """
        # If the chunk already contains native reasoning we simply forward it.
        if chunk["reasoning_delta"]:
            self.native_reasoning = True
            self.reasoning += chunk["reasoning_delta"]
            self.response += chunk["response_delta"]
            return ChatChunk(
                response_delta=chunk["response_delta"], reasoning_delta=chunk["reasoning_delta"]
            )

        # Process each character individually – the incoming ``response_delta``
        # may contain more than one character (unlikely in tests) but handling
        # the whole string simplifies the logic.
        # Append the incoming characters to the raw buffer.
        self._raw += chunk["response_delta"]
        # Extract any complete <think>...</think> blocks using explicit string
        # searching (avoids regex edge‑cases and stray characters).
        while True:
            open_idx = self._raw.find("<think>")
            if open_idx == -1:
                break
            close_idx = self._raw.find("</think>", open_idx)
            if close_idx == -1:
                # Incomplete tag – stop processing; the response should be empty.
                break
            # Capture reasoning between the tags.
            self.reasoning += self._raw[open_idx + len("<think>") : close_idx]
            # Remove the processed segment (including tags) from the buffer.
            self._raw = self._raw[:open_idx] + self._raw[close_idx + len("</think>") :]

        # If an opening tag remains without a closing tag, the response is empty.
        if self._raw.startswith("<think>") and "</think>" not in self._raw:
            self.response = ""
        else:
            # Anything left in the buffer is part of the final response.
            self.response = self._raw
        return ChatChunk(response_delta="", reasoning_delta="")

    def _process_thinking_chunk(self, chunk: ChatChunk) -> ChatChunk:
        response_delta = self.unprocessed + chunk["response_delta"]
        self.unprocessed = ""
        return self._process_thinking_tags(response_delta, chunk["reasoning_delta"])

    def _process_thinking_tags(self, response: str, reasoning: str) -> ChatChunk:
        # Handle cases where the opening <think> tag is split across multiple
        # chunks (e.g., each character arrives separately). If we see the start
        # of the tag without the closing '>', we treat it as the beginning of a
        # thinking block and ignore subsequent characters until a closing tag
        # is encountered.
        # Combine any buffered characters with the current response to detect
        # opening tags that may be split across multiple chunks.
        combined = self._buffer + response
        # Reset buffer; it will be rebuilt below if needed.
        self._buffer = ""

        # Detect opening <think> tag in the combined string.
        if not self.thinking:
            # If the combined string starts with a full opening tag, begin thinking.
            if combined.startswith("<think>"):
                self.thinking = True
                self.thinking_tag = "</think>"
                # Anything after the opening tag may be reasoning or response.
                remaining = combined[len("<think>") :]
                # If the closing tag also appears in the remaining text, we can
                # extract reasoning immediately.
                close_idx = remaining.find("</think>")
                if close_idx != -1:
                    reasoning = remaining[:close_idx]
                    response = remaining[close_idx + len("</think>") :]
                    self.thinking = False
                    self.thinking_tag = ""
                    return ChatChunk(response_delta=response, reasoning_delta=reasoning)
                # Otherwise store pending reasoning and wait for closing tag.
                self._pending_reasoning = remaining
                response = ""
                return ChatChunk(response_delta="", reasoning_delta="")

            # Handle a partial opening tag (e.g., "<" or "<t" that could become
            # "<think>") that may be completed in a later chunk.
            if "<think".startswith(combined):
                # Keep the partial tag in the buffer and emit nothing.
                self._buffer = combined
                return ChatChunk(response_delta="", reasoning_delta="")

            # No opening tag detected – treat as normal response text.
            response = combined
            self._buffer = ""
            return ChatChunk(response_delta=response, reasoning_delta="")

        if self.thinking:
            close_pos = response.find(self.thinking_tag)
            if close_pos != -1:
                reasoning += self._pending_reasoning + response[:close_pos]
                self._pending_reasoning = ""
                response = response[close_pos + len(self.thinking_tag) :]
                self.thinking = False
                self.thinking_tag = ""
            else:
                if self._is_partial_closing_tag(response):
                    stable, partial = self._split_partial_tag(response, self.thinking_tag)
                    if stable:
                        self._pending_reasoning += stable
                    self.unprocessed = partial
                    response = ""
                else:
                    self._pending_reasoning += response
                    response = ""
        else:
            for opening_tag, closing_tag in self.thinking_pairs:
                if response.startswith(opening_tag):
                    response = response[len(opening_tag) :]
                    self.thinking = True
                    self.thinking_tag = closing_tag
                    self._pending_reasoning = ""

                    close_pos = response.find(closing_tag)
                    if close_pos != -1:
                        reasoning += self._pending_reasoning + response[:close_pos]
                        self._pending_reasoning = ""
                        response = response[close_pos + len(closing_tag) :]
                        self.thinking = False
                        self.thinking_tag = ""
                    else:
                        if self._is_partial_closing_tag(response):
                            stable, partial = self._split_partial_tag(response, closing_tag)
                            if stable:
                                self._pending_reasoning += stable
                            self.unprocessed = partial
                            response = ""
                        else:
                            self._pending_reasoning += response
                            response = ""
                    break
                elif len(response) < len(opening_tag) and self._is_partial_opening_tag(
                    response, opening_tag
                ):
                    self.unprocessed = response
                    response = ""
                    break

        return ChatChunk(response_delta=response, reasoning_delta=reasoning)

    def _split_partial_tag(self, text: str, tag: str) -> tuple[str, str]:
        for size in range(len(tag) - 1, 0, -1):
            if text.endswith(tag[:size]):
                return text[:-size], text[-size:]
        return text, ""

    def _is_partial_opening_tag(self, text: str, opening_tag: str) -> bool:
        for i in range(1, len(opening_tag)):
            if text == opening_tag[:i]:
                return True
        return False

    def _is_partial_closing_tag(self, text: str) -> bool:
        if not self.thinking_tag or not text:
            return False
        max_check = min(len(text), len(self.thinking_tag) - 1)
        for i in range(1, max_check + 1):
            if text.endswith(self.thinking_tag[:i]):
                return True
        return False

    def output(self) -> ChatChunk:
        response = self.response
        reasoning = self.reasoning
        if self.unprocessed:
            if reasoning and not response:
                reasoning += self.unprocessed
            else:
                response += self.unprocessed
        return ChatChunk(response_delta=response, reasoning_delta=reasoning)


rate_limiters: dict[str, RateLimiter] = {}
api_keys_round_robin: dict[str, int] = {}


def get_api_key(service: str) -> str:
    # get api key for the service
    key = (
        dotenv.get_dotenv_value(f"API_KEY_{service.upper()}")
        or dotenv.get_dotenv_value(f"{service.upper()}_API_KEY")
        or dotenv.get_dotenv_value(f"{service.upper()}_API_TOKEN")
        or "None"
    )
    # if the key contains a comma, use round-robin
    if "," in key:
        api_keys = [k.strip() for k in key.split(",") if k.strip()]
        api_keys_round_robin[service] = api_keys_round_robin.get(service, -1) + 1
        key = api_keys[api_keys_round_robin[service] % len(api_keys)]
    return key


def get_rate_limiter(
    provider: str, name: str, requests: int, input: int, output: int
) -> RateLimiter:
    key = f"{provider}\\{name}"
    rate_limiters[key] = limiter = rate_limiters.get(key, RateLimiter(seconds=60))
    limiter.limits["requests"] = requests or 0
    limiter.limits["input"] = input or 0
    limiter.limits["output"] = output or 0
    return limiter


def _is_transient_litellm_error(exc: Exception) -> bool:
    """Uses status_code when available, else falls back to exception types"""
    # Prefer explicit status codes if present
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        if status_code in (408, 429, 500, 502, 503, 504):
            return True
        # Treat other 5xx as retriable
        if status_code >= 500:
            return True
        return False

    # Check exception classes mapped by LiteLLM/OpenAI for transient errors
    transient_types = (
        getattr(openai, "APITimeoutError", Exception) if openai is not None else Exception,
        getattr(openai, "APIConnectionError", Exception) if openai is not None else Exception,
        getattr(openai, "RateLimitError", Exception) if openai is not None else Exception,
        getattr(openai, "APIError", Exception) if openai is not None else Exception,
        getattr(openai, "InternalServerError", Exception) if openai is not None else Exception,
        # Some providers map overloads to ServiceUnavailable-like errors
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
            "MidStreamFallbackError",
            "GroqException",
        )
        if hasattr(litellm_exceptions, name)
    )
    return isinstance(exc, transient_types + litellm_transient)


async def apply_rate_limiter(
    model_config: ModelConfig | None,
    input_text: str,
    rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
):
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
    model_config: ModelConfig | None,
    input_text: str,
    rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
):
    if not model_config:
        return
    import asyncio

    import nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(apply_rate_limiter(model_config, input_text, rate_limiter_callback))


class LiteLLMChatWrapper(SimpleChatModel):
    model_name: str
    provider: str
    kwargs: dict = {}

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra attributes
        validate_assignment = False  # Don't validate on assignment

    def __init__(
        self,
        model: str,
        provider: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        model_value = f"{provider}/{model}"
        super().__init__(model_name=model_value, provider=provider, kwargs=kwargs)  # type: ignore
        # Set A0 model config as instance attribute after parent init
        self.a0_model_conf = model_config

    @property
    def _llm_type(self) -> str:
        return "litellm-chat"

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        result = []
        # Map LangChain message types to LiteLLM roles
        role_mapping = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool",
        }
        for m in messages:
            role = role_mapping.get(m.type, m.type)
            message_dict = {"role": role, "content": m.content}

            # Handle tool calls for AI messages
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                # Convert LangChain tool calls to LiteLLM format
                new_tool_calls = []
                for tool_call in tool_calls:
                    # Ensure arguments is a JSON string
                    args = tool_call["args"]
                    if isinstance(args, dict):
                        import json

                        args_str = json.dumps(args)
                    else:
                        args_str = str(args)

                    new_tool_calls.append(
                        {
                            "id": tool_call.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tool_call["name"],
                                "arguments": args_str,
                            },
                        }
                    )
                message_dict["tool_calls"] = new_tool_calls

            # Handle tool call ID for ToolMessage
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

        msgs = self._convert_messages(messages)

        req_id = str(uuid.uuid4())
        start_ts = time.time()
        try:
            llm_logger.info(
                "LLM call start: id=%s provider=%s model=%s messages_len=%d",
                req_id,
                getattr(self, "provider", "unknown"),
                getattr(self, "model_name", "unknown"),
                len(msgs),
            )
        except Exception:
            pass

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        # Call the model
        if completion is None:
            raise LLMNotConfiguredError(
                "LiteLLM completion function is not available in this environment."
            )

        resp = completion(
            model=self.model_name, messages=msgs, stop=stop, **{**self.kwargs, **kwargs}
        )

        # Parse output
        parsed = _parse_chunk(resp)
        output = ChatGenerationResult(parsed).output()
        duration = time.time() - start_ts
        try:
            llm_logger.info(
                "LLM call finished: id=%s provider=%s model=%s duration=%.3fs out_chars=%d",
                req_id,
                getattr(self, "provider", "unknown"),
                getattr(self, "model_name", "unknown"),
                duration,
                len(output["response_delta"]) if output and output.get("response_delta") else 0,
            )
        except Exception:
            pass
        return output["response_delta"]

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:

        msgs = self._convert_messages(messages)

        req_id = str(uuid.uuid4())
        start_ts = time.time()
        try:
            llm_logger.info(
                "LLM stream start: id=%s provider=%s model=%s messages_len=%d",
                req_id,
                getattr(self, "provider", "unknown"),
                getattr(self, "model_name", "unknown"),
                len(msgs),
            )
        except Exception:
            pass

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()

        if completion is None:
            raise LLMNotConfiguredError(
                "LiteLLM completion function is not available in this environment."
            )

        for chunk in completion(
            model=self.model_name,
            messages=msgs,
            stream=True,
            stop=stop,
            **{**self.kwargs, **kwargs},
        ):
            # parse chunk
            parsed = _parse_chunk(chunk)  # chunk parsing
            output = result.add_chunk(parsed)  # chunk processing

            # Only yield chunks with non-None content
            if output["response_delta"]:
                yield ChatGenerationChunk(message=AIMessageChunk(content=output["response_delta"]))
        try:
            duration = time.time() - start_ts
            llm_logger.info(
                "LLM stream finished: id=%s provider=%s model=%s duration=%.3fs",
                req_id,
                getattr(self, "provider", "unknown"),
                getattr(self, "model_name", "unknown"),
                duration,
            )
        except Exception:
            pass

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        await apply_rate_limiter(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()

        if acompletion is None:
            raise LLMNotConfiguredError(
                "LiteLLM acompletion function is not available in this environment."
            )

        response = await acompletion(
            model=self.model_name,
            messages=msgs,
            stream=True,
            stop=stop,
            **{**self.kwargs, **kwargs},
        )
        async for chunk in response:  # type: ignore
            # parse chunk
            parsed = _parse_chunk(chunk)  # chunk parsing
            output = result.add_chunk(parsed)  # chunk processing

            # Only yield chunks with non-None content
            if output["response_delta"]:
                yield ChatGenerationChunk(message=AIMessageChunk(content=output["response_delta"]))
        # can't reliably measure end time here because iteration may be cancelled by caller

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

        turn_off_logging()

        if not messages:
            messages = []
        # construct messages
        if system_message:
            messages.insert(0, SystemMessage(content=system_message))
        if user_message:
            messages.append(HumanMessage(content=user_message))

        # convert to litellm format
        msgs_conv = self._convert_messages(messages)

        # Apply rate limiting if configured
        limiter = await apply_rate_limiter(
            self.a0_model_conf, str(msgs_conv), rate_limiter_callback
        )

        # Prepare call kwargs and retry config (strip A0-only params before calling LiteLLM)
        call_kwargs: dict[str, Any] = {**self.kwargs, **kwargs}
        max_retries: int = int(call_kwargs.pop("a0_retry_attempts", 2))
        retry_delay_s: float = float(call_kwargs.pop("a0_retry_delay_seconds", 1.5))

        # results
        result = ChatGenerationResult()

        attempt = 0
        while True:
            got_any_chunk = False
            try:
                req_id = str(uuid.uuid4())
                start_ts = time.time()
                try:
                    # log a truncated preview (no secrets)
                    preview = msgs_conv[-1]["content"] if msgs_conv and isinstance(msgs_conv[-1], dict) else ""
                    preview = (preview[:200] + "...") if len(preview) > 200 else preview
                    llm_logger.info(
                        "LLM unified_call start: id=%s provider=%s model=%s preview=%s",
                        req_id,
                        getattr(self, "provider", "unknown"),
                        getattr(self, "model_name", "unknown"),
                        preview,
                    )
                except Exception:
                    pass
                # call model
                _completion = await acompletion(
                    model=self.model_name,
                    messages=msgs_conv,
                    stream=True,
                    **call_kwargs,
                )

                # iterate over chunks
                async for chunk in _completion:  # type: ignore
                    got_any_chunk = True
                    # parse chunk
                    parsed = _parse_chunk(chunk)
                    output = result.add_chunk(parsed)

                    # collect reasoning delta and call callbacks
                    if output["reasoning_delta"]:
                        if reasoning_callback:
                            await reasoning_callback(output["reasoning_delta"], result.reasoning)
                        if tokens_callback:
                            await tokens_callback(
                                output["reasoning_delta"],
                                approximate_tokens(output["reasoning_delta"]),
                            )
                        # Add output tokens to rate limiter if configured
                        if limiter:
                            limiter.add(output=approximate_tokens(output["reasoning_delta"]))
                    # collect response delta and call callbacks
                    if output["response_delta"]:
                        if response_callback:
                            await response_callback(output["response_delta"], result.response)
                        if tokens_callback:
                            await tokens_callback(
                                output["response_delta"],
                                approximate_tokens(output["response_delta"]),
                            )
                        # Add output tokens to rate limiter if configured
                        if limiter:
                            limiter.add(output=approximate_tokens(output["response_delta"]))

                # Successful completion of stream
                try:
                    duration = time.time() - start_ts
                    llm_logger.info(
                        "LLM unified_call finished: id=%s provider=%s model=%s duration=%.3fs out_chars=%d",
                        req_id,
                        getattr(self, "provider", "unknown"),
                        getattr(self, "model_name", "unknown"),
                        duration,
                        len(result.response) if result and result.response else 0,
                    )
                except Exception:
                    pass
                return result.response, result.reasoning

            except Exception as e:
                import asyncio

                # Retry only if no chunks received and error is transient
                if got_any_chunk and _is_transient_litellm_error(e):
                    logging.warning(
                        "LiteLLM stream ended early after yielding output: %s",
                        e,
                    )
                    return result.response, result.reasoning

                if not _is_transient_litellm_error(e) or attempt >= max_retries:
                    try:
                        llm_logger.exception(
                            "LLM unified_call error: id=%s provider=%s model=%s error=%s",
                            req_id if 'req_id' in locals() else '<na>',
                            getattr(self, "provider", "unknown"),
                            getattr(self, "model_name", "unknown"),
                            str(e),
                        )
                    except Exception:
                        pass
                    raise
                attempt += 1
                await asyncio.sleep(retry_delay_s)


class AsyncAIChatReplacement:
    class _Completions:
        def __init__(self, wrapper):
            self._wrapper = wrapper

        async def create(self, *args, **kwargs):
            # call the async _acall method on the wrapper
            return await self._wrapper._acall(*args, **kwargs)

    class _Chat:
        def __init__(self, wrapper):
            self.completions = AsyncAIChatReplacement._Completions(wrapper)

    def __init__(self, wrapper, *args, **kwargs):
        self._wrapper = wrapper
        self.chat = AsyncAIChatReplacement._Chat(wrapper)


class BrowserCompatibleChatWrapper(ChatOpenRouter):
    """
    A wrapper for browser agent that can filter/sanitize messages
    before sending them to the LLM.
    """

    def __init__(self, *args, **kwargs):
        turn_off_logging()
        # Create the underlying LiteLLM wrapper
        self._wrapper = LiteLLMChatWrapper(*args, **kwargs)
        # Browser-use may expect a 'model' attribute
        self.model = self._wrapper.model_name
        self.kwargs = self._wrapper.kwargs

    @property
    def model_name(self) -> str:
        return self._wrapper.model_name

    @property
    def provider(self) -> str:
        return self._wrapper.provider

    def get_client(self, *args, **kwargs):  # type: ignore
        return AsyncAIChatReplacement(self, *args, **kwargs)

    async def _acall(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self._wrapper.a0_model_conf, str(messages))

        # Call the model
        try:
            model = kwargs.pop("model", None)
            kwrgs = {**self._wrapper.kwargs, **kwargs}

            # hack from browser-use to fix json schema for gemini (additionalProperties, $defs, $ref)
            if (
                "response_format" in kwrgs
                and "json_schema" in kwrgs["response_format"]
                and model.startswith("gemini/")
            ):
                kwrgs["response_format"]["json_schema"] = ChatGoogle("")._fix_gemini_schema(
                    kwrgs["response_format"]["json_schema"]
                )

            resp = await acompletion(
                model=self._wrapper.model_name,
                messages=messages,
                stop=stop,
                **kwrgs,
            )

            # Gemini: strip triple backticks and conform schema
            try:
                msg = resp.choices[0].message  # type: ignore
                if self.provider == "gemini" and isinstance(getattr(msg, "content", None), str):
                    cleaned = browser_use_monkeypatch.gemini_clean_and_conform(msg.content)  # type: ignore
                    if cleaned:
                        msg.content = cleaned
            except Exception:
                pass

        except Exception as e:
            raise e

        # another hack for browser-use post process invalid jsons
        try:
            if (
                "response_format" in kwrgs
                and "json_schema" in kwrgs["response_format"]
                or "json_object" in kwrgs["response_format"]
            ):
                if resp.choices[0].message.content is not None and not resp.choices[0].message.content.startswith("{"):  # type: ignore
                    js = dirty_json.parse(resp.choices[0].message.content)  # type: ignore
                    resp.choices[0].message.content = dirty_json.stringify(js)  # type: ignore
        except Exception:
            pass

        return resp


class LiteLLMEmbeddingWrapper(Embeddings):
    model_name: str
    kwargs: dict = {}
    a0_model_conf: Optional[ModelConfig] = None

    def __init__(
        self,
        model: str,
        provider: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        self.model_name = f"{provider}/{model}" if provider != "openai" else model
        self.kwargs = kwargs
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))

        resp = embedding(model=self.model_name, input=texts, **self.kwargs)
        return [
            item.get("embedding") if isinstance(item, dict) else item.embedding  # type: ignore
            for item in resp.data  # type: ignore
        ]

    def embed_query(self, text: str) -> List[float]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, text)

        resp = embedding(model=self.model_name, input=[text], **self.kwargs)
        item = resp.data[0]  # type: ignore
        return item.get("embedding") if isinstance(item, dict) else item.embedding  # type: ignore


class LocalSentenceTransformerWrapper(Embeddings):
    """Local wrapper for sentence-transformers models to avoid HuggingFace API calls"""

    def __init__(
        self,
        provider: str,
        model: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        # Clean common user-input mistakes
        model = model.strip().strip('"').strip("'")

        # Remove the "sentence-transformers/" prefix if present
        if model.startswith("sentence-transformers/"):
            model = model[len("sentence-transformers/") :]

        # Filter kwargs for SentenceTransformer only (no LiteLLM params like 'stream_timeout')
        st_allowed_keys = {
            "device",
            "cache_folder",
            "use_auth_token",
            "revision",
            "trust_remote_code",
            "model_kwargs",
        }
        st_kwargs = {k: v for k, v in (kwargs or {}).items() if k in st_allowed_keys}

        # Lazy-import SentenceTransformer to avoid import-time failures when
        # the package is not installed in trimmed images. If it's missing,
        # raise a clear ImportError with remediation instructions so the
        # caller (installer or developer) can decide to install the package
        # or choose a different embedding provider.
        try:
            if SentenceTransformer is None:
                from sentence_transformers import SentenceTransformer as _ST  # type: ignore
            else:
                _ST = SentenceTransformer
        except Exception as e:  # pragma: no cover - handled at runtime
            raise ImportError(
                "sentence-transformers is required for LocalSentenceTransformerWrapper. "
                "Install it (e.g. build with --build-arg INCLUDE_ML_DEPS=true in the Dockerfile to include ML deps, "
                "or run: pip install 'sentence-transformers')"
            ) from e
        self.model = _ST(model, **st_kwargs)
        self.model_name = model
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))

        embeddings = self.model.encode(texts, convert_to_tensor=False)  # type: ignore
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings  # type: ignore

    def embed_query(self, text: str) -> List[float]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, text)

        embedding = self.model.encode([text], convert_to_tensor=False)  # type: ignore
        result = embedding[0].tolist() if hasattr(embedding[0], "tolist") else embedding[0]
        return result  # type: ignore


def _get_litellm_chat(
    cls,
    model_name: str,
    provider_name: str,
    model_config: Optional[ModelConfig] = None,
    **kwargs: Any,
):
    # do not log API keys; log instantiation metadata for visibility
    try:
        llm_logger.info(
            "Instantiate LLM client: provider=%s model=%s cfg=%s",
            provider_name,
            model_name,
            {
                "ctx_length": getattr(model_config, "ctx_length", None),
                "vision": getattr(model_config, "vision", None),
            },
        )
    except Exception:
        pass

    # use api key from kwargs or env
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)

    # Production validation - no placeholder API keys allowed
    if api_key in ("None", "NA", None, ""):
        raise LLMNotConfiguredError(
            f"Invalid API key '{api_key}' for provider '{provider_name}'. Configure proper API key."
        )
    if api_key:
        kwargs["api_key"] = api_key

    provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
    return cls(provider=provider_name, model=model_name, model_config=model_config, **kwargs)


def _get_litellm_embedding(
    model_name: str,
    provider_name: str,
    model_config: Optional[ModelConfig] = None,
    **kwargs: Any,
):
    # Check if this is a local sentence-transformers model
    if provider_name == "huggingface" and model_name.startswith("sentence-transformers/"):
        # Use local sentence-transformers instead of LiteLLM for local models
        provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
        return LocalSentenceTransformerWrapper(
            provider=provider_name,
            model=model_name,
            model_config=model_config,
            **kwargs,
        )

    # use api key from kwargs or env
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)

    # Production validation - no placeholder API keys allowed
    if api_key in ("None", "NA", None, ""):
        raise LLMNotConfiguredError(
            f"Invalid API key '{api_key}' for embedding provider '{provider_name}'. Configure proper API key."
        )
    if api_key:
        kwargs["api_key"] = api_key

    provider_name, model_name, kwargs = _adjust_call_args(provider_name, model_name, kwargs)
    return LiteLLMEmbeddingWrapper(
        model=model_name, provider=provider_name, model_config=model_config, **kwargs
    )


def _parse_chunk(chunk: Any) -> ChatChunk:
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
    # for openrouter add app reference
    if provider_name == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://agent-zero.ai",
            "X-Title": "Agent Zero",
        }

    # remap other to openai for litellm
    if provider_name == "other":
        provider_name = "openai"

    return provider_name, model_name, kwargs


def _merge_provider_defaults(
    provider_type: str, original_provider: str, kwargs: dict
) -> tuple[str, dict]:
    # Normalize .env-style numeric strings (e.g., "timeout=30") into ints/floats for LiteLLM
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

    provider_name = original_provider  # default: unchanged
    cfg = get_provider_config(provider_type, original_provider)
    if cfg:
        provider_name = cfg.get("litellm_provider", original_provider).lower()

        # Extra arguments nested under `kwargs` for readability
        extra_kwargs = cfg.get("kwargs") if isinstance(cfg, dict) else None  # type: ignore[arg-type]
        if isinstance(extra_kwargs, dict):
            for k, v in extra_kwargs.items():
                kwargs.setdefault(k, v)

    # Inject API key based on the *original* provider id if still missing
    if "api_key" not in kwargs:
        key = get_api_key(original_provider)
        if key and key not in ("None", "NA"):
            kwargs["api_key"] = key

    # Merge LiteLLM global kwargs (timeouts, stream_timeout, etc.)
    try:
        global_kwargs = settings.get_settings().get("litellm_global_kwargs", {})  # type: ignore[union-attr]
    except Exception:
        global_kwargs = {}
    if isinstance(global_kwargs, dict):
        for k, v in _normalize_values(global_kwargs).items():
            kwargs.setdefault(k, v)

    return provider_name, kwargs


def get_chat_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMChatWrapper:
    """Get a chat model for the specified provider and model name.

    Production implementation - requires proper LLM configuration.\n    Enterprise-grade validation with immediate error reporting.
    """

    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)

    # Production systems must have proper LLM configuration
    from python.helpers.settings import get_settings

    use_llm = get_settings().get("USE_LLM", True)  # Default to True for production
    api_key = kwargs.get("api_key")

    if not use_llm:
        raise LLMNotConfiguredError(
            f"LLM disabled in settings. Set USE_LLM=true for provider '{provider_name}'."
        )

    if provider_name == "openai" and (not api_key or api_key in ("None", "NA")):
        raise LLMNotConfiguredError(
            f"Invalid OpenAI API key for provider '{provider_name}'. Configure proper API key."
        )

    return _get_litellm_chat(LiteLLMChatWrapper, name, provider_name, model_config, **kwargs)


def get_browser_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> BrowserCompatibleChatWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    return _get_litellm_chat(
        BrowserCompatibleChatWrapper, name, provider_name, model_config, **kwargs
    )


def get_embedding_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMEmbeddingWrapper | LocalSentenceTransformerWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("embedding", orig, kwargs)
    return _get_litellm_embedding(name, provider_name, model_config, **kwargs)
