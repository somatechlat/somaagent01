"""Policy adapter wrapping PolicyClient.

This adapter implements PolicyAdapterPort by delegating ALL operations
to the existing production PolicyClient implementation.
"""

from typing import Optional

from services.common.policy_client import PolicyClient, PolicyRequest
# from src.core.domain.ports.adapters.policy_adapter import (
    PolicyAdapterPort,
    PolicyRequestDTO,
)


class OPAPolicyAdapter(PolicyAdapterPort):
    """Implements PolicyAdapterPort using existing PolicyClient.

    Delegates ALL operations to services.common.policy_client.PolicyClient.
    """

    def __init__(
        self,
        client: Optional[PolicyClient] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize adapter with existing client or create new one.

        Args:
            client: Existing PolicyClient instance (preferred)
            base_url: OPA base URL (used if client not provided)
        """
        self._client = client or PolicyClient(base_url=base_url)

    async def evaluate(self, request: PolicyRequestDTO) -> bool:
        policy_request = PolicyRequest(
            tenant=request.tenant,
            persona_id=request.persona_id,
            action=request.action,
            resource=request.resource,
            context=request.context,
        )
        return await self._client.evaluate(policy_request)

    async def close(self) -> None:
        await self._client.close()
