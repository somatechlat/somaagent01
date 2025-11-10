from __future__ import annotations

from typing import Optional

from services.common.policy_client import PolicyClient, PolicyRequest


class ConversationPolicyEnforcer:
    """Centralizes policy checks required by the conversation worker."""

    def __init__(self, policy_client: PolicyClient | None = None) -> None:
        self.policy = policy_client or PolicyClient()

    async def check_message_policy(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        message: str,
        metadata: dict,
    ) -> bool:
        """Check whether an inbound user message is permitted."""
        # Hard delete of LOCAL bypass: always enforce policy
        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="conversation.send",
            resource="message",
            context={
                "message_length": len(message or ""),
                "metadata": metadata,
            },
        )
        return await self.policy.evaluate(request)

    async def check_memory_write_policy(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        memory_data: dict,
    ) -> bool:
        """Check whether the conversation worker can write to long-term memory."""

        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="memory.write",
            resource="conversation_memory",
            context=memory_data,
        )
        return await self.policy.evaluate(request)

    async def check_tool_request_policy(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        tool_name: str,
        tool_args: dict,
    ) -> bool:
        """Check whether a tool request issued by the conversation worker is allowed."""

        request = PolicyRequest(
            tenant=tenant,
            persona_id=persona_id,
            action="tool.request",
            resource=tool_name,
            context=tool_args,
        )
        return await self.policy.evaluate(request)
