"""LLM compatibility layer for provider-specific quirks.

This module formalizes provider-specific transformations that were previously
scattered as ad-hoc fixes in the main models.py. Each compatibility function has
clear contracts, feature flags, and tests.

SRS Reference: Multi-provider LLM support

"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
    from langchain_google_genai import ChatGoogleGenerativeAI as ChatGoogle
    import dirty_json
    from admin.core.helpers import browser_use_monkeypatch
except ImportError:
    ChatGoogle = None  # type: ignore
    dirty_json = None  # type: ignore
    browser_use_monkeypatch = None  # type: ignore

import os

__all__ = [
    "fix_gemini_schema",
    "clean_gemini_json_response",
    "clean_invalid_json",
]


def fix_gemini_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Fix JSON schema for Gemini provider compatibility.

    Gemini has specific requirements for JSON schema format:
    - additionalProperties handling
    - $defs and $ref resolution

    Args:
        schema: Original JSON schema dict

    Returns:
        Gemini-compatible schema

    Raises:
        RuntimeError: If ChatGoogle not available and Gemini compatibility required
    """
    if ChatGoogle is None:
        raise RuntimeError(
            "langchain-google-genai required for Gemini compatibility. "
            "Install with: pip install langchain-google-genai"
        )

    return ChatGoogle("")._fix_gemini_schema(schema)


def clean_gemini_json_response(content: str) -> Optional[str]:
    """Clean Gemini JSON responses (strip markdown code fences).

    Gemini sometimes wraps JSON in triple backticks which breaks parsing.

    Args:
        content: Raw response content from Gemini

    Returns:
        Cleaned JSON string or None if cleaning not needed
    """
    if browser_use_monkeypatch is None:
        return None

    return browser_use_monkeypatch.gemini_clean_and_conform(content)


def clean_invalid_json(content: str) -> str:
    """Post-process invalid JSON using lenient parser.

    Some providers return malformed JSON. This uses dirty_json to
    parse and re-stringify for correctness.

    Args:
        content: Potentially malformed JSON string

    Returns:
        Valid JSON string

    Raises:
        RuntimeError: If dirty_json not available
    """
    if dirty_json is None:
        raise RuntimeError(
            "dirty-json required for lenient JSON parsing. " "Install with: pip install dirty-json"
        )

    parsed = dirty_json.parse(content)
    return dirty_json.stringify(parsed)


def should_apply_gemini_compat() -> bool:
    """Check if Gemini compatibility should be applied.

    Can be disabled via feature flag for testing or alternative implementations.
    """
    return os.environ.get("SA01_GEMINI_COMPAT_ENABLED", "true").lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


def should_apply_json_cleaning() -> bool:
    """Check if JSON cleaning should be applied.

    Can be disabled via feature flag for strict mode.
    """
    return os.environ.get("SA01_JSON_CLEANING_ENABLED", "true").lower() in {
        "true",
        "1",
        "yes",
        "on",
    }