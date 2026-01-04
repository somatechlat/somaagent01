"""Policy adapter port interface.

This port defines the contract for policy evaluation operations.
The interface matches the existing PolicyClient methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.common.policy_client.PolicyClient
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PolicyRequestDTO:
    """Data transfer object for policy requests.

    Mirrors services.common.policy_client.PolicyRequest structure.
    """

    tenant: str
    persona_id: Optional[str]
    action: str
    resource: str
    context: Dict[str, Any]


class PolicyAdapterPort(ABC):
    """Abstract interface for policy evaluation.

    This port wraps the existing PolicyClient implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def evaluate(self, request: PolicyRequestDTO) -> bool:
        """Evaluate a policy request.

        Args:
            request: Policy request containing:
                - tenant: Tenant identifier
                - persona_id: Persona identifier
                - action: Action being performed
                - resource: Resource being accessed
                - context: Additional context

        Returns:
            True if allowed, False if denied
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the policy client and release resources."""
        ...