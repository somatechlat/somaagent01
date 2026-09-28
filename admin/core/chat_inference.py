"""Chat LLM inference: model selection and streaming."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, cast, Dict, List, Optional

from admin.core.chat_context import to_langchain_messages
from admin.core.context import BuiltContext
from admin.core.model_router import detect_required_capabilities, select_model, SelectedModel

logger = logging.getLogger(__name__)


class ChatInferenceEngine:
    """Handles model selection and LLM streaming for chat turns."""

    def __init__(self, cb_llm: Any, metrics: Any) -> None:
        self._cb_llm = cb_llm
        self._metrics = metrics

    async def select_model(
        self,
        user_message: str,
        attachments: List[Dict[str, Any]],
        capsule_body: Dict[str, Any],
        tenant_id: str,
    ) -> SelectedModel:
        """Select the best model for the turn."""
        caps = detect_required_capabilities(message=user_message, attachments=attachments)
        return cast(
            SelectedModel,
            await self._cb_llm.call(
                select_model,
                required_capabilities=caps,
                capsule_body=capsule_body,
                tenant_id=tenant_id,
            ),
        )

    async def stream_llm(
        self,
        llm: Any,
        context: BuiltContext,
        history: List[Dict[str, str]],
        user_message: str,
        tools_for_llm: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM.

        Raises CircuitBreakerError or asyncio.TimeoutError on failure.
        """
        messages = to_langchain_messages(context, history, user_message)

        call_kwargs: Dict[str, Any] = {"messages": messages}
        if tools_for_llm is not None:
            call_kwargs["tools"] = tools_for_llm if tools_for_llm else None

        stream = cast(
            AsyncIterator[Any],
            await self._cb_llm.call(llm._astream, **call_kwargs),
        )
        async for chunk in stream:
            token = (
                str(chunk.message.content)
                if hasattr(chunk, "message") and hasattr(chunk.message, "content")
                else ""
            )
            if token:
                yield token


__all__ = [
    "ChatInferenceEngine",
]
