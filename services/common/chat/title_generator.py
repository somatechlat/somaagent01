"""Title generation service for conversations.

Extracted from chat_service.py per VIBE Rule 245 (650-line max).
Handles automatic conversation title generation using utility models.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async

from services.common.chat.metrics import CHAT_LATENCY, CHAT_REQUESTS

if TYPE_CHECKING:
    from services.common.chat_schemas import Message


class TitleGenerator:
    """Service for generating conversation titles.

    Extracted from ChatService to enforce 650-line limit.
    """

    async def generate_title(
        self, conversation_id: str, messages: list["Message"]
    ) -> str:
        """Generate conversation title using utility model."""
        from langchain_core.messages import HumanMessage, SystemMessage

        from admin.chat.models import Conversation as ConversationModel
        from admin.core.helpers.settings_defaults import get_default_settings
        from admin.llm.services.litellm_client import get_chat_model

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def get_agent_id():
                conv = (
                    ConversationModel.objects.filter(id=conversation_id)
                    .only("agent_id")
                    .first()
                )
                return str(conv.agent_id) if conv else "default"

            agent_id = await get_agent_id()
            settings = get_default_settings(agent_id=agent_id)
            provider = settings.util_model_provider or settings.chat_model_provider
            model_name = settings.util_model_name or settings.chat_model_name
            if "/" in model_name:
                model_provider, model_value = model_name.split("/", 1)
                if not provider or provider == model_provider:
                    provider, model_name = model_provider, model_value

            util_kwargs = dict(
                settings.util_model_kwargs or settings.chat_model_kwargs or {}
            )
            if settings.util_model_api_base:
                util_kwargs.setdefault("api_base", settings.util_model_api_base)

            llm = get_chat_model(provider=provider, name=model_name, **util_kwargs)
            context = "\n".join(f"{m.role}: {m.content[:200]}" for m in messages[:5])
            title_tokens = []
            async for chunk in llm._astream(
                messages=[
                    SystemMessage(
                        content="You generate short chat titles. Return a concise title (max 8 words), no quotes."
                    ),
                    HumanMessage(content=context),
                ]
            ):
                token = (
                    str(chunk.message.content)
                    if hasattr(chunk, "message") and hasattr(chunk.message, "content")
                    else ""
                )
                if token:
                    title_tokens.append(token)

            title = "".join(title_tokens).strip() or (
                messages[0].content[:50] if messages else "New Conversation"
            )

            @sync_to_async
            def update_title():
                ConversationModel.objects.filter(id=conversation_id).update(title=title)

            await update_title()
            CHAT_LATENCY.labels(method="generate_title").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="generate_title", result="success").inc()
            return title
        except Exception:
            CHAT_LATENCY.labels(method="generate_title").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="generate_title", result="error").inc()
            return messages[0].content[:50] if messages else "New Conversation"


__all__ = ["TitleGenerator"]
