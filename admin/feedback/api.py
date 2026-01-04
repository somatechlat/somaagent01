"""Feedback API - User feedback and ratings.


Conversation ratings and improvement signals.

7-Persona Implementation:
- PM: User satisfaction
- QA: Quality monitoring
- ML Eng: RLHF data
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["feedback"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Feedback(BaseModel):
    """User feedback."""

    feedback_id: str
    conversation_id: str
    message_id: Optional[str] = None
    user_id: str
    rating: int  # 1-5
    category: str  # helpful, accurate, fast, creative
    comment: Optional[str] = None
    created_at: str


class FeedbackStats(BaseModel):
    """Feedback statistics."""

    total_feedback: int
    avg_rating: float
    rating_distribution: dict
    category_breakdown: dict


# =============================================================================
# ENDPOINTS - Feedback CRUD
# =============================================================================


@router.get(
    "",
    summary="List feedback",
    auth=AuthBearer(),
)
async def list_feedback(
    request,
    conversation_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    rating: Optional[int] = None,
    limit: int = 50,
) -> dict:
    """List feedback.

    PM: Feedback review.
    """
    return {
        "feedback": [],
        "total": 0,
    }


@router.post(
    "",
    response=Feedback,
    summary="Submit feedback",
    auth=AuthBearer(),
)
async def submit_feedback(
    request,
    conversation_id: str,
    user_id: str,
    rating: int,
    category: str = "helpful",
    message_id: Optional[str] = None,
    comment: Optional[str] = None,
) -> Feedback:
    """Submit user feedback.

    PM: User satisfaction tracking.
    """
    feedback_id = str(uuid4())

    logger.info(f"Feedback: {feedback_id}, rating={rating}")

    return Feedback(
        feedback_id=feedback_id,
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        category=category,
        comment=comment,
        created_at=timezone.now().isoformat(),
    )


@router.get(
    "/{feedback_id}",
    response=Feedback,
    summary="Get feedback",
    auth=AuthBearer(),
)
async def get_feedback(request, feedback_id: str) -> Feedback:
    """Get feedback details."""
    return Feedback(
        feedback_id=feedback_id,
        conversation_id="conv-1",
        user_id="user-1",
        rating=5,
        category="helpful",
        created_at=timezone.now().isoformat(),
    )


@router.delete(
    "/{feedback_id}",
    summary="Delete feedback",
    auth=AuthBearer(),
)
async def delete_feedback(request, feedback_id: str) -> dict:
    """Delete feedback."""
    return {
        "feedback_id": feedback_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Thumbs
# =============================================================================


@router.post(
    "/thumbs-up",
    summary="Thumbs up",
    auth=AuthBearer(),
)
async def thumbs_up(
    request,
    conversation_id: str,
    message_id: str,
    user_id: str,
) -> dict:
    """Quick thumbs up feedback.

    PM: Quick positive signal.
    """
    feedback_id = str(uuid4())

    return {
        "feedback_id": feedback_id,
        "type": "thumbs_up",
        "recorded": True,
    }


@router.post(
    "/thumbs-down",
    summary="Thumbs down",
    auth=AuthBearer(),
)
async def thumbs_down(
    request,
    conversation_id: str,
    message_id: str,
    user_id: str,
    reason: Optional[str] = None,
) -> dict:
    """Quick thumbs down feedback.

    QA: Negative signal for review.
    """
    feedback_id = str(uuid4())

    logger.warning(f"Thumbs down: {message_id}")

    return {
        "feedback_id": feedback_id,
        "type": "thumbs_down",
        "recorded": True,
    }


# =============================================================================
# ENDPOINTS - RLHF
# =============================================================================


@router.post(
    "/compare",
    summary="Compare responses",
    auth=AuthBearer(),
)
async def compare_responses(
    request,
    conversation_id: str,
    response_a_id: str,
    response_b_id: str,
    preferred: str,  # a, b
    user_id: str,
) -> dict:
    """A/B comparison for RLHF.

    ML Eng: RLHF training data.
    """
    comparison_id = str(uuid4())

    return {
        "comparison_id": comparison_id,
        "preferred": preferred,
        "recorded": True,
    }


@router.get(
    "/rlhf/export",
    summary="Export RLHF data",
    auth=AuthBearer(),
)
async def export_rlhf_data(
    request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Export feedback for RLHF training.

    ML Eng: Training data export.
    """
    export_id = str(uuid4())

    return {
        "export_id": export_id,
        "status": "generating",
        "format": "jsonl",
    }


# =============================================================================
# ENDPOINTS - Stats
# =============================================================================


@router.get(
    "/stats",
    response=FeedbackStats,
    summary="Get stats",
    auth=AuthBearer(),
)
async def get_stats(
    request,
    agent_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> FeedbackStats:
    """Get feedback statistics.

    PM: Quality metrics.
    """
    return FeedbackStats(
        total_feedback=0,
        avg_rating=0.0,
        rating_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        category_breakdown={},
    )


@router.get(
    "/categories",
    summary="List categories",
    auth=AuthBearer(),
)
async def list_categories(request) -> dict:
    """List feedback categories.

    PM: Categorization.
    """
    return {
        "categories": [
            {"id": "helpful", "name": "Helpful"},
            {"id": "accurate", "name": "Accurate"},
            {"id": "fast", "name": "Fast"},
            {"id": "creative", "name": "Creative"},
            {"id": "clear", "name": "Clear"},
        ],
        "total": 5,
    }
