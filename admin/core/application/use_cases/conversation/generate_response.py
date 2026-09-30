"""Generate response use case.

This use case handles LLM response generation with streaming,
tool calling, and escalation support.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from services.conversation_worker.llm_metrics import (
    record_llm_failure,
    record_llm_success,
)

LOGGER = logging.getLogger(__name__)


class GatewayClientProtocol(Protocol):
    """Protocol for gateway LLM invocation."""

    async def invoke_stream(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> tuple[str, Dict[str, int]]:
        """Stream invocation.

        Args:
            url: The gateway URL.
            payload: Request payload.
            headers: Request headers.

        Returns:
            Tuple of response text and usage dict.
        """
        ...

    async def invoke(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Non-streaming invocation.

        Args:
            url: The gateway URL.
            payload: Request payload.
            headers: Request headers.

        Returns:
            Response dict.
        """
        ...


class PublisherProtocol(Protocol):
    """Protocol for event publishing."""

    async def publish(
        self,
        topic: str,
        payload: Any,
        *,
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
    ) -> Any:
        """Publish an event.

        Args:
            topic: Target topic.
            payload: Event payload.
            dedupe_key: Deduplication key.
            session_id: Session identifier.
            tenant: Tenant identifier.

        Returns:
            Publish result.
        """
        ...


@dataclass
class GenerateResponseInput:
    """Input for generate response use case."""

    session_id: str
    persona_id: Optional[str]
    messages: List[Any]  # List of ChatMessage
    tenant: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    base_url: Optional[str] = None
    base_metadata: Dict[str, Any] = field(default_factory=dict)
    tools_enabled: bool = False


@dataclass
class GenerateResponseOutput:
    """Output from generate response use case."""

    text: str
    usage: Dict[str, int]
    model: str
    latency: float
    success: bool = True
    error: Optional[str] = None
    confidence: Optional[float] = None


def normalize_usage(raw: Dict[str, Any] | None) -> Dict[str, int]:
    """Normalize usage payload to standard format."""
    payload: Dict[str, Any] = raw or {}
    prompt = payload.get("input_tokens", payload.get("prompt_tokens", 0))
    completion = payload.get("output_tokens", payload.get("completion_tokens", 0))
    try:
        prompt_val = int(prompt) if prompt is not None else 0
    except Exception:
        prompt_val = 0
    try:
        completion_val = int(completion) if completion is not None else 0
    except Exception:
        completion_val = 0
    return {"input_tokens": max(prompt_val, 0), "output_tokens": max(completion_val, 0)}


# Values that are placeholders rather than model identifiers. The parameter
# default used to be the literal ``"unknown"``, which would have reached the
# gateway as if a model by that name existed (VIBE §1 / §4).
_PLACEHOLDER_MODELS = frozenset({"unknown", "n/a", "none", "tbd", "todo", "placeholder", ""})


class GenerateResponseUseCase:
    """Use case for generating LLM responses."""

    def __init__(
        self,
        gateway_base: str,
        internal_token: str | None,
        publisher: PublisherProtocol,
        outbound_topic: str,
        default_model: str | None,
    ):
        """Initialize the instance.

        ``internal_token`` is a credential, not a string. It is the Vault
        secret ``gateway_internal_token`` and it is sent as ``X-Internal-Token``
        on every internal gateway call.

        This used to accept anything and the call sites did
        ``get_credential(...) or ""``, so an absent secret became an empty
        header on a live request. An empty string is a dummy credential: it
        crosses a gate looking like a value nobody issued. A missing secret
        refuses construction here instead (VIBE Rule 91 / Rule 164).

        ``default_model`` is required and is the model actually sent when the
        caller names none. Its parameter default used to be the placeholder
        ``"unknown"``.
        """

        # Validate before anything is stored or contacted.
        if not isinstance(internal_token, str) or not internal_token.strip():
            raise ValueError(
                "internal_token is required: it is the Vault credential "
                "gateway_internal_token, sent as X-Internal-Token on every "
                "internal gateway call. An empty, blank or missing value is not "
                "a credential and must not be sent. Set "
                "secret/agent/credentials/gateway_internal_token in Vault."
            )

        if not isinstance(default_model, str) or not default_model.strip():
            raise ValueError(
                "default_model is required: it is the model sent to the gateway "
                "when the caller names none. An empty or missing value is not a "
                "model. Set SA01_LLM_MODEL to a real model identifier."
            )
        resolved_model = default_model.strip()
        if resolved_model.lower() in _PLACEHOLDER_MODELS:
            raise ValueError(
                "default_model must name a real model, not a placeholder. "
                f"Got {resolved_model!r}. Set SA01_LLM_MODEL to a real model "
                "identifier."
            )

        self._gateway_base = gateway_base.rstrip("/")
        self._internal_token = internal_token.strip()
        self._publisher = publisher
        self._outbound_topic = outbound_topic
        self._default_model = resolved_model

    async def execute(self, input_data: GenerateResponseInput) -> GenerateResponseOutput:
        """Generate LLM response."""

        model = input_data.model or self._default_model
        start_time = time.perf_counter()

        try:
            # Build request
            overrides = self._build_overrides(input_data)
            payload = {
                "role": "dialogue",
                "session_id": input_data.session_id,
                "persona_id": input_data.persona_id,
                "tenant": input_data.tenant,
                "messages": [self._message_to_dict(m) for m in input_data.messages],
                "overrides": overrides,
            }
            # No ``or ""`` here. The constructor refuses to run without a real
            # token, so this is always a credential — and writing
            # ``x or ""`` is what turned a missing secret into an empty header.
            headers = {"X-Internal-Token": self._internal_token}

            # Try streaming first
            try:
                text, usage, confidence = await self._stream_response(
                    input_data, payload, headers
                )
            except Exception as stream_error:
                LOGGER.warning("Streaming failed, falling back to non-stream: %s", stream_error)
                text, usage, confidence = await self._invoke_response(payload, headers)

            latency = time.perf_counter() - start_time

            if not text.strip():
                text = "I encountered an issue generating a response."

            result = GenerateResponseOutput(
                text=text,
                usage=normalize_usage(usage),
                model=model,
                latency=latency,
                confidence=confidence,
                success=True,
            )
            usage_norm = result.usage or {"input_tokens": 0, "output_tokens": 0}
            record_llm_success(
                model=model,
                input_tokens=usage_norm.get("input_tokens", 0),
                output_tokens=usage_norm.get("output_tokens", 0),
                elapsed=latency,
            )
            return result

        except Exception as e:
            LOGGER.exception("Response generation failed")
            record_llm_failure(model=model)
            return GenerateResponseOutput(
                text="I encountered an error while generating a reply.",
                usage={"input_tokens": 0, "output_tokens": 0},
                model=model,
                latency=time.perf_counter() - start_time,
                success=False,
                error=str(e),
            )

    def _build_overrides(self, input_data: GenerateResponseInput) -> Dict[str, Any]:
        """Build overrides dict, omitting empty values.

        The model is always present. ``execute`` resolves
        ``input_data.model or self._default_model``, and that resolved value is
        what the gateway must use. Keying this off ``input_data.model`` alone
        meant the configured default was computed and then discarded, so a
        deployment that set one silently got the gateway's own default instead.
        """
        ov: Dict[str, Any] = {
            "model": (input_data.model or self._default_model).strip(),
        }
        if input_data.base_url and input_data.base_url.strip():
            ov["base_url"] = input_data.base_url
        if input_data.temperature is not None:
            ov["temperature"] = input_data.temperature
        return ov

    def _message_to_dict(self, msg: Any) -> Dict[str, str]:
        """Convert message to dict format."""
        if hasattr(msg, "__dict__"):
            return msg.__dict__
        if isinstance(msg, dict):
            return msg
        return {"role": "user", "content": str(msg)}

    async def _stream_response(
        self,
        input_data: GenerateResponseInput,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> tuple[str, Dict[str, int], Optional[float]]:
        """Stream response from gateway.

        The model travels in ``payload["overrides"]["model"]``. It used to be
        passed in here as well and never read — a parameter that promised
        influence over the request and had none.
        """
        import httpx

        url = f"{self._gateway_base}/v1/llm/invoke/stream"
        buffer: List[str] = []
        usage = {"input_tokens": 0, "output_tokens": 0}
        confidence: Optional[float] = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.is_error:
                    body = await resp.aread()
                    raise RuntimeError(f"Gateway error {resp.status_code}: {body.decode()[:512]}")

                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except Exception:
                        continue

                    choices = chunk.get("choices")
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        buffer.append(content)

                        # Publish streaming event
                        await self._publish_stream_event(input_data, "".join(buffer), len(buffer))

                    chunk_usage = chunk.get("usage")
                    if isinstance(chunk_usage, dict):
                        usage["input_tokens"] = int(
                            chunk_usage.get("prompt_tokens", usage["input_tokens"])
                        )
                        usage["output_tokens"] = int(
                            chunk_usage.get("completion_tokens", usage["output_tokens"])
                        )

        text = "".join(buffer)
        if not text:
            raise RuntimeError("Empty response from streaming")

        return text, usage, confidence

    async def _invoke_response(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> tuple[str, Dict[str, int], Optional[float]]:
        """Non-streaming response from gateway."""
        import httpx

        url = f"{self._gateway_base}/v1/llm/invoke"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.is_error:
                raise RuntimeError(f"Gateway error {resp.status_code}: {resp.text[:512]}")

            data = resp.json()
            text = data.get("content", "")
            usage = data.get("usage", {"input_tokens": 0, "output_tokens": 0})
            confidence = data.get("confidence")

            if not text:
                raise RuntimeError("Empty response from gateway")

            return text, usage, confidence

    async def _publish_stream_event(
        self,
        input_data: GenerateResponseInput,
        content: str,
        stream_index: int,
    ) -> None:
        """Publish streaming event."""
        try:
            metadata = dict(input_data.base_metadata)
            metadata["source"] = "llm"
            metadata["status"] = "streaming"
            metadata["stream_index"] = stream_index

            event = {
                "event_id": str(uuid.uuid4()),
                "session_id": input_data.session_id,
                "persona_id": input_data.persona_id,
                "role": "assistant",
                "message": content,
                "metadata": metadata,
                "version": "sa01-v1",
                "type": "assistant.stream",
            }

            await self._publisher.publish(
                self._outbound_topic,
                event,
                dedupe_key=event.get("event_id"),
                session_id=input_data.session_id,
                tenant=input_data.tenant,
            )
        except Exception:
            LOGGER.debug("Failed to publish stream event", exc_info=True)
