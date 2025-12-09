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
# Cognitive and SomaBrain modules - imported as namespaces by agent.py
from python.somaagent import cognitive, somabrain_integration
from python.somaagent.agent_context import AgentConfig, AgentContext, AgentContextType, UserMessage
from python.somaagent.conversation_orchestrator import LoopData
from python.somaagent.error_handler import HandledException, InterventionException

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
