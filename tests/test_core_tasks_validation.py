"""Tests for JSON‑schema validation in core_tasks.

These ensure that the new validation logic raises errors for malformed inputs
and passes for correct payloads, satisfying VIBE security requirements.
"""

import pytest

from python.tasks import core_tasks
from python.tasks.schemas import (
    DELEGATE_PAYLOAD_SCHEMA,
    STORE_INTERACTION_PAYLOAD_SCHEMA,
    FEEDBACK_LOOP_PAYLOAD_SCHEMA,
    CLEANUP_SESSIONS_ARGS_SCHEMA,
    REBUILD_INDEX_ARGS_SCHEMA,
    EVALUATE_POLICY_ARGS_SCHEMA,
)
from python.tasks.validation import validate_payload


def test_delegate_payload_validation_success():
    payload = {"persona_id": "user1", "target": "taskX"}
    # Should not raise
    validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)


def test_delegate_payload_validation_failure():
    payload = {"persona_id": 123}  # invalid type
    with pytest.raises(ValueError):
        validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)


def test_cleanup_sessions_validation_success():
    validate_payload(CLEANUP_SESSIONS_ARGS_SCHEMA, {"max_age_hours": 24})


def test_cleanup_sessions_validation_failure():
    with pytest.raises(ValueError):
        validate_payload(CLEANUP_SESSIONS_ARGS_SCHEMA, {"max_age_hours": -1})


def test_rebuild_index_schema_success():
    validate_payload(REBUILD_INDEX_ARGS_SCHEMA, {"tenant_id": "tenantA"})


def test_rebuild_index_schema_failure():
    with pytest.raises(ValueError):
        validate_payload(REBUILD_INDEX_ARGS_SCHEMA, {"tenant": "tenantA"})


def test_evaluate_policy_schema_success():
    validate_payload(
        EVALUATE_POLICY_ARGS_SCHEMA,
        {"tenant_id": "t1", "action": "read", "resource": {"name": "res"}},
    )


def test_evaluate_policy_schema_failure():
    with pytest.raises(ValueError):
        validate_payload(
            EVALUATE_POLICY_ARGS_SCHEMA,
            {"tenant_id": "t1", "action": "read"},  # missing resource
        )
