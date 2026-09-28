"""Capsule Model Manager — provider/model resolution for agent identity.

Agent Zero parity: models are configured as slots (chat / vision / utility /
embedding) with provider registry + write-only API keys. Soma binds those
slots to the **Capsule** (body model FKs) so identity owns model sovereignty.

Security (VIBE / T-5):
- API keys live only in Vault via ``UnifiedSecretManager`` — never returned
  to the UI, never logged, never stored on model rows.
- Missing key or missing model → fail-closed (``ModelNotConfigured``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

# Built-in provider catalog (Agent Zero `conf/model_providers.yaml` parity).
# ``key_env`` is documentation only — runtime keys come from Vault.
PROVIDER_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "groq",
        "label": "Groq",
        "litellm_provider": "groq",
        "kind": "chat",
        "api_base": "https://api.groq.com/openai/v1",
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "litellm_provider": "openai",
        "kind": "chat",
        "api_base": "https://api.openai.com/v1",
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "litellm_provider": "anthropic",
        "kind": "chat",
        "api_base": "https://api.anthropic.com",
    },
    {
        "id": "google",
        "label": "Google Gemini",
        "litellm_provider": "gemini",
        "kind": "chat",
        "api_base": "",
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "litellm_provider": "openrouter",
        "kind": "chat",
        "api_base": "https://openrouter.ai/api/v1",
    },
    {
        "id": "ollama",
        "label": "Ollama (local)",
        "litellm_provider": "ollama",
        "kind": "chat",
        "api_base": "http://127.0.0.1:11434",
    },
    {
        "id": "azure",
        "label": "Azure OpenAI",
        "litellm_provider": "azure",
        "kind": "chat",
        "api_base": "",
    },
    {
        "id": "bedrock",
        "label": "AWS Bedrock",
        "litellm_provider": "bedrock",
        "kind": "chat",
        "api_base": "",
    },
    {"id": "xai", "label": "xAI", "litellm_provider": "xai", "kind": "chat", "api_base": ""},
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "litellm_provider": "deepseek",
        "kind": "chat",
        "api_base": "",
    },
    {
        "id": "mistral",
        "label": "Mistral",
        "litellm_provider": "mistral",
        "kind": "chat",
        "api_base": "",
    },
    {
        "id": "fireworks",
        "label": "Fireworks",
        "litellm_provider": "fireworks",
        "kind": "chat",
        "api_base": "",
    },
    {
        "id": "huggingface",
        "label": "HuggingFace",
        "litellm_provider": "huggingface",
        "kind": "embedding",
        "api_base": "",
    },
    {
        "id": "other",
        "label": "OpenAI-compatible",
        "litellm_provider": "openai",
        "kind": "chat",
        "api_base": "",
    },
]

SLOT_NAMES = ("chat", "utility", "embedding", "vision", "browser", "voice")


class ModelNotConfigured(Exception):
    """Fail-closed when a model slot or provider key is missing."""


@dataclass
class ModelSlot:
    """Resolved model slot ready for LiteLLM."""

    slot: str
    provider: str
    name: str
    api_base: str = ""
    api_key: str = ""  # runtime only — never serialize to API responses
    ctx_length: int = 0
    max_tokens: int = 0
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> Dict[str, Any]:
        """Safe representation for APIs/UI (no secret)."""
        return {
            "slot": self.slot,
            "provider": self.provider,
            "name": self.name,
            "api_base": self.api_base,
            "ctx_length": self.ctx_length,
            "max_tokens": self.max_tokens,
            "has_api_key": bool(self.api_key),
            "kwargs": {k: v for k, v in self.kwargs.items() if "key" not in k.lower()},
        }


class CapsuleModelManager:
    """Resolve model slots from Capsule body + LLMModelConfig + Vault keys."""

    def __init__(self, capsule: Optional[Any] = None) -> None:
        self._capsule = capsule

    # ------------------------------------------------------------------
    # Provider catalog
    # ------------------------------------------------------------------
    def list_providers(self) -> List[Dict[str, Any]]:
        """Provider catalog with key-configured flags (booleans only)."""
        from services.common.unified_secret_manager import UnifiedSecretManager

        sm = UnifiedSecretManager()
        out = []
        for p in PROVIDER_CATALOG:
            row = dict(p)
            try:
                row["key_configured"] = bool(sm.get_provider_key(p["id"]))
            except Exception:  # noqa: BLE001 — catalog must not fail closed
                row["key_configured"] = False
            out.append(row)
        return out

    def set_provider_key(self, provider: str, api_key: str) -> bool:
        """Store provider key in Vault (write-only). Never returns the key."""
        if not api_key or not provider:
            raise ModelNotConfigured("provider and api_key are required")
        from services.common.unified_secret_manager import UnifiedSecretManager

        sm = UnifiedSecretManager()
        ok = sm.set_provider_key(provider.lower(), api_key.strip())
        if not ok:
            raise ModelNotConfigured(f"failed to store key for provider '{provider}'")
        return True

    # ------------------------------------------------------------------
    # LLM model registry (DB rows — metadata only, no secrets)
    # ------------------------------------------------------------------
    def list_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        from admin.llm.models import LLMModelConfig

        qs = LLMModelConfig.objects.filter(is_active=True)
        if model_type:
            qs = qs.filter(model_type=model_type)
        rows = []
        for m in qs.order_by("-priority", "provider", "name"):
            rows.append(
                {
                    "id": str(m.id),
                    "name": m.name,
                    "display_name": m.display_name or m.name,
                    "provider": m.provider,
                    "model_type": m.model_type,
                    "api_base": m.api_base or "",
                    "ctx_length": m.ctx_length,
                    "capabilities": list(m.capabilities or []),
                    "priority": m.priority,
                    "cost_tier": m.cost_tier,
                    "is_active": m.is_active,
                }
            )
        return rows

    def upsert_model(
        self,
        *,
        name: str,
        provider: str,
        model_type: str = "chat",
        display_name: str = "",
        api_base: str = "",
        ctx_length: int = 0,
        capabilities: Optional[List[str]] = None,
        priority: int = 50,
        cost_tier: str = "standard",
        is_active: bool = True,
    ) -> Dict[str, Any]:
        """Create or update a model catalog row (metadata only)."""
        from admin.llm.models import LLMModelConfig

        if not name or not provider:
            raise ModelNotConfigured("name and provider are required")
        obj, _ = LLMModelConfig.objects.update_or_create(
            name=name,
            defaults={
                "provider": provider.lower(),
                "model_type": model_type if model_type in ("chat", "embedding") else "chat",
                "display_name": display_name or name,
                "api_base": api_base,
                "ctx_length": int(ctx_length or 0),
                "capabilities": capabilities or [],
                "priority": int(priority),
                "cost_tier": cost_tier,
                "is_active": is_active,
            },
        )
        return {"id": str(obj.id), "name": obj.name, "provider": obj.provider}

    # ------------------------------------------------------------------
    # Capsule slots
    # ------------------------------------------------------------------
    def resolve_slot(self, slot: str) -> ModelSlot:
        """Resolve a Capsule model slot (fail-closed)."""
        if slot not in SLOT_NAMES:
            raise ModelNotConfigured(f"unknown model slot '{slot}'")
        cap = self._capsule
        model_row = None
        if cap is not None:
            model_row = getattr(cap, f"{slot}_model", None)
            if model_row is None and slot in ("chat", "utility"):
                model_row = getattr(cap, "chat_model", None)

        if model_row is None:
            # Fall back to highest-priority active model of the right type.
            from admin.llm.models import LLMModelConfig

            wanted = "embedding" if slot == "embedding" else "chat"
            model_row = (
                LLMModelConfig.objects.filter(is_active=True, model_type=wanted)
                .order_by("-priority")
                .first()
            )
        if model_row is None:
            raise ModelNotConfigured(
                f"no model configured for slot '{slot}' (configure Models settings or Capsule body)"
            )

        provider = (model_row.provider or "").lower()
        api_key = ""
        try:
            from services.common.unified_secret_manager import UnifiedSecretManager

            api_key = UnifiedSecretManager().get_provider_key(provider) or ""
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("vault key lookup failed for %s: %s", provider, exc)

        # Ollama and some local endpoints do not need a key.
        needs_key = provider not in ("ollama", "lm_studio", "other")
        if needs_key and not api_key:
            raise ModelNotConfigured(f"Missing API key for provider '{provider}' in secret manager")

        return ModelSlot(
            slot=slot,
            provider=provider,
            name=model_row.name,
            api_base=getattr(model_row, "api_base", "") or "",
            api_key=api_key,
            ctx_length=int(getattr(model_row, "ctx_length", 0) or 0),
            kwargs=dict(getattr(model_row, "kwargs", None) or {}),
        )

    def bind_capsule_models(
        self,
        *,
        chat_model_id: Optional[str] = None,
        utility_model_id: Optional[str] = None,
        embedding_model_id: Optional[str] = None,
        vision_model_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Bind model rows onto the Capsule body (Agent Zero preset parity)."""
        from admin.llm.models import LLMModelConfig

        cap = self._capsule
        if cap is None:
            raise ModelNotConfigured("capsule is required to bind model slots")
        updates = []
        result = {}
        for attr, mid in (
            ("chat_model", chat_model_id or utility_model_id),
            ("embedding_model", embedding_model_id),
            ("image_model", vision_model_id),
        ):
            if not mid:
                continue
            if not hasattr(cap, attr):
                continue
            row = LLMModelConfig.objects.filter(id=mid).first()
            if not row:
                raise ModelNotConfigured(f"model '{mid}' not found")
            setattr(cap, attr, row)
            updates.append(attr)
            result[attr] = str(row.id)
        if updates:
            cap.save(update_fields=updates)
        return result


def get_model_manager(capsule: Optional[Any] = None) -> CapsuleModelManager:
    return CapsuleModelManager(capsule=capsule)
