"""Execute tool use case - orchestrates tool execution.

This use case coordinates:
- Policy evaluation via PolicyAdapterPort
- Tool execution via ExecutionEnginePort
- Event publishing via EventBusPort

It contains NO infrastructure code - only business logic coordination.
"""

# from src.core.application.dto import ExecuteToolInput, ExecuteToolOutput
# from src.core.domain.ports import (
    EventBusPort,
    ExecutionEnginePort,
    ExecutionLimitsDTO,
    PolicyAdapterPort,
    PolicyRequestDTO,
)


class ExecuteToolUseCase:
    """Orchestrates tool execution through domain ports.

    This use case:
    1. Evaluates policy to check if execution is allowed
    2. Executes the tool with resource limits
    3. Publishes execution result event
    """

    def __init__(
        self,
        policy_adapter: PolicyAdapterPort,
        execution_engine: ExecutionEnginePort,
        event_bus: EventBusPort,
    ):
        self._policy = policy_adapter
        self._engine = execution_engine
        self._bus = event_bus

    async def execute(self, input_data: ExecuteToolInput) -> ExecuteToolOutput:
        """Execute a tool with policy enforcement.

        Args:
            input_data: Tool execution input

        Returns:
            Execution output with status and result
        """
        # 1. Evaluate policy
        policy_request = PolicyRequestDTO(
            tenant=input_data.tenant,
            persona_id=input_data.persona_id,
            action="execute",
            resource=f"tool:{input_data.tool_name}",
            context={
                "session_id": input_data.session_id,
                "args": input_data.args,
            },
        )

        allowed = await self._policy.evaluate(policy_request)
        if not allowed:
            return ExecuteToolOutput(
                status="denied",
                result={"error": "Policy denied tool execution"},
                execution_time=0.0,
                logs=["Policy evaluation: DENIED"],
            )

        # 2. Execute tool with limits
        limits = ExecutionLimitsDTO(
            timeout_seconds=30.0,
            max_memory_mb=512,
            max_output_bytes=1024 * 1024,
        )

        result = await self._engine.execute(
            tool_name=input_data.tool_name,
            args=input_data.args,
            limits=limits,
        )

        # 3. Publish execution event
        await self._bus.publish(
            topic="tool.execution.completed",
            payload={
                "tool_name": input_data.tool_name,
                "session_id": input_data.session_id,
                "status": result.status,
                "execution_time": result.execution_time,
            },
        )

        return ExecuteToolOutput(
            status=result.status,
            result=result.payload,
            execution_time=result.execution_time,
            logs=result.logs,
        )
