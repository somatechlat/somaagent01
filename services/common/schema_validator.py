"""Lightweight JSON schema validation helpers for SomaAgent 01 services.

This module centralises access to JSON schemas stored in the repository's
`schemas/` directory so individual services can validate their payloads
without duplicating file-loading logic. Schemas are loaded lazily and cached
after the first use to avoid repeated disk I/O during long-running services.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, Dict

import jsonschema
from jsonschema import Draft7Validator

_SCHEMA_FILES: Dict[str, str] = {
    "tool_result": "tool_result.json",
    "tool_event": "tool_event.json",
    "conversation_event": "conversation_event.json",
    "tool_request": "tool_request.json",
}


def _schema_path(schema_name: str) -> Path:
    try:
        filename = _SCHEMA_FILES[schema_name]
    except KeyError as exc:
        raise ValueError(f"Unknown schema '{schema_name}'") from exc

    base_dir = Path(__file__).resolve().parents[2] / "schemas"
    return base_dir / filename


@functools.lru_cache(maxsize=None)
def _get_validator(schema_name: str) -> Draft7Validator:
    schema_file = _schema_path(schema_name)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with schema_file.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    if "$id" not in schema:
        resolver = jsonschema.RefResolver(base_uri=schema_file.as_uri(), referrer=schema)
        return Draft7Validator(schema, resolver=resolver)
    return Draft7Validator(schema)


def validate_event(payload: Dict[str, Any], schema_name: str) -> None:
    """Validate *payload* against the named JSON schema.

    Raises the underlying ``jsonschema.ValidationError`` if validation fails.
    """

    validator = _get_validator(schema_name)
    validator.validate(payload)
