"""SomaAgent package - Agent components and orchestration.

This package contains extracted components from the main agent module.
The Agent class in agent.py imports directly from these submodules.

Primary modules (actively used by Agent):
- agent_context: AgentContext, AgentConfig, UserMessage
- cognitive: Cognitive state and neuromodulation functions
- somabrain_integration: SomaBrain memory operations
- error_handler: Exception classes
- conversation_orchestrator: LoopData

Utility modules (available for external use):
- tool_selector: Standalone tool selection utilities
- response_generator: LLM model utilities
- input_processor: Message processing utilities
"""

# Primary exports - used by agent.py
from python.somaagent.agent_context import (
    AgentContext, AgentContextType, AgentConfig, UserMessage
)
from python.somaagent.error_handler import (
    InterventionException, HandledException
)
from python.somaagent.conversation_orchestrator import LoopData

# Cognitive and SomaBrain modules - imported as namespaces by agent.py
from python.somaagent import cognitive
from python.somaagent import somabrain_integration

__all__ = [
    # Primary exports (used by agent.py)
    "AgentContext",
    "AgentContextType",
    "AgentConfig",
    "UserMessage",
    "InterventionException",
    "HandledException",
    "LoopData",
    # Module namespaces
    "cognitive",
    "somabrain_integration",
]
