"""Chat LLM factory — Vault-only keys, gateway-keyed honesty.

LAW (operator 2026-10-13):
- Provider API keys come from ``UnifiedSecretManager.get_provider_key`` only.
- Never invent a key. Never read one from the environment.
- Missing key for a vault-keyed provider is an honest ``LLMNotConfiguredError``.
- Gateway-keyed providers (mimo / custom / ollama) have no vendor API key and
  must not demand one.

No mocks: the secret manager seam is exercised through the real
``UnifiedSecretManager`` against the live Vault when available; the
gateway-keyed path is pure factory behaviour and needs no secret at all.
"""

from __future__ import annotations

import pytest

from admin.llm.exceptions import LLMNotConfiguredError
from admin.llm.providers import GATEWAY_KEYED_PROVIDER_IDS, VAULT_PROVIDER_IDS


def test_gateway_keyed_provider_ids_are_the_no_vendor_key_set():
    """Pin the contract: mimo/custom/ollama are keyed by a gateway, not a key."""
    assert set(GATEWAY_KEYED_PROVIDER_IDS) == {"mimo", "custom", "ollama"}
    assert "openai" in VAULT_PROVIDER_IDS
    assert "groq" in VAULT_PROVIDER_IDS
    for p in GATEWAY_KEYED_PROVIDER_IDS:
        assert p not in VAULT_PROVIDER_IDS


def test_get_api_key_is_not_required_for_gateway_keyed_providers():
    """get_chat_model('mimo', …) must not demand a Vault API key.

    Before: ``_merge_provider_defaults`` → ``get_api_key('mimo')`` raised
    ``LLMNotConfiguredError: Missing API key for provider 'mimo'`` even though
    mimo is gateway-keyed and has no vendor credential. That was the live
    chat-reply blocker (WS → orchestrator → LLM → reply).
    """
    from admin.llm.services.litellm_client import get_chat_model

    llm = get_chat_model(provider="mimo", name="mimo-flash")
    assert llm is not None
    # No invented key is smuggled into the call kwargs.
    assert "api_key" not in (getattr(llm, "kwargs", None) or {})


def test_get_chat_model_missing_vault_key_is_honest():
    """A vault-keyed provider with no key in Vault fails closed with a clear reason.

    Never a generic internal_error, never a silent empty key, never an env fallback.
    """
    from admin.llm.services.litellm_client import get_chat_model

    # anthropic is vault-keyed. If the live Vault already holds a key this
    # factory must succeed — skip rather than pretend the key is missing.
    from services.common.unified_secret_manager import UnifiedSecretManager

    try:
        manager = UnifiedSecretManager()
        existing = manager.get_provider_key("anthropic")
    except Exception as exc:  # Vault down → the honest failure IS the assertion
        with pytest.raises((LLMNotConfiguredError, RuntimeError)):
            get_chat_model(provider="anthropic", name="claude-3-5-haiku")
        pytest.skip(f"Vault unavailable for positive key check: {type(exc).__name__}")

    if existing and existing not in ("None", "NA"):
        llm = get_chat_model(provider="anthropic", name="claude-3-5-haiku")
        assert llm is not None
        pytest.skip("Vault holds an anthropic key — missing-key path not reachable")

    with pytest.raises(LLMNotConfiguredError) as excinfo:
        get_chat_model(provider="anthropic", name="claude-3-5-haiku")
    msg = str(excinfo.value).lower()
    assert "api key" in msg or "secret" in msg or "vault" in msg
    # The message must name the provider so an operator knows what to fix.
    assert "anthropic" in msg


def test_no_env_key_bypass_in_llm_factory():
    """The factory must never read a provider key out of the process environment."""
    from pathlib import Path

    src = Path("admin/llm/services/litellm_client.py").read_text(encoding="utf-8")
    helpers = Path("admin/llm/services/litellm_helpers.py").read_text(encoding="utf-8")
    for blob, name in ((src, "litellm_client.py"), (helpers, "litellm_helpers.py")):
        for banned in (
            "OPENAI_API_KEY",
            "GROQ_API_KEY",
            "ANTHROPIC_API_KEY",
            "os.environ.get(\"OPENAI",
            "os.environ.get(\"GROQ",
            "os.environ.get(\"ANTHROPIC",
        ):
            assert banned not in blob, f"{name} must not read {banned} from env"


def test_selected_model_carries_api_base_for_the_call():
    """SelectedModel must deliver the catalog api_base to the LLM factory.

    Before: ``select_model`` dropped ``LLMModelConfig.api_base`` and
    ``get_chat_model`` was called without it, so gateway deployments (mimo
    with an operator-set base) had nowhere to send the request.
    """
    import inspect

    from admin.core.model_router import SelectedModel

    fields = getattr(SelectedModel, "__dataclass_fields__", {})
    assert "api_base" in fields, "SelectedModel must carry api_base"
    sig = inspect.signature(SelectedModel)
    assert sig.parameters["api_base"].default == ""
