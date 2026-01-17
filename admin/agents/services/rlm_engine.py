"""
RLMEngine - Recursive Language Model Engine.

Implements the Controller-Executor architecture:
- Controller: LLM proposes actions
- Executor: Runs tools, observes results
- MemoryService: Sub-LM queries for context retrieval

SRS Source: SRS-RLM-ENGINE-2026-01-16

Applied Personas:
- PhD Developer: MIT CSAIL compliant architecture
- PhD Analyst: FC-STOMP cognitive loop
- Security: Bounded iterations, no infinite loops
- Performance: Async, Temporal-ready
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from admin.core.agentiq import derive_all_settings

if TYPE_CHECKING:
    from admin.core.models import Capsule

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Type of action proposed by Controller."""

    MEMORY_QUERY = "memory_query"  # Query MemoryService Sub-LM
    TOOL_CALL = "tool_call"  # Execute a tool
    COMPLETE = "complete"  # Task complete
    REASONING = "reasoning"  # Continue reasoning


@dataclass
class RLMAction:
    """Action proposed by the Controller LLM."""

    action_type: ActionType
    content: str = ""
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class RLMState:
    """State of the RLM execution loop."""

    iteration: int = 0
    observations: List[str] = field(default_factory=list)
    reasoning_trace: List[str] = field(default_factory=list)
    result: Optional[str] = None
    is_complete: bool = False


class MemoryServiceProtocol(Protocol):
    """Protocol for memory/recall service."""

    async def query(
        self,
        question: str,
        capsule_id: str,
        memory_config: Dict[str, Any],
    ) -> str:
        """Query memory service for context."""
        ...


class ExecutorProtocol(Protocol):
    """Protocol for tool execution."""

    async def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> str:
        """Execute tool and return observation."""
        ...


class ControllerProtocol(Protocol):
    """Protocol for LLM controller."""

    async def propose(
        self,
        state: RLMState,
        context: str,
        max_tokens: int,
    ) -> RLMAction:
        """Propose next action."""
        ...


class RLMEngine:
    """
    Recursive Language Model Engine.

    Implements the Controller-Executor-Memory architecture:
    - Controller (LLM): Proposes actions
    - Executor (Tools): Executes and observes
    - MemoryService: Sub-LM queries for retrieval

    All settings derived from capsule.body.persona.knobs via AgentIQ.
    """

    def __init__(
        self,
        controller: Optional[ControllerProtocol] = None,
        executor: Optional[ExecutorProtocol] = None,
        memory_service: Optional[MemoryServiceProtocol] = None,
    ) -> None:
        """
        Initialize RLMEngine.

        Args:
            controller: LLM for action proposal
            executor: Tool executor
            memory_service: Memory/recall service
        """
        self._controller = controller
        self._executor = executor
        self._memory_service = memory_service

    async def execute(
        self,
        capsule: "Capsule",
        task: str,
        context: str = "",
    ) -> str:
        """
        Execute RLM loop for a task.

        Args:
            capsule: Capsule with configuration
            task: Task to execute
            context: Optional context

        Returns:
            Result string
        """
        # 1. Derive settings from AgentIQ
        settings = derive_all_settings(capsule)
        max_iterations = settings.rlm_iterations
        reasoning_budget = settings.thinking_budget
        memory_enabled = settings.brain_query_enabled

        logger.info(
            "RLM starting: max_iter=%d, reasoning=%d, memory=%s",
            max_iterations,
            reasoning_budget,
            memory_enabled,
        )

        # 2. Initialize state
        state = RLMState()
        full_context = f"{context}\n\nTask: {task}"

        # 3. Controller-Executor loop
        for iteration in range(max_iterations):
            state.iteration = iteration + 1

            # Controller: Propose action
            if self._controller:
                action = await self._controller.propose(
                    state=state,
                    context=full_context,
                    max_tokens=reasoning_budget,
                )
            else:
                # No Controller configured - default to complete
                action = RLMAction(
                    action_type=ActionType.COMPLETE,
                    content=f"[No LLM configured] Task received: {task}",
                )

            state.reasoning_trace.append(
                f"Iter {state.iteration}: {action.action_type.value}"
            )

            # Handle action
            if action.action_type == ActionType.COMPLETE:
                state.result = action.content
                state.is_complete = True
                break

            elif action.action_type == ActionType.MEMORY_QUERY and memory_enabled:
                # Sub-LM query to MemoryService
                observation = await self._query_memory(capsule, action.content)
                state.observations.append(f"Memory: {observation}")
                full_context += f"\n[Memory Result]: {observation}"

            elif action.action_type == ActionType.TOOL_CALL:
                # Executor runs tool
                observation = await self._execute_tool(
                    action.tool_name or "",
                    action.tool_args,
                )
                state.observations.append(f"Tool {action.tool_name}: {observation}")
                full_context += f"\n[Tool Result]: {observation}"

            elif action.action_type == ActionType.REASONING:
                # Continue reasoning
                state.reasoning_trace.append(action.content)
                full_context += f"\n[Reasoning]: {action.content}"

        # 4. Return result
        if state.result:
            return state.result

        # Max iterations reached without complete
        return f"[RLM] Max iterations ({max_iterations}) reached. Last state: {state.reasoning_trace[-1] if state.reasoning_trace else 'empty'}"

    async def _query_memory(
        self,
        capsule: "Capsule",
        question: str,
    ) -> str:
        """Query MemoryService for context retrieval."""
        if not self._memory_service:
            return "[MemoryService not configured]"

        try:
            body: Dict[str, Any] = capsule.body or {}
            memory_config = body.get("persona", {}).get("memory", {})

            return await self._memory_service.query(
                question=question,
                capsule_id=str(capsule.id),
                memory_config=memory_config,
            )
        except Exception as exc:
            logger.warning("MemoryService.query() failed: %s", exc)
            return f"[Memory error: {exc}]"

    async def _execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
    ) -> str:
        """Execute tool via Executor."""
        if not self._executor:
            return "[Executor not configured]"

        try:
            return await self._executor.execute(tool_name, args)
        except Exception as exc:
            logger.warning("Executor.execute() failed: %s", exc)
            return f"[Tool error: {exc}]"
