"""
Quality Evaluation API.

Asset quality evaluation and bounded retry logic.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.core.helpers.service_urls import require_service_url
from services.common.authorization import authorize

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
    await authorize(request, action="system:read_metrics", resource="quality")
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

    logger.info(
        "Quality evaluation %s: %.2f (%s)", evaluation_id, overall, "PASS" if passed else "FAIL"
    )

    return QualityEvaluationResponse(
        evaluation_id=evaluation_id,
        asset_id=payload.asset_id,
        overall_score=overall,
        passed=passed,
        scores=scores,
        recommendations=recommendations,
        evaluated_at=timezone.now().isoformat(),
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
    await authorize(request, action="system:configure", resource="quality")
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
                logger.info("Retry %s: succeeded on attempt %s", execution_id, attempts)
            else:
                errors.append(
                    f"Attempt {attempts}: quality {score:.2f} < threshold {policy.quality_threshold}"
                )

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
            logger.warning("Retry %s: attempt %s failed: %s", execution_id, attempts, e)

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
    await authorize(request, action="system:view", resource="quality")
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
    """Get quality threshold configuration.

    Only the threshold this module actually applies is reported. There is
    no per-asset-type threshold store, and no endpoint to write one —
    claiming otherwise was inventing configuration.
    """
    await authorize(request, action="system:view", resource="quality")
    return {"default_threshold": DEFAULT_QUALITY_THRESHOLD}


# Threshold persistence is not implemented: there is no settings store wired
# for it. /thresholds is read-only until one exists.


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
    """Evaluate a single quality criterion using LLM."""
    import httpx
    from django.conf import settings

    # Checked BEFORE the request, not inside it. The previous code built
    # `Authorization: Bearer {LLM_API_KEY or ""}` and posted anyway, so a missing
    # key produced an unauthenticated call that failed as a bare 401 far away.
    # A missing credential is a configuration error and is reported as one
    # (VIBE Rule 164).
    llm_api_key = getattr(settings, "LLM_API_KEY", None)
    if not llm_api_key:
        raise HttpError(
            503,
            "Quality evaluation is not configured: LLM_API_KEY is missing. "
            "Set secret/agent/credentials/llm_api_key in Vault.",
        )

    try:
        llm_url = require_service_url("LLM_API_URL")

        prompt = f"""Evaluate the following {asset_type} content for {criterion} on a scale of 0.0 to 1.0.
        
Content: {content[:500] if content else "No content provided"}

Respond with ONLY a JSON object in this format:
{{"score": 0.X, "feedback": "Brief explanation"}}"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                llm_url,
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": getattr(settings, "QUALITY_EVAL_MODEL", "gpt-4o-mini"),
                    "max_tokens": 100,
                },
                headers={"Authorization": f"Bearer {llm_api_key}"},
            )

            if response.status_code == 200:
                import json

                result = response.json()
                content_text = result.get("content", result.get("message", {}).get("content", ""))
                # Parse JSON from response
                try:
                    eval_result = json.loads(content_text.strip())
                except json.JSONDecodeError:
                    raise HttpError(
                        502,
                        "Quality evaluation failed: the LLM did not return parsable JSON.",
                    )
                if "score" not in eval_result:
                    raise HttpError(
                        502,
                        "Quality evaluation failed: the LLM returned no score.",
                    )
                return QualityScore(
                    criterion=criterion,
                    score=float(eval_result["score"]),
                    feedback=eval_result.get("feedback"),
                )

    except Exception as e:
        logger.error("Quality evaluation error: %s", e)
        raise HttpError(502, f"Quality evaluation unavailable: {e}")

    raise HttpError(502, "Quality evaluation failed: LLM returned no parsable score.")


async def _execute_operation(operation_type: str, input_data: dict) -> dict:
    """Execute an operation via appropriate service."""
    import httpx
    from django.conf import settings

    # Route to appropriate service
    service_urls = {
        "generate_image": require_service_url("IMAGE_GEN_URL"),
        "render_diagram": require_service_url("DIAGRAM_URL"),
        "llm_completion": require_service_url("LLM_API_URL"),
    }

    url = service_urls.get(operation_type)
    if not url:
        raise HttpError(400, f"Unknown operation_type: {operation_type!r}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=input_data)
            if response.status_code == 200:
                return {"result": "completed", "type": operation_type, "data": response.json()}
            else:
                return {"result": "error", "type": operation_type, "status": response.status_code}
    except Exception as e:
        logger.error("Operation %s failed: %s", operation_type, e)
        raise


async def _quick_quality_check(output: dict) -> float:
    """Score an operation's output with the real LLM evaluator.

    This used to return invented constants derived from
    ``len(str(output))`` — 0.9 for "more than 100 characters", 0.7 for
    "completed but empty", and so on. Those numbers drove the retry gate
    and had nothing to do with the quality of the output. Now the score
    comes from the same LLM evaluation that ``/evaluate`` uses.
    """
    import json

    if not output:
        raise HttpError(502, "Operation produced no output to evaluate.")

    score = await _evaluate_criterion(
        criterion="quality",
        content=json.dumps(output, default=str)[:4000],
        asset_type="text",
    )
    return score.score


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


