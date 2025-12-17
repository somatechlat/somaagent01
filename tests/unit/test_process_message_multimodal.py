
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.application.use_cases.conversation.process_message import (
    ProcessMessageInput,
    ProcessMessageUseCase,
)
from services.common.job_planner import JobPlan

@pytest.fixture
def mock_deps():
    return {
        "session_repo": AsyncMock(),
        "policy_enforcer": AsyncMock(),
        "memory_client": AsyncMock(),
        "publisher": AsyncMock(),
        "context_builder": AsyncMock(),
        "response_generator": AsyncMock(),
        "analyzer": MagicMock(),
    }

@pytest.fixture
def use_case(mock_deps):
    uc = ProcessMessageUseCase(
        session_repo=mock_deps["session_repo"],
        policy_enforcer=mock_deps["policy_enforcer"],
        memory_client=mock_deps["memory_client"],
        publisher=mock_deps["publisher"],
        context_builder=mock_deps["context_builder"],
        response_generator=mock_deps["response_generator"],
        outbound_topic="test.topic",
        analyzer=mock_deps["analyzer"],
    )
    # Setup default policy allowing
    mock_deps["policy_enforcer"].check_message_policy.return_value = True
    
    # Setup default context build
    mock_deps["context_builder"].build_for_turn.return_value = MagicMock(messages=[])
    
    return uc

@pytest.mark.asyncio
async def test_extract_multimodal_plan(use_case, mock_deps):
    """Test that JSON plan is extracted, executed, and stripped from response."""
    
    # Mocks
    mock_deps["response_generator"].execute.return_value = MagicMock(
        text="Here is your image.\n\n```json\n{\"multimodal_plan\": {\"tasks\": [{\"step_type\": \"generate_image\"}]}}\n```",
        usage={"input_tokens": 10, "output_tokens": 10},
        success=True
    )
    
    mock_executor = AsyncMock()
    
    # Patch dependencies
    with patch("src.core.application.use_cases.conversation.process_message.cfg") as mock_cfg, \
         patch("src.core.application.use_cases.conversation.process_message.MultimodalExecutor", return_value=mock_executor) as MockExecutorCls, \
         patch("src.core.application.use_cases.conversation.process_message.JobPlanner") as MockPlannerCls, \
         patch("src.core.application.use_cases.conversation.process_message.asyncio.create_task") as mock_create_task:
        
        # Enable feature flag
        mock_cfg.env.return_value.lower.return_value = "true"
        
        # Setup specific mocked planner to return a fake plan
        mock_planner = MockPlannerCls.return_value
        fake_plan = JobPlan(
            id="plan-123",
            tenant_id="test-tenant",
            session_id="sess-123",
            tasks=[],
            status="pending"
        )
        mock_planner.create_plan.return_value = fake_plan

        # Execute
        input_data = ProcessMessageInput(
            event={"message": "Draw something"},
            session_id="sess-123",
            tenant="test-tenant"
        )
        
        result = await use_case.execute(input_data)
        
        # Assertions
        assert result.success
        assert "Here is your image." in result.response_text
        assert "```json" not in result.response_text # JSON should be stripped
        
        # Verify planner called correctly
        mock_planner.create_plan.assert_called_once()
        _, kwargs = mock_planner.create_plan.call_args
        assert kwargs["tasks"] == [{"step_type": "generate_image"}]
        
        # Verify executor called
        # We mocked asyncio.create_task, so check it was called with a coroutine
        mock_create_task.assert_called_once()
        
        # Verify execute_plan was called (we need to await the coroutine manually if we want to check side effects,
        # but here we just check that create_task was called with the right task wrapper)
        # Instead, since we are inside `_handle_multimodal_plan`, we can check if `executor.execute_plan` was called?
        # No, because `_safe_execute_plan` is the coroutine passed to create_task. 
        # But we can verify `MockExecutorCls` was instantiated.
        MockExecutorCls.assert_called_once()

@pytest.mark.asyncio
async def test_no_extraction_when_disabled(use_case, mock_deps):
    """Test that nothing happens if feature flag is disabled."""
    
    json_text = "Text.\n```json\n{\"multimodal_plan\": {}}\n```"
    mock_deps["response_generator"].execute.return_value = MagicMock(
        text=json_text,
        usage={},
        success=True
    )
    
    with patch("src.core.application.use_cases.conversation.process_message.cfg") as mock_cfg, \
         patch("src.core.application.use_cases.conversation.process_message.MultimodalExecutor") as MockExecutorCls:
        
        # Disable feature flag
        mock_cfg.env.return_value.lower.return_value = "false"
        
        input_data = ProcessMessageInput(
            event={"message": "Draw something"},
            session_id="sess-123",
            tenant="test-tenant"
        )
        
        result = await use_case.execute(input_data)
        
        # Assertions
        assert result.success
        assert result.response_text == json_text # Text unchanged
        MockExecutorCls.assert_not_called()
