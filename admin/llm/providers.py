"""LLM provider ids, vendor protocol bases, and model-role bindings.

Role names are the product concept (Chat / Utility / Embedding / Vision /
Decision). ``ROLE_SETTING_KEYS`` maps each non-FK role to the ``AgentSetting``
key that stores the bound ``LLMModelConfig`` id. ``decision_role`` is Clef
(System One) and is stored under ``decision_role_id``.
"""

from __future__ import annotations

from typing import Final, Tuple

from admin.core.helpers.vendor_api_bases import (
    ANTHROPIC_API_BASE,
    DEEPSEEK_API_BASE,
    GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
    GROQ_API_BASE,
    HUGGINGFACE_API_BASE,
    OPENAI_API_BASE,
    effective_base,
)

KNOWN_PROVIDER_IDS: Final[Tuple[str, ...]] = (
    "openai",
    "anthropic",
    "google",
    "groq",
    "deepseek",
    "huggingface",
    "ollama",
    "cloudflare",
    "mimo",
    "custom",
)

# Providers whose credential is a single API key in Vault.
VAULT_PROVIDER_IDS: Final[Tuple[str, ...]] = (
    "openai",
    "anthropic",
    "google",
    "groq",
    "deepseek",
    "huggingface",
    "cloudflare",
    "mimo",
)

# Providers keyed through an external gateway (no vendor API key of their
# own — the operator supplies a deployment endpoint and the gateway handles
# any upstream auth).
GATEWAY_KEYED_PROVIDER_IDS: Final[Tuple[str, ...]] = ("custom", "ollama")

# Providers that speak the OpenAI wire protocol via a deployment endpoint.
# LiteLLM has no native ``mimo`` / ``custom`` / ``ollama`` chat provider, so
# calls are addressed as ``openai/<model>`` with ``api_base`` naming the
# real gateway.  Ollama's OpenAI-compatible surface works the same way.
OPENAI_COMPAT_PROVIDER_IDS: Final[Tuple[str, ...]] = ("mimo", "custom", "ollama")

# Vendor protocol bases. Deployment endpoints (Ollama, Mimo, Cloudflare
# account-scoped Workers AI) have an empty protocol default — the operator
# names them (LLMModelConfig.api_base / InfrastructureConfig).
PROVIDER_API_BASES: Final[dict[str, str]] = {
    "openai": OPENAI_API_BASE,
    "anthropic": ANTHROPIC_API_BASE,
    "google": GOOGLE_GENERATIVE_LANGUAGE_API_BASE,
    "groq": GROQ_API_BASE,
    "deepseek": DEEPSEEK_API_BASE,
    "huggingface": HUGGINGFACE_API_BASE,
    "ollama": "",
    "cloudflare": "",
    "mimo": "",
    "custom": "",
}

# The five model roles. ``decision_role`` is Clef (System One).
MODEL_ROLES: Final[Tuple[str, ...]] = (
    "chat_role",
    "utility_role",
    "embedding_role",
    "vision_role",
    "decision_role",
)

# Role -> AgentSetting key for roles stored as settings (not Capsule FKs).
# chat_role -> Capsule.chat_model FK; vision_role -> Capsule.image_model FK.
ROLE_SETTING_KEYS: Final[dict[str, str]] = {
    "chat_role": "chat_model_id",
    "utility_role": "utility_model_id",
    "embedding_role": "embedding_model_id",
    "vision_role": "vision_model_id",
    "decision_role": "decision_role_id",
}

# AgentSetting scope key for the tenant-level model-role defaults. One name,
# one authority — the bootstrap, the roles API and the settings chain all
# address the same rows.
DEFAULTS_AGENT_ID: Final[str] = "default"


def provider_api_base(provider_id: str, override: str | None = None) -> str:
    """Return the base URL to call for ``provider_id``.

    Operator override (``LLMModelConfig.api_base``) wins; otherwise the vendor
    protocol constant. Deployment endpoints have no default — empty is returned
    and the caller must fail closed rather than invent a host.
    """
    protocol = PROVIDER_API_BASES.get(provider_id.lower(), "")
    return effective_base(protocol, override)


def is_known_provider(provider_id: str) -> bool:
    return provider_id.strip().lower() in KNOWN_PROVIDER_IDS


def provider_requires_api_key(provider_id: str) -> bool:
    """True when this provider's credential is a vendor/gateway API key in Vault.

    Vault-keyed providers (including mimo) fail closed without a key from
    ``UnifiedSecretManager.get_provider_key``.  Pure gateway-keyed providers
    (custom / ollama) have no vendor key — the operator supplies only a
    deployment endpoint.

    OpenAI-compatible deployment endpoints (mimo / custom / ollama) MUST also
    carry ``api_base``; without it LiteLLM would address api.openai.com.
    """
    return provider_id.strip().lower() not in GATEWAY_KEYED_PROVIDER_IDS


def litellm_provider_for(provider_id: str) -> str:
    """Return the LiteLLM protocol prefix for ``provider_id``.

    Deployment endpoints that speak the OpenAI wire protocol (mimo, custom,
    ollama) have no native LiteLLM chat provider.  Addressing them as
    ``openai/<model>`` with ``api_base`` is the supported LiteLLM pattern for
    OpenAI-compatible gateways.
    """
    pid = provider_id.strip().lower()
    if pid in OPENAI_COMPAT_PROVIDER_IDS:
        return "openai"
    return pid


__all__ = [
    "KNOWN_PROVIDER_IDS",
    "GATEWAY_KEYED_PROVIDER_IDS",
    "VAULT_PROVIDER_IDS",
    "OPENAI_COMPAT_PROVIDER_IDS",
    "PROVIDER_API_BASES",
    "MODEL_ROLES",
    "ROLE_SETTING_KEYS",
    "DEFAULTS_AGENT_ID",
    "provider_api_base",
    "is_known_provider",
    "provider_requires_api_key",
    "litellm_provider_for",
    "ANTHROPIC_API_BASE",
    "DEEPSEEK_API_BASE",
    "GOOGLE_GENERATIVE_LANGUAGE_API_BASE",
    "GROQ_API_BASE",
    "HUGGINGFACE_API_BASE",
    "OPENAI_API_BASE",
]
