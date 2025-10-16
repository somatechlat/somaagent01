import pytest

import models


@pytest.mark.parametrize(
    "payload,expected_response,expected_reasoning",
    [
        ("<think>reasoning goes here</think>response", "response", "reasoning goes here"),
        ("<think>partial", "", ""),
        ("no tags reply", "no tags reply", ""),
    ],
)
def test_chat_generation_result_extracts_reasoning(payload, expected_response, expected_reasoning):
    result = models.ChatGenerationResult()
    for character in payload:
        result.add_chunk(models.ChatChunk(response_delta=character, reasoning_delta=""))

    assert result.response == expected_response
    assert result.reasoning == expected_reasoning
