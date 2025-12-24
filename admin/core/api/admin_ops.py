"""Admin Operations API Router.

Migrated from: dlq.py, requeue.py, profiles.py
Pure Django Ninja for admin operations.

VIBE COMPLIANT - Django patterns.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import NotFoundError

router = Router(tags=["admin-ops"])
logger = logging.getLogger(__name__)


# === DLQ Operations ===


class DLQItemResponse(BaseModel):
    """DLQ item schema."""

    id: str
    topic: str
    payload: dict
    error: Optional[str] = None


def _get_dlq_store():
    from services.common.dlq_store import DLQStore
    from django.conf import settings

    return DLQStore(dsn=settings.DATABASE_DSN)


@router.get("/dlq/{topic}", response=list[DLQItemResponse], summary="List DLQ items")
async def list_dlq(topic: str):
    """List dead letter queue items for a topic."""
    store = _get_dlq_store()
    return await store.list(topic)


@router.delete("/dlq/{topic}", summary="Clear DLQ topic")
async def clear_dlq(topic: str) -> dict:
    """Clear all items from a DLQ topic."""
    store = _get_dlq_store()
    await store.clear(topic)
    return {"cleared": topic}


@router.post("/dlq/{topic}/{item_id}/reprocess", summary="Reprocess DLQ item")
async def reprocess_dlq(topic: str, item_id: str) -> dict:
    """Reprocess a specific DLQ item."""
    store = _get_dlq_store()
    ok = await store.reprocess(topic, item_id)
    if not ok:
        raise NotFoundError("dlq_item", item_id)
    return {"reprocessed": item_id, "topic": topic}


# === Requeue Operations ===


class RequeueItemResponse(BaseModel):
    """Requeue item schema."""

    requeue_id: str
    payload: dict
    status: str


def _get_requeue_store():
    from services.common.requeue_store import RequeueStore
    from django.conf import settings

    return RequeueStore(
        url=settings.REDIS_URL,
        prefix="policy:requeue",
    )


@router.get("/requeue", summary="List requeue items")
async def list_requeue():
    """List pending requeue items."""
    store = _get_requeue_store()
    return await store.list()


@router.post("/requeue/{requeue_id}/resolve", summary="Resolve requeue item")
async def resolve_requeue(requeue_id: str) -> dict:
    """Resolve a requeue item."""
    store = _get_requeue_store()
    ok = await store.resolve(requeue_id)
    if not ok:
        raise NotFoundError("requeue", requeue_id)
    return {"resolved": requeue_id}


@router.delete("/requeue/{requeue_id}", summary="Delete requeue item")
async def delete_requeue(requeue_id: str) -> dict:
    """Delete a requeue item."""
    store = _get_requeue_store()
    ok = await store.delete(requeue_id)
    if not ok:
        raise NotFoundError("requeue", requeue_id)
    return {"deleted": requeue_id}


# === Model Profiles ===


class ModelProfileCreate(BaseModel):
    """Model profile create request."""

    role: str
    deployment_mode: str
    config: dict


def _get_profile_store():
    from services.common.model_profiles import ModelProfileStore

    return ModelProfileStore()


@router.get("/model-profiles", summary="List model profiles")
async def list_model_profiles():
    """List all model profiles."""
    store = _get_profile_store()
    return await store.list()


@router.post("/model-profiles", summary="Create model profile")
async def create_model_profile(body: ModelProfileCreate) -> dict:
    """Create a new model profile."""
    from services.common.model_profiles import ModelProfile

    store = _get_profile_store()
    profile = ModelProfile(role=body.role, deployment_mode=body.deployment_mode, config=body.config)
    await store.upsert(profile)
    return {"status": "created"}


@router.put("/model-profiles/{role}/{deployment_mode}", summary="Update model profile")
async def update_model_profile(role: str, deployment_mode: str, body: ModelProfileCreate) -> dict:
    """Update an existing model profile."""
    from services.common.model_profiles import ModelProfile

    store = _get_profile_store()
    profile = ModelProfile(role=role, deployment_mode=deployment_mode, config=body.config)
    await store.upsert(profile)
    return {"status": "updated"}


@router.delete("/model-profiles/{role}/{deployment_mode}", summary="Delete model profile")
async def delete_model_profile(role: str, deployment_mode: str) -> dict:
    """Delete a model profile."""
    store = _get_profile_store()
    deleted = await store.delete(role, deployment_mode)
    if not deleted:
        raise NotFoundError("profile", f"{role}/{deployment_mode}")
    return {"deleted": f"{role}/{deployment_mode}"}


@router.get("/agents/profiles", summary="List agent profiles")
async def list_agent_profiles():
    """List all agent profiles (alias for model-profiles)."""
    store = _get_profile_store()
    return await store.list()
