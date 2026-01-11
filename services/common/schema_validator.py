"""
JSON schema validation utilities for inbound events.
"""

from __future__ import annotations

from typing import Any, Dict

import jsonschema

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "conversation_event": {
        "type": "object",
        "required": ["event_id", "session_id", "message"],
        "properties": {
            "event_id": {"type": "string"},
            "session_id": {"type": "string"},
            "persona_id": {"type": ["string", "null"]},
            "message": {"type": "string"},
            "attachments": {"type": "array", "items": {"type": "string"}},
            "metadata": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "assistant_event": {
        "type": "object",
        "required": ["event_id", "session_id", "role", "message"],
        "properties": {
            "event_id": {"type": "string"},
            "session_id": {"type": "string"},
            "role": {"type": "string", "enum": ["assistant"]},
            "message": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "additionalProperties": True,
    },
}


def validate(payload: Dict[str, Any], schema_name: str) -> None:
    """Validate ``payload`` against ``schema_name``.

    The original code exposed a ``validate_event`` helper that delegated to this
    function.  Several modules (e.g. ``conversation_worker`` and ``tool_executor``)
    still import ``validate_event``.  To preserve backward compatibility we keep
    the core validation logic here and provide a thin wrapper below.
    """
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return
    jsonschema.validate(payload, schema)


def validate_event(payload: Dict[str, Any], schema_name: str) -> None:
    """Legacy alias for :func:`validate`.

    Tests and existing code expect ``validate_event`` to raise the same
    ``jsonschema.ValidationError`` when validation fails.  Delegating to the
    primary ``validate`` implementation ensures a single source of truth.
    """
    return validate(payload, schema_name)
