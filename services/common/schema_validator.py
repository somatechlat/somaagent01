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
    """Validate a payload against a named schema; raises jsonschema.ValidationError on failure."""
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return
    jsonschema.validate(payload, schema)
