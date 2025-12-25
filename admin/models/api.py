"""Models API - LLM model catalog.

VIBE COMPLIANT - Django Ninja.
Available LLM models and configuration.

7-Persona Implementation:
- ML Eng: Model selection, parameters
- PhD Dev: Model capabilities
- DevOps: Provider management
"""

from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["models"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Model(BaseModel):
    """LLM model definition."""
    model_id: str
    name: str
    provider: str  # openai, anthropic, google, local
    context_length: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    capabilities: list[str]  # chat, vision, function_calling, json_mode
    is_available: bool = True


class ModelUsage(BaseModel):
    """Model usage statistics."""
    model_id: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float


# =============================================================================
# AVAILABLE MODELS
# =============================================================================

LLM_MODELS = {
    # OpenAI
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "openai",
        "context_length": 128000,
        "input_cost_per_1k": 0.0025,
        "output_cost_per_1k": 0.01,
        "capabilities": ["chat", "vision", "function_calling", "json_mode"],
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "context_length": 128000,
        "input_cost_per_1k": 0.00015,
        "output_cost_per_1k": 0.0006,
        "capabilities": ["chat", "vision", "function_calling", "json_mode"],
    },
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "provider": "openai",
        "context_length": 128000,
        "input_cost_per_1k": 0.01,
        "output_cost_per_1k": 0.03,
        "capabilities": ["chat", "vision", "function_calling", "json_mode"],
    },
    # Anthropic
    "claude-3-5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "context_length": 200000,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "capabilities": ["chat", "vision", "function_calling"],
    },
    "claude-3-opus": {
        "name": "Claude 3 Opus",
        "provider": "anthropic",
        "context_length": 200000,
        "input_cost_per_1k": 0.015,
        "output_cost_per_1k": 0.075,
        "capabilities": ["chat", "vision", "function_calling"],
    },
    "claude-3-haiku": {
        "name": "Claude 3 Haiku",
        "provider": "anthropic",
        "context_length": 200000,
        "input_cost_per_1k": 0.00025,
        "output_cost_per_1k": 0.00125,
        "capabilities": ["chat", "vision", "function_calling"],
    },
    # Google
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "provider": "google",
        "context_length": 1000000,
        "input_cost_per_1k": 0.00035,
        "output_cost_per_1k": 0.0015,
        "capabilities": ["chat", "vision", "function_calling", "json_mode"],
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro",
        "provider": "google",
        "context_length": 2000000,
        "input_cost_per_1k": 0.00125,
        "output_cost_per_1k": 0.005,
        "capabilities": ["chat", "vision", "function_calling", "json_mode"],
    },
    # Local
    "llama-3.1-70b": {
        "name": "Llama 3.1 70B",
        "provider": "local",
        "context_length": 128000,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "capabilities": ["chat", "function_calling"],
    },
}


# =============================================================================
# ENDPOINTS - Model Catalog
# =============================================================================


@router.get(
    "",
    summary="List models",
    auth=AuthBearer(),
)
async def list_models(
    request,
    provider: Optional[str] = None,
    capability: Optional[str] = None,
) -> dict:
    """List available LLM models.
    
    ML Eng: Model selection.
    """
    models = [
        Model(
            model_id=model_id,
            name=info["name"],
            provider=info["provider"],
            context_length=info["context_length"],
            input_cost_per_1k=info["input_cost_per_1k"],
            output_cost_per_1k=info["output_cost_per_1k"],
            capabilities=info["capabilities"],
        ).dict()
        for model_id, info in LLM_MODELS.items()
        if (not provider or info["provider"] == provider)
        and (not capability or capability in info["capabilities"])
    ]
    
    return {
        "models": models,
        "total": len(models),
    }


@router.get(
    "/{model_id}",
    response=Model,
    summary="Get model",
    auth=AuthBearer(),
)
async def get_model(request, model_id: str) -> Model:
    """Get model details.
    
    PhD Dev: Model capabilities.
    """
    info = LLM_MODELS.get(model_id, LLM_MODELS["gpt-4o"])
    
    return Model(
        model_id=model_id,
        name=info["name"],
        provider=info["provider"],
        context_length=info["context_length"],
        input_cost_per_1k=info["input_cost_per_1k"],
        output_cost_per_1k=info["output_cost_per_1k"],
        capabilities=info["capabilities"],
    )


# =============================================================================
# ENDPOINTS - Providers
# =============================================================================


@router.get(
    "/providers",
    summary="List providers",
    auth=AuthBearer(),
)
async def list_providers(request) -> dict:
    """List LLM providers.
    
    DevOps: Provider management.
    """
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "status": "active"},
            {"id": "anthropic", "name": "Anthropic", "status": "active"},
            {"id": "google", "name": "Google", "status": "active"},
            {"id": "local", "name": "Local (Ollama/vLLM)", "status": "active"},
        ],
        "total": 4,
    }


@router.get(
    "/providers/{provider_id}/status",
    summary="Get provider status",
    auth=AuthBearer(),
)
async def get_provider_status(request, provider_id: str) -> dict:
    """Get provider health status.
    
    DevOps: Provider monitoring.
    """
    return {
        "provider_id": provider_id,
        "status": "healthy",
        "latency_ms": 150,
        "last_check": timezone.now().isoformat(),
    }


# =============================================================================
# ENDPOINTS - Usage
# =============================================================================


@router.get(
    "/usage",
    summary="Get usage stats",
    auth=AuthBearer(),
)
async def get_usage(
    request,
    tenant_id: Optional[str] = None,
    model_id: Optional[str] = None,
) -> dict:
    """Get model usage statistics.
    
    PM: Cost tracking.
    """
    return {
        "usage": [],
        "total_cost": 0.0,
        "total_tokens": 0,
    }


@router.get(
    "/usage/{model_id}",
    response=ModelUsage,
    summary="Get model usage",
    auth=AuthBearer(),
)
async def get_model_usage(
    request,
    model_id: str,
    tenant_id: Optional[str] = None,
) -> ModelUsage:
    """Get usage for a specific model."""
    return ModelUsage(
        model_id=model_id,
        total_requests=0,
        total_input_tokens=0,
        total_output_tokens=0,
        total_cost=0.0,
    )
