"""Tests for the JSON‑schema validation utilities.

The VIBE rules require real validation of external inputs.  These tests ensure
that the ``validate_payload`` helper correctly accepts valid data and raises a
clear ``ValueError`` for invalid data.
"""

import pytest

from python.tasks.schemas import A2A_CHAT_ARGS_SCHEMA, DELEGATE_PAYLOAD_SCHEMA
from python.tasks.validation import validate_payload


def test_validate_delegate_payload_success():
    payload = {
        "persona_id": "user-123",
        "target": "some-task",
        "session_id": "sess-456",
    }
    # Should not raise
    validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)


def test_validate_delegate_payload_failure():
    # Missing required type (schema allows additional properties, so we inject a bad type)
    payload = {"persona_id": 123}  # persona_id should be string or null
    with pytest.raises(ValueError) as exc:
        validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)
    assert "Payload validation error" in str(exc.value)


def test_validate_a2a_chat_args_success():
    args = {
        "agent_url": "http://example.com",
        "message": "hello",
        "attachments": ["file.txt"],
        "reset": False,
        "session_id": None,
        "metadata": None,
    }
    validate_payload(A2A_CHAT_ARGS_SCHEMA, args)


def test_validate_a2a_chat_args_failure_missing_required():
    args = {"message": "hello"}  # missing agent_url
    with pytest.raises(ValueError):
        validate_payload(A2A_CHAT_ARGS_SCHEMA, args)
