"""Request validation for tool executor service.

This module handles validation of incoming tool execution requests
and outgoing tool result events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from jsonschema import ValidationError

from services.common.schema_validator import validate_event

LOGGER = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    error_message: str | None = None
    tool_name: str | None = None
    session_id: str | None = None
    tenant: str = "default"
    persona_id: str | None = None


def validate_tool_request(event: dict[str, Any]) -> ValidationResult:
    """Validate an incoming tool execution request.

    Args:
        event: The raw event from Kafka containing tool request data.

    Returns:
        ValidationResult with valid=True if request is valid,
        or valid=False with error_message if invalid.
    """
    session_id = event.get("session_id")
    tool_name = event.get("tool_name")
    tenant = event.get("metadata", {}).get("tenant", "default")
    persona_id = event.get("persona_id")

    if not session_id:
        return ValidationResult(
            valid=False,
            error_message="Missing required field: session_id",
            tool_name=tool_name,
            session_id=None,
            tenant=tenant,
            persona_id=persona_id,
        )

    if not tool_name:
        return ValidationResult(
            valid=False,
            error_message="Missing required field: tool_name",
            tool_name=None,
            session_id=session_id,
            tenant=tenant,
            persona_id=persona_id,
        )

    return ValidationResult(
        valid=True,
        tool_name=tool_name,
        session_id=session_id,
        tenant=tenant,
        persona_id=persona_id,
    )


def validate_tool_result(result_event: dict[str, Any]) -> bool:
    """Validate a tool result event against the schema.

    Args:
        result_event: The tool result event to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate_event(result_event, "tool_result")
        return True
    except ValidationError as exc:
        LOGGER.error(
            "Invalid tool result payload",
            extra={"tool": result_event.get("tool_name"), "error": exc.message},
        )
        return False