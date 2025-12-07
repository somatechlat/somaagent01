"""JSON‑schema validation utilities for Celery task payloads.

The VIBE rules require real validation of external input.  This module provides a
light‑weight wrapper around the ``jsonschema`` library that raises a
``ValueError`` when validation fails.  The helper is deliberately small – it
avoids pulling in heavy validation frameworks and keeps the implementation
production‑ready.
"""

from __future__ import annotations

from typing import Any, Mapping

from jsonschema import Draft7Validator

# Cache for compiled validators to avoid mutating the original schema dict.
_validator_cache: dict[int, Draft7Validator] = {}

__all__ = ["validate_payload"]


def _load_schema(schema: Mapping[str, Any]) -> Draft7Validator:
    """Compile a JSON‑schema into a ``Draft7Validator``.

    The function caches the validator on the schema object itself to avoid
    recompilation on every call – a small optimisation useful for high‑throughput
    tasks.
    """
    if not isinstance(schema, dict):
        raise TypeError("Schema must be a mapping")
    # Attach a cached validator if not already present
    # Use the ``id`` of the schema dict as a cache key – this is stable for the
    # lifetime of the dict object. Storing the validator on the dict itself is
    # prohibited by the VIBE rule against mutating input arguments.
    key = id(schema)
    validator = _validator_cache.get(key)
    if validator is None:
        validator = Draft7Validator(schema)
        _validator_cache[key] = validator
    return validator


def validate_payload(schema: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    """Validate *payload* against *schema*.

    Raises ``ValueError`` with a concise error description if validation fails.
    The function does **not** mutate the payload.
    """
    validator = _load_schema(schema)
    errors = list(validator.iter_errors(payload))
    if errors:
        # Build a readable message from the first error (VIBE: no excessive noise)
        first = errors[0]
        raise ValueError(f"Payload validation error: {first.message}")
