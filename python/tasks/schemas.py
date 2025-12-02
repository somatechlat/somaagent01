"""JSON‑schema definitions for Celery task payloads.

The schemas are deliberately minimal – they capture the required fields that
core tasks expect.  Keeping them in a separate module makes them reusable across
tasks and allows the ``validation.validate_payload`` helper to be applied
consistently, satisfying VIBE security and correctness rules.
"""

from __future__ import annotations

# Schema for the ``delegate`` task payload.  The task records a delegation
# request and expects a ``persona_id`` (optional) and a ``target`` or ``task``
# identifier.
DELEGATE_PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "persona_id": {"type": ["string", "null"]},
        "target": {"type": ["string", "null"]},
        "task": {"type": ["string", "null"]},
        "session_id": {"type": ["string", "null"]},
    },
    "required": [],
    "additionalProperties": True,
}

# Schema for the ``a2a_chat`` task arguments (excluding ``self`` which is
# injected by Celery).  Only a subset is validated – the rest are passed through
# to the underlying FastA2A client.
A2A_CHAT_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "agent_url": {"type": "string", "format": "uri"},
        "message": {"type": "string"},
        "attachments": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reset": {"type": "boolean"},
        "session_id": {"type": ["string", "null"]},
        "metadata": {"type": ["object", "null"]},
    },
    "required": ["agent_url", "message"],
    "additionalProperties": False,
}

# Schema for ``store_interaction`` task payload
STORE_INTERACTION_PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "interaction": {"type": "object"},
    },
    "required": ["session_id", "interaction"],
    "additionalProperties": False,
}

# Schema for ``feedback_loop`` task payload
FEEDBACK_LOOP_PAYLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "session_id": {"type": "string"},
        "feedback": {"type": "object"},
    },
    "required": ["session_id", "feedback"],
    "additionalProperties": False,
}

# Schema for ``cleanup_sessions`` task arguments (optional max_age_hours)
CLEANUP_SESSIONS_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "max_age_hours": {"type": "integer", "minimum": 1},
    },
    "required": [],
    "additionalProperties": False,
}

# Schema for ``evaluate_policy`` task arguments
EVALUATE_POLICY_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "tenant_id": {"type": "string"},
        "action": {"type": "string"},
        "resource": {"type": "object"},
    },
    "required": ["tenant_id", "action", "resource"],
    "additionalProperties": False,
}

# Schema for ``rebuild_index`` task arguments (tenant_id required)
REBUILD_INDEX_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "tenant_id": {"type": "string"},
    },
    "required": ["tenant_id"],
    "additionalProperties": False,
}

__all__ = [
    "DELEGATE_PAYLOAD_SCHEMA",
    "A2A_CHAT_ARGS_SCHEMA",
    "STORE_INTERACTION_PAYLOAD_SCHEMA",
    "FEEDBACK_LOOP_PAYLOAD_SCHEMA",
    "CLEANUP_SESSIONS_ARGS_SCHEMA",
    "REBUILD_INDEX_ARGS_SCHEMA",
    "EVALUATE_POLICY_ARGS_SCHEMA",
]
