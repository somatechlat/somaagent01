"""LiteLLM Schemas - Data classes and TypedDicts for LLM operations.

Extracted from litellm_client.py for 650-line compliance.
"""

from __future__ import annotations

from typing import TypedDict


class ChatChunk(TypedDict):
    """Simplified response chunk for chat models."""

    response_delta: str
    reasoning_delta: str


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
        if chunk:
            self.add_chunk(chunk)

    def add_chunk(self, chunk: ChatChunk) -> ChatChunk:
        """Consume a chunk of output.

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
        else:
            self.response = self._raw
        return ChatChunk(response_delta="", reasoning_delta="")

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
