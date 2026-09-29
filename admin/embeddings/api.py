"""Embeddings API - Vector embedding generation.


Embedding endpoint for RAG and semantic search.

- ML Eng: Embedding models, batch processing
- PhD Dev: Vector representation
- DevOps: Model serving
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.memory_contract import embed_text

router = Router(tags=["embeddings"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class EmbeddingRequest(BaseModel):
    """Embedding request."""

    input: list[str]
    model: str = "text-embedding-ada-002"


class EmbeddingResult(BaseModel):
    """Embedding result."""

    object: str = "list"
    model: str
    data: list[dict]
    usage: dict


class ModelInfo(BaseModel):
    """Embedding model info."""

    model_id: str
    name: str
    dimensions: int
    max_tokens: int
    provider: str


# =============================================================================
# AVAILABLE MODELS
# =============================================================================

from services.common.memory_contract import get_mem_embed_dim

EMBEDDING_MODELS = {
    "text-embedding-ada-002": {
        "name": "text-embedding-ada-002",
        "dimensions": get_mem_embed_dim(),
        "max_tokens": 8192,
        "provider": "openai",
    },
    "text-embedding-3-small": {
        "name": "text-embedding-3-small",
        "dimensions": get_mem_embed_dim(),
        "max_tokens": 8192,
        "provider": "openai",
    },
    "text-embedding-3-large": {
        "name": "text-embedding-3-large",
        "dimensions": get_mem_embed_dim(),
        "max_tokens": 8192,
        "provider": "openai",
    },
    "voyage-large-2": {
        "name": "voyage-large-2",
        "dimensions": get_mem_embed_dim(),
        "max_tokens": 16000,
        "provider": "voyage",
    },
    "local-sentence-transformer": {
        "name": "all-MiniLM-L6-v2",
        "dimensions": get_mem_embed_dim(),
        "max_tokens": 512,
        "provider": "local",
    },
}


# =============================================================================
# ENDPOINTS - Embedding Generation
# =============================================================================


@router.post(
    "",
    response=EmbeddingResult,
    summary="Create embeddings",
    auth=AuthBearer(),
)
async def create_embeddings(
    request,
    input: list[str],
    model: str = "text-embedding-ada-002",
) -> EmbeddingResult:
    """Create embeddings for input texts.

    ML Eng: Batch embedding generation.
    """
    dim = EMBEDDING_MODELS.get(model, EMBEDDING_MODELS["text-embedding-ada-002"])["dimensions"]

    data = [
        {
            "object": "embedding",
            "index": i,
            "embedding": embed_text(text, dim=dim),
        }
        for i, text in enumerate(input)
    ]

    return EmbeddingResult(
        model=model,
        data=data,
        usage={
            "prompt_tokens": sum(len(t.split()) for t in input),
            "total_tokens": sum(len(t.split()) for t in input),
        },
    )


@router.post(
    "/batch",
    summary="Create batch embeddings",
    auth=AuthBearer(),
)
async def create_batch_embeddings(
    request,
    inputs: list[str],
    model: str = "text-embedding-ada-002",
    batch_size: int = 100,
) -> dict:
    """Create embeddings in batches.

    ML Eng: Large-scale embedding.
    DevOps: Batch processing.
    """
    raise HttpError(501, "Batch embedding is not implemented: no async embedding job runner.")


@router.get(
    "/batch/{batch_id}",
    summary="Get batch status",
    auth=AuthBearer(),
)
async def get_batch_status(
    request,
    batch_id: str,
) -> dict:
    """Get batch embedding status."""
    raise HttpError(
        501, "Batch embedding status is not implemented: no async embedding job runner."
    )


# =============================================================================
# ENDPOINTS - Model Info
# =============================================================================


@router.get(
    "/models",
    summary="List models",
    auth=AuthBearer(),
)
async def list_models(request) -> dict:
    """List available embedding models.

    ML Eng: Model selection.
    """
    models = [
        ModelInfo(
            model_id=model_id,
            name=info["name"],
            dimensions=info["dimensions"],
            max_tokens=info["max_tokens"],
            provider=info["provider"],
        ).dict()
        for model_id, info in EMBEDDING_MODELS.items()
    ]

    return {
        "models": models,
        "total": len(models),
    }


@router.get(
    "/models/{model_id}",
    response=ModelInfo,
    summary="Get model",
    auth=AuthBearer(),
)
async def get_model(request, model_id: str) -> ModelInfo:
    """Get model details."""
    info = EMBEDDING_MODELS.get(model_id, EMBEDDING_MODELS["text-embedding-ada-002"])

    return ModelInfo(
        model_id=model_id,
        name=info["name"],
        dimensions=info["dimensions"],
        max_tokens=info["max_tokens"],
        provider=info["provider"],
    )


# =============================================================================
# ENDPOINTS - Similarity
# =============================================================================


@router.post(
    "/similarity",
    summary="Compute similarity",
    auth=AuthBearer(),
)
async def compute_similarity(
    request,
    embedding1: list[float],
    embedding2: list[float],
) -> dict:
    """Compute cosine similarity.

    ML Eng: Similarity scoring.
    """
    # Compute cosine similarity
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5

    similarity = dot_product / (norm1 * norm2) if norm1 and norm2 else 0.0

    return {
        "similarity": similarity,
    }


# =============================================================================
# ENDPOINTS - Stats
# =============================================================================


@router.get(
    "/stats",
    summary="Get usage stats",
    auth=AuthBearer(),
)
async def get_stats(
    request,
    tenant_id: Optional[str] = None,
) -> dict:
    """Get embedding usage statistics.

    PM: Usage tracking.
    """
    return {
        "total_embeddings_created": 0,
        "total_tokens_used": 0,
        "models_used": {},
    }
