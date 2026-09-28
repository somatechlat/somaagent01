"""LiteLLM Schemas - Data classes, TypedDicts and typed errors for LLM operations.

Extracted from litellm_client.py for 650-line compliance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, NotRequired, TypedDict


@dataclass
class ToolCallDelta:
    """Normalized fragment of a streamed native tool call.

    Native function-calling only — tool calls are never regex-parsed
    out of model text (VIBE rule).
    """

    index: int
    id: str = ""
    name: str = ""
    arguments: str = ""


@dataclass
class AssembledToolCall:
    """A complete native tool call assembled from stream fragments.

    ``arguments`` is a dict when the provider JSON parsed cleanly; the raw
    string is kept otherwise so the caller can fail the call visibly.
    """

    id: str
    name: str
    arguments: Any


@dataclass
class ToolCallDeltasChunk:
    """Yielded mid-stream so callers can render a live tool-argument timeline."""

    deltas: list[ToolCallDelta] = field(default_factory=list)


@dataclass
class ToolCallsChunk:
    """Yielded after a completion when the model requested native tool calls."""

    tool_calls: list[AssembledToolCall] = field(default_factory=list)


class ChatChunk(TypedDict):
    """Simplified response chunk for chat models."""

    response_delta: str
    reasoning_delta: str
    tool_call_deltas: NotRequired[list[ToolCallDelta]]


class ToolCallAccumulator:
    """Assemble native tool_call stream fragments into complete calls."""

    def __init__(self) -> None:
        self._by_index: dict[int, dict[str, Any]] = {}
        self._order: list[int] = []

    def add_deltas(self, deltas: list[ToolCallDelta]) -> None:
        """Merge streaming fragments into the per-index assembly slots."""
        for delta in deltas:
            idx = int(delta.index)
            slot = self._by_index.get(idx)
            if slot is None:
                slot = {"id": "", "name": "", "arguments": ""}
                self._by_index[idx] = slot
                self._order.append(idx)
            if delta.id:
                slot["id"] = delta.id
            if delta.name:
                slot["name"] += delta.name
            if delta.arguments:
                slot["arguments"] += delta.arguments

    def complete(self) -> list[AssembledToolCall]:
        """Return fully assembled tool calls, in arrival order."""
        out: list[AssembledToolCall] = []
        for idx in self._order:
            slot = self._by_index[idx]
            name = (slot.get("name") or "").strip()
            if not name:
                continue
            raw = slot.get("arguments") or ""
            if not raw.strip():
                args: Any = {}
            else:
                try:
                    parsed = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    args = raw
                else:
                    args = parsed if isinstance(parsed, dict) else raw
            out.append(
                AssembledToolCall(
                    id=slot.get("id") or f"call_{idx}",
                    name=name,
                    arguments=args,
                )
            )
        return out


# --- Typed errors for the LiteLLM call path (fail-closed) ---
# Config problems (missing key / disabled LLM) raise LLMNotConfiguredError from
# admin.llm.exceptions; call-time failures raise the types below.


class LLMCallError(Exception):
    """Base class for LLM call failures surfaced by the LiteLLM client."""


class LLMNonRetryableError(LLMCallError):
    """Provider rejected the request (auth, model_not_found, 400, ...).

    Raised immediately: retrying cannot succeed, so no retries are attempted.
    """

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMTransientError(LLMCallError):
    """Transient provider failure (rate limit / timeout / 5xx / connection).

    Raised only after bounded retries are exhausted.
    """


class LLMTimeoutError(LLMTransientError, TimeoutError):
    """LLM call exceeded the configured connect/read timeout.

    Also a ``TimeoutError`` so existing ``except asyncio.TimeoutError``
    degraded-mode handlers keep working.
    """


class ChatGenerationResult:
    """Chat generation result object for processing LLM stream output."""

    def __init__(self, chunk: ChatChunk | None = None):
        """Initialize the instance."""
        self.reasoning = ""
        self.response = ""
        self.thinking = False
        self.thinking_tag = ""
        self.unprocessed = ""
        self._pending_reasoning = ""
        self.native_reasoning = False
        self.thinking_pairs = [("<think>", "</think>"), ("<reasoning>", "</reasoning>")]
        self._buffer = ""
        self._raw: str = ""
        self.tool_accumulator = ToolCallAccumulator()
        if chunk:
            self.add_chunk(chunk)

    @property
    def tool_calls(self) -> list[AssembledToolCall]:
        """Complete native tool calls assembled from the stream so far."""
        return self.tool_accumulator.complete()

    def add_chunk(self, chunk: ChatChunk) -> ChatChunk:
        """Consume a chunk of output (text + native tool-call fragments)."""
        deltas = chunk.get("tool_call_deltas") or []
        if deltas:
            self.tool_accumulator.add_deltas(deltas)
        out = self._add_text_chunk(chunk)
        if deltas:
            merged: dict[str, Any] = dict(out)
            merged["tool_call_deltas"] = deltas
            return merged  # type: ignore[return-value]
        return out

    def _add_text_chunk(self, chunk: ChatChunk) -> ChatChunk:
        """Consume a text chunk of output.

        Implements a state-machine that recognises <think> and </think> tags,
        collecting the inner text as reasoning and treating everything outside
        those tags as the final response.
        """
        # If the chunk already contains native reasoning we simply forward it.
        if chunk["reasoning_delta"]:
            self.native_reasoning = True
            self.reasoning += chunk["reasoning_delta"]
            self.response += chunk["response_delta"]
            return ChatChunk(
                response_delta=chunk["response_delta"], reasoning_delta=chunk["reasoning_delta"]
            )

        # Append the incoming characters to the raw buffer.
        self._raw += chunk["response_delta"]

        # Extract any complete <think>...</think> blocks
        while True:
            open_idx = self._raw.find("<think>")
            if open_idx == -1:
                break
            close_idx = self._raw.find("</think>", open_idx)
            if close_idx == -1:
                break
            # Capture reasoning between the tags.
            self.reasoning += self._raw[open_idx + len("<think>") : close_idx]
            # Remove the processed segment from the buffer.
            self._raw = self._raw[:open_idx] + self._raw[close_idx + len("</think>") :]

        # Handle incomplete opening tag
        if self._raw.startswith("<think>") and "</think>" not in self._raw:
            self.response = ""
            return ChatChunk(response_delta="", reasoning_delta="")
        else:
            self.response = self._raw
            # Return the delta that was actually added
            return ChatChunk(response_delta=chunk["response_delta"], reasoning_delta="")

    def _process_thinking_chunk(self, chunk: ChatChunk) -> ChatChunk:
        """Process thinking chunk with buffered content."""
        response_delta = self.unprocessed + chunk["response_delta"]
        self.unprocessed = ""
        return self._process_thinking_tags(response_delta, chunk["reasoning_delta"])

    def _process_thinking_tags(self, response: str, reasoning: str) -> ChatChunk:
        """Process opening/closing thinking tags in response text."""
        combined = self._buffer + response
        self._buffer = ""

        if not self.thinking:
            if combined.startswith("<think>"):
                self.thinking = True
                self.thinking_tag = "</think>"
                remaining = combined[len("<think>") :]
                close_idx = remaining.find("</think>")
                if close_idx != -1:
                    reasoning = remaining[:close_idx]
                    response = remaining[close_idx + len("</think>") :]
                    self.thinking = False
                    self.thinking_tag = ""
                    return ChatChunk(response_delta=response, reasoning_delta=reasoning)
                self._pending_reasoning = remaining
                return ChatChunk(response_delta="", reasoning_delta="")

            if "<think".startswith(combined):
                self._buffer = combined
                return ChatChunk(response_delta="", reasoning_delta="")

            response = combined
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
        """Split text at partial tag boundary."""
        for size in range(len(tag) - 1, 0, -1):
            if text.endswith(tag[:size]):
                return text[:-size], text[-size:]
        return text, ""

    def _is_partial_opening_tag(self, text: str, opening_tag: str) -> bool:
        """Check if text is a partial opening tag."""
        for i in range(1, len(opening_tag)):
            if text == opening_tag[:i]:
                return True
        return False

    def _is_partial_closing_tag(self, text: str) -> bool:
        """Check if text ends with partial closing tag."""
        if not self.thinking_tag or not text:
            return False
        max_check = min(len(text), len(self.thinking_tag) - 1)
        for i in range(1, max_check + 1):
            if text.endswith(self.thinking_tag[:i]):
                return True
        return False

    def output(self) -> ChatChunk:
        """Return final output chunk."""
        response = self.response
        reasoning = self.reasoning
        if self.unprocessed:
            if reasoning and not response:
                reasoning += self.unprocessed
            else:
                response += self.unprocessed
        return ChatChunk(response_delta=response, reasoning_delta=reasoning)
