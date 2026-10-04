"""Vendor public API bases — **protocol constants**, not deployment config.

These are the well-known public endpoints of third-party services. Each one
is part of that vendor's published API protocol (the host and path prefix the
vendor documents), not of this product's deployment topology.

They live in exactly one module so that:

1. a reviewer sees every external host in one file;
2. call sites never embed a URL;
3. the *effective* base an operator actually calls can still be redirected
   through configuration (corporate proxy, regional endpoint, test harness)
   via :func:`effective_base` — the constant is the protocol default, never
   the only allowed value.

Do **not** put this product's own service topology here. Those are deployment
URLs: declared on ``SettingsModel`` / Django settings, registered in
``KEY_CATEGORY``, and resolved through
``admin.core.helpers.service_urls.require_service_url`` (SOMA-STD-CONFIG-001).

Ollama is deliberately absent: it is not a vendor cloud. Its endpoint is a
deployment URL and resolves through ``require_service_url`` /
``LLMModelConfig.api_base`` like every other service (R-VEN-02).
"""

from __future__ import annotations

from typing import Optional

# --- LLM provider protocol bases -------------------------------------------
OPENAI_API_BASE = "https://api.openai.com/v1"
ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"
GOOGLE_GENERATIVE_LANGUAGE_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GROQ_API_BASE = "https://api.groq.com/openai/v1"
# --- Messaging / social bridge protocol bases ------------------------------
TELEGRAM_API_BASE = "https://api.telegram.org"
WHATSAPP_CLOUD_API_BASE = "https://graph.facebook.com"

# --- Attribution / identity -----------------------------------------------
# OpenRouter and similar gateways accept an HTTP-Referer identifying the
# calling application. This is the product's public repository, not a
# deployment endpoint.
SOMA_GITHUB_REPOSITORY_URL = "https://github.com/somatechlat/somaAgent01"


def effective_base(protocol_constant: str, override: Optional[str]) -> str:
    """Return the base URL to actually call.

    An operator override (model ``api_base``, env, AgentSetting) wins so the
    vendor traffic can be pointed at a proxy or a regional endpoint. When no
    override is configured the vendor protocol constant is used unchanged.

    The override is never invented: ``None`` / empty means "use the protocol
    constant", not "guess a host".
    """
    if override is not None and str(override).strip():
        return str(override).strip().rstrip("/")
    return str(protocol_constant).rstrip("/")


__all__ = [
    "OPENAI_API_BASE",
    "ANTHROPIC_API_BASE",
    "GOOGLE_GENERATIVE_LANGUAGE_API_BASE",
    "GROQ_API_BASE",
    "TELEGRAM_API_BASE",
    "WHATSAPP_CLOUD_API_BASE",
    "SOMA_GITHUB_REPOSITORY_URL",
    "effective_base",
]
