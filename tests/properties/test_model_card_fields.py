"""Property: Model card field completeness.

Validates: Requirements 7.11, 7.12, 7.13, 7.14 (provider selector, model name,
context length, rate limits, advanced kwargs, defaults).
"""

import json
import pathlib
import re


def test_model_card_exposes_core_fields_and_defaults():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/settings/model-card.js").read_text(encoding="utf-8")

    # Core config fields
    for field in [
        "provider",
        "modelName",
        "contextLength",
        "rateLimit",
        "temperature",
        "maxTokens",
        "kwargs",
    ]:
        assert field in text, f"Missing model card field: {field}"

    # Defaults in resetDefaults
    assert "resetDefaults()" in text
    defaults = {
        "provider": "openai",
        "contextLength": 4096,
        "rateLimit": 60,
        "temperature": 0.7,
        "maxTokens": 2048,
        "kwargs": {},
    }
    for key, val in defaults.items():
        assert str(val) in text, f"Default {key} not found in resetDefaults"


def test_model_card_providers_list_covers_required_options():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/settings/model-card.js").read_text(encoding="utf-8")

    # Providers array should contain a representative set (openai, anthropic, google, groq)
    for provider in ["openai", "anthropic", "google", "groq"]:
        assert re.search(rf"value:\s*'{provider}'", text), f"Provider {provider} missing"

    # Provider list should have at least 8 entries (broad coverage)
    providers_raw = re.search(r"const PROVIDERS = \[(.*?)\];", text, re.S)
    assert providers_raw, "Providers list not found"
    entries = [e for e in providers_raw.group(1).split("\n") if "value" in e]
    assert len(entries) >= 8, "Providers list should include at least 8 options"
