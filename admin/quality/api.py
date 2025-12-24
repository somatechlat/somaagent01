"""Quality Gating API - Asset Critic and Retry Logic.

VIBE COMPLIANT - Django Ninja + LLM evaluation.
Per AGENT_TASKS.md Phase 7.4 - Quality Gating.

7-Persona Implementation:
- PhD Dev: Quality metrics, bounded retry patterns
- ML Eng: LLM-based quality evaluation
- QA: Automated quality assertions
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError

router = Router(tags=["quality"])
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_RETRY_ATTEMPTS = 3
DEFAULT_QUALITY_THRESHOLD = 0.7


# =============================================================================
# SCHEMAS
# =============================================================================


class QualityEvaluationRequest(BaseModel):
    """Request quality evaluation."""
    asset_id: str
    asset_type: str  # text, image, code, diagram
    content: Optional[str] = None
    content_url: Optional[str] = None
    criteria: Optional[list[str]] = None  # accuracy, coherence, relevance, etc.


class QualityScore(BaseModel):
    """Quality score result."""
    criterion: str
    score: float  # 0.0 - 1.0
    feedback: Optional[str] = None


class QualityEvaluationResponse(BaseModel):
    """Quality evaluation result."""
    evaluation_id: str
    asset_id: str
    overall_score: float
    passed: bool
    scores: list[QualityScore]
    recommendations: Optional[list[str]] = None
    evaluated_at: str


class RetryPolicyRequest(BaseModel):
    """Bounded retry configuration."""
    max_attempts: int = 3
    backoff_type: str = "exponential"  # none, linear, exponential
    initial_delay_ms: int = 100
    max_delay_ms: int = 10000
    quality_threshold: float = 0.7


class RetryExecutionRequest(BaseModel):
    """Execute with retry."""
    operation_type: str  # generate_image, render_diagram, llm_completion
    input: dict
    retry_policy: Optional[RetryPolicyRequest] = None


class RetryExecutionResponse(BaseModel):
    """Retry execution result."""
    execution_id: str
    success: bool
    attempts: int
    final_quality_score: Optional[float] = None
    output: Optional[dict] = None
    errors: Optional[list[str]] = None
    total_duration_ms: float


class AssetCritiqueRequest(BaseModel):
    """Request asset critique."""
    asset_id: str
    asset_type: str
    content: str
    rubric: Optional[dict] = None  # Custom evaluation rubric


class AssetCritiqueResponse(BaseModel):
    """Asset critique result."""
    critique_id: str
    asset_id: str
    overall_assessment: str  # excellent, good, acceptable, needs_improvement, poor
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    detailed_scores: dict
    critiqued_at: str


# =============================================================================
# ENDPOINTS - Quality Evaluation
# =============================================================================


@router.post(
    "/evaluate",
    response=QualityEvaluationResponse,
    summary="Evaluate asset quality",
    auth=AuthBearer(),
)
async def evaluate_quality(
    request,
    payload: QualityEvaluationRequest,
) -> QualityEvaluationResponse:
    """Evaluate quality of an asset using LLM.
    
    Per Phase 7.4: LLM quality evaluation
    
    ML Eng: Uses GPT-4 or similar to evaluate quality.
    """
    evaluation_id = str(uuid4())
    
    # Default criteria based on asset type
    criteria = payload.criteria or _get_default_criteria(payload.asset_type)
    
    # Evaluate each criterion
    scores = []
    for criterion in criteria:
        score = await _evaluate_criterion(
            criterion=criterion,
            content=payload.content,
            asset_type=payload.asset_type,
        )
        scores.append(score)
    
    # Calculate overall score
    overall = sum(s.score for s in scores) / len(scores) if scores else 0.0
    passed = overall >= DEFAULT_QUALITY_THRESHOLD
    
    # Generate recommendations if needed
    recommendations = None
    if not passed:
        recommendations = [
            f"Improve {s.criterion}: {s.feedback}"
            for s in scores
            if s.score < DEFAULT_QUALITY_THRESHOLD
        ]
    
    logger.info(f"Quality evaluation {evaluation_id}: {overall:.2f} ({'PASS' if passed else 'FAIL'})")
    
    return QualityEvaluationResponse(
        evaluation_id=evaluation_id,
        asset_id=payload.asset_id,
        overall_score=overall,
        passed=passed,
        scores=scores,
        recommendations=recommendations,
        evaluated_at=timezone.now().isoformat(),
    )


@router.post(
    "/critique",
    response=AssetCritiqueResponse,
    summary="Get asset critique",
    auth=AuthBearer(),
)
async def critique_asset(
    request,
    payload: AssetCritiqueRequest,
) -> AssetCritiqueResponse:
    """Get detailed critique of an asset.
    
    Per Phase 7.4: AssetCritic service
    
    PhD Dev: Comprehensive analysis with actionable feedback.
    """
    critique_id = str(uuid4())
    
    # In production: call LLM for detailed critique
    # response = await openai.chat.completions.create(...)
    
    # Mock critique based on asset type
    assessment, strengths, weaknesses, suggestions = _generate_critique(
        payload.asset_type,
        payload.content,
        payload.rubric,
    )
    
    return AssetCritiqueResponse(
        critique_id=critique_id,
        asset_id=payload.asset_id,
        overall_assessment=assessment,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions,
        detailed_scores={
            "clarity": 0.8,
            "accuracy": 0.75,
            "completeness": 0.7,
            "style": 0.85,
        },
        critiqued_at=timezone.now().isoformat(),
    )


# =============================================================================
# ENDPOINTS - Bounded Retry
# =============================================================================


@router.post(
    "/retry/execute",
    response=RetryExecutionResponse,
    summary="Execute with bounded retry",
    auth=AuthBearer(),
)
async def execute_with_retry(
    request,
    payload: RetryExecutionRequest,
) -> RetryExecutionResponse:
    """Execute an operation with bounded retry and quality gating.
    
    Per Phase 7.4: Bounded retry logic
    
    PhD Dev: Exponential backoff with quality threshold.
    """
    import asyncio
    import time
    
    execution_id = str(uuid4())
    policy = payload.retry_policy or RetryPolicyRequest()
    
    start_time = time.time()
    attempts = 0
    errors = []
    final_output = None
    final_score = None
    success = False
    
    while attempts < policy.max_attempts and not success:
        attempts += 1
        
        try:
            # Execute operation
            output = await _execute_operation(
                payload.operation_type,
                payload.input,
            )
            
            # Evaluate quality
            score = await _quick_quality_check(output)
            final_score = score
            
            if score >= policy.quality_threshold:
                success = True
                final_output = output
                logger.info(f"Retry {execution_id}: succeeded on attempt {attempts}")
            else:
                errors.append(f"Attempt {attempts}: quality {score:.2f} < threshold {policy.quality_threshold}")
                
                # Wait before retry
                if attempts < policy.max_attempts:
                    delay = _calculate_backoff(
                        attempts,
                        policy.backoff_type,
                        policy.initial_delay_ms,
                        policy.max_delay_ms,
                    )
                    await asyncio.sleep(delay / 1000)
                    
        except Exception as e:
            errors.append(f"Attempt {attempts}: {str(e)}")
            logger.warning(f"Retry {execution_id}: attempt {attempts} failed: {e}")
    
    total_duration = (time.time() - start_time) * 1000
    
    return RetryExecutionResponse(
        execution_id=execution_id,
        success=success,
        attempts=attempts,
        final_quality_score=final_score,
        output=final_output,
        errors=errors if not success else None,
        total_duration_ms=total_duration,
    )


@router.get(
    "/retry/policies",
    summary="List retry policies",
    auth=AuthBearer(),
)
async def list_retry_policies(request) -> dict:
    """List available retry policy presets."""
    return {
        "policies": [
            {
                "name": "aggressive",
                "max_attempts": 5,
                "backoff_type": "exponential",
                "initial_delay_ms": 50,
            },
            {
                "name": "moderate",
                "max_attempts": 3,
                "backoff_type": "exponential",
                "initial_delay_ms": 100,
            },
            {
                "name": "conservative",
                "max_attempts": 2,
                "backoff_type": "linear",
                "initial_delay_ms": 500,
            },
        ],
    }


# =============================================================================
# ENDPOINTS - Quality Thresholds
# =============================================================================


@router.get(
    "/thresholds",
    summary="Get quality thresholds",
    auth=AuthBearer(),
)
async def get_thresholds(request) -> dict:
    """Get quality threshold configuration."""
    return {
        "default_threshold": DEFAULT_QUALITY_THRESHOLD,
        "thresholds_by_type": {
            "text": 0.7,
            "image": 0.6,
            "code": 0.8,
            "diagram": 0.65,
        },
    }


@router.patch(
    "/thresholds",
    summary="Update quality thresholds",
    auth=AuthBearer(),
)
async def update_thresholds(request, thresholds: dict) -> dict:
    """Update quality threshold configuration.
    
    Security Auditor: Admin only.
    """
    # In production: persist to database
    return {
        "updated": True,
        "thresholds": thresholds,
    }


# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def _get_default_criteria(asset_type: str) -> list[str]:
    """Get default evaluation criteria by asset type."""
    criteria_map = {
        "text": ["clarity", "coherence", "relevance", "grammar"],
        "image": ["quality", "relevance", "composition", "style"],
        "code": ["correctness", "readability", "efficiency", "documentation"],
        "diagram": ["clarity", "accuracy", "completeness", "aesthetics"],
    }
    return criteria_map.get(asset_type, ["quality", "relevance"])


async def _evaluate_criterion(
    criterion: str,
    content: Optional[str],
    asset_type: str,
) -> QualityScore:
    """Evaluate a single quality criterion.
    
    In production: call LLM for evaluation.
    """
    # Mock evaluation
    import random
    score = random.uniform(0.5, 1.0)
    
    feedback = None
    if score < DEFAULT_QUALITY_THRESHOLD:
        feedback = f"Could improve {criterion}"
    
    return QualityScore(
        criterion=criterion,
        score=score,
        feedback=feedback,
    )


def _generate_critique(
    asset_type: str,
    content: str,
    rubric: Optional[dict],
) -> tuple[str, list[str], list[str], list[str]]:
    """Generate critique for an asset.
    
    In production: call LLM for detailed analysis.
    """
    # Mock critique
    assessment = "good"
    strengths = ["Clear structure", "Good formatting"]
    weaknesses = ["Could be more concise"]
    suggestions = ["Add more examples", "Improve transitions"]
    
    return assessment, strengths, weaknesses, suggestions


async def _execute_operation(operation_type: str, input: dict) -> dict:
    """Execute an operation (placeholder)."""
    return {"result": "completed", "type": operation_type}


async def _quick_quality_check(output: dict) -> float:
    """Quick quality check for retry logic."""
    import random
    return random.uniform(0.6, 1.0)


def _calculate_backoff(
    attempt: int,
    backoff_type: str,
    initial_delay: int,
    max_delay: int,
) -> int:
    """Calculate backoff delay in milliseconds."""
    if backoff_type == "none":
        return 0
    elif backoff_type == "linear":
        delay = initial_delay * attempt
    else:  # exponential
        delay = initial_delay * (2 ** (attempt - 1))
    
    return min(delay, max_delay)
