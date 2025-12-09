"""SomaAgent package - Agent components and orchestration.

This package contains extracted components from the main agent module:
- input_processor: User message handling
- tool_selector: Tool selection and execution
- response_generator: LLM calls and response handling
- error_handler: Exception handling
- conversation_orchestrator: Message flow management
- context_builder: LLM context building
- capsule: Capsule management
"""

from python.somaagent.input_processor import UserMessage, process_user_message, process_intervention
from python.somaagent.tool_selector import get_tool, process_tool_request, extract_tool_from_response
from python.somaagent.response_generator import (
    get_chat_model, get_utility_model, call_chat_model, call_utility_model, apply_neuromodulation
)
from python.somaagent.error_handler import (
    InterventionException, HandledException, handle_critical_exception,
    is_recoverable_error, format_error_for_llm
)
from python.somaagent.conversation_orchestrator import LoopData, run_message_loop, process_chain

__all__ = [
    # Input processing
    "UserMessage",
    "process_user_message",
    "process_intervention",
    # Tool selection
    "get_tool",
    "process_tool_request",
    "extract_tool_from_response",
    # Response generation
    "get_chat_model",
    "get_utility_model",
    "call_chat_model",
    "call_utility_model",
    "apply_neuromodulation",
    # Error handling
    "InterventionException",
    "HandledException",
    "handle_critical_exception",
    "is_recoverable_error",
    "format_error_for_llm",
    # Conversation orchestration
    "LoopData",
    "run_message_loop",
    "process_chain",
]
