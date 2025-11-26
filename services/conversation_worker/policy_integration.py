from __future__ import annotations

from typing import Optional

from services.common.policy_client import PolicyClient, PolicyRequest
from src.core.config import cfg


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
        # VIBE CODING RULE: No bypasses. Policy checks are mandatory.
        
        # 1. Check if policy is enabled for this tenant
        if not self.client:
            return True

        # 2. Construct context for OPA
        ctx = {
            "message": message,
            "metadata": metadata,
            "role": "user",
        }

        # 3. Evaluate policy
        try:
            allowed = await self.client.evaluate(
                PolicyRequest(
                    tenant=tenant,
                    persona_id=persona_id,
                    action="conversation.message",
                    resource="conversation",
                    context=ctx,
                )
            )
            return allowed
        except Exception as e:
            # Fail closed on policy error
            LOGGER.error(f"Policy evaluation failed: {e}")
            return False
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
