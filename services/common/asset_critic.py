"""Asset Critic service for quality gating.

Evaluates multimodal assets against defined quality rubrics using strict heuristics
and prepared hooks for LLM-based evaluation.

SRS Reference: Section 16.7 (Quality Gating)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.common.asset_store import AssetRecord, AssetType

from services.common.llm_adapter import LLMAdapter

__all__ = [
    "AssetCritic",
    "AssetRubric",
    "AssetEvaluation",
    "evaluation_status",
]

logger = logging.getLogger(__name__)


class evaluation_status(str, Enum):
    """Status of an asset evaluation."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass(slots=True)
class AssetRubric:
    """Criteria for evaluating an asset.
    
    Attributes:
        min_width: Minimum width in pixels (images/video)
        min_height: Minimum height in pixels (images/video)
        max_size_bytes: Maximum file size
        required_formats: List of allowed formats
        required_keywords: Keywords that must verify in content/metadata
        min_quality_score: Minimum LLM-assessed score (0.0-1.0)
    """
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    max_size_bytes: Optional[int] = None
    required_formats: Optional[List[str]] = None
    required_keywords: Optional[List[str]] = None
    min_quality_score: float = 0.7


@dataclass(slots=True)
class AssetEvaluation:
    """Result of an asset evaluation.
    
    Attributes:
        asset_id: ID of evaluated asset
        status: Pass/Fail/Warn
        score: Numerical quality score (0.0-1.0)
        feedback: List of feedback strings
        failed_criteria: List of criteria that failed
    """
    asset_id: UUID
    status: evaluation_status
    score: float
    feedback: List[str] = field(default_factory=list)
    failed_criteria: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == evaluation_status.PASSED


class AssetCritic:
    """Service for evaluating asset quality.
    
    Applies heuristic and semantic checks to ensure assets meet
    defined quality standards.
    
    Usage:
        critic = AssetCritic()
        rubric = AssetRubric(min_width=1024)
        result = await critic.evaluate(asset, rubric)
    """

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None) -> None:
        """Initialize with optional LLM adapter."""
        self._llm_adapter = llm_adapter

    async def evaluate(
        self,
        asset: AssetRecord,
        rubric: AssetRubric,
        context: Optional[Dict[str, Any]] = None,
    ) -> AssetEvaluation:
        """Evaluate an asset against a rubric.
        
        Args:
            asset: Asset to evaluate
            rubric: Validation criteria
            context: Execution context for LLM evaluation
            
        Returns:
            AssetEvaluation result
        """
        feedback: List[str] = []
        failed: List[str] = []
        score = 1.0  # Start perfect, deduct for issues
        
        # 1. Heuristic Checks
        if asset.asset_type == AssetType.IMAGE:
            h_score, h_feedback, h_failed = self._evaluate_image_heuristics(asset, rubric)
            score = min(score, h_score)
            feedback.extend(h_feedback)
            failed.extend(h_failed)
            
        elif asset.asset_type == AssetType.DIAGRAM:
            h_score, h_feedback, h_failed = self._evaluate_diagram_heuristics(asset, rubric)
            score = min(score, h_score)
            feedback.extend(h_feedback)
            failed.extend(h_failed)
        
        # 2. Format Checks
        if rubric.required_formats:
            if asset.format.lower() not in [f.lower() for f in rubric.required_formats]:
                failed.append(f"Format {asset.format} not in {rubric.required_formats}")
                feedback.append("Invalid file format")
                score = 0.0
        
        # 3. Size Checks
        if rubric.max_size_bytes and asset.content_size_bytes > rubric.max_size_bytes:
            failed.append(f"Size {asset.content_size_bytes} > {rubric.max_size_bytes}")
            feedback.append("File size too large")
            score = max(0.0, score - 0.2)
            
        # 4. LLM Semantic Checks (Only if heuristics pass and client available)
        if not failed and self._llm_adapter and rubric.min_quality_score > 0:
            if asset.asset_type == AssetType.IMAGE:
                llm_score, llm_feedback, llm_passed = await self._evaluate_image_llm(asset, rubric, context)
                if not llm_passed:
                    score = min(score, llm_score)
                    if llm_feedback:
                        feedback.append(f"Aesthetice/Semantic issue: {llm_feedback}")
                        # If score is very low, mark as failed constraint
                        if llm_score < 0.4:
                            failed.append(f"LLM quality check failed (score {llm_score:.2f})")
                else:
                    # Average with heuristic score if passed
                    score = (score + llm_score) / 2
                    if llm_feedback:
                         feedback.append(f"LLM Feedback: {llm_feedback}")

        # Determine status
        if failed:
            status = evaluation_status.FAILED
        elif score < rubric.min_quality_score:
            status = evaluation_status.WARNING
            feedback.append(f"Score {score:.2f} below threshold {rubric.min_quality_score}")
        else:
            status = evaluation_status.PASSED
            
        return AssetEvaluation(
            asset_id=asset.id,
            status=status,
            score=score,
            feedback=feedback,
            failed_criteria=failed,
        )

    def _evaluate_image_heuristics(
        self,
        asset: AssetRecord,
        rubric: AssetRubric,
    ) -> tuple[float, List[str], List[str]]:
        """Evaluate image-specific heuristics."""
        score = 1.0
        feedback = []
        failed = []
        
        dims = asset.dimensions or {}
        width = dims.get("width", 0)
        height = dims.get("height", 0)
        
        if rubric.min_width and width < rubric.min_width:
            failed.append(f"Width {width} < {rubric.min_width}")
            feedback.append("Image resolution too low (width)")
            score -= 0.3
            
        if rubric.min_height and height < rubric.min_height:
            failed.append(f"Height {height} < {rubric.min_height}")
            feedback.append("Image resolution too low (height)")
            score -= 0.3
            
        return max(0.0, score), feedback, failed

    def _evaluate_diagram_heuristics(
        self,
        asset: AssetRecord,
        rubric: AssetRubric,
    ) -> tuple[float, List[str], List[str]]:
        """Evaluate diagram-specific heuristics."""
        score = 1.0
        feedback = []
        failed = []
        
        # Diagrams (SVG) might not have dimensions in metadata
        # Heuristic: SVGs should generally be larger than a few bytes
        if asset.content_size_bytes < 100:
            failed.append("Diagram content too small (<100 bytes)")
            feedback.append("Diagram appears empty")
            score = 0.0
            
        return score, feedback, failed

    async def _evaluate_image_llm(
        self,
        asset: AssetRecord,
        rubric: AssetRubric,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[float, Optional[str], bool]:
        """Evaluate image using Vision LLM.
        
        Constructs a multimodal payload with base64-encoded image and defined criteria.
        Expects LLM to return JSON with score/feedback.
        """
        if not self._llm_adapter or not asset.content:
            return 0.5, "Skipped check (no client or content)", True
            
        import base64
        import json
        
        # 1. Base64 Encode
        try:
            b64_content = base64.b64encode(asset.content).decode("utf-8")
        except Exception:
            return 0.5, "Failed to encode image", True
            
        data_uri = f"data:image/{asset.format.lower()};base64,{b64_content}"
        
        # 2. Construct Prompt
        system_prompt = (
            "You are an expert design critic. Evaluate the provided image against these criteria:\n"
            f"- Minimum Quality Score: {rubric.min_quality_score}\n"
            f"- Keywords: {', '.join(rubric.required_keywords or [])}\n"
            "Return JSON only: { \"pass\": bool, \"score\": float(0.0-1.0), \"feedback\": \"string\" }"
        )
        
        user_content = [
            {"type": "text", "text": "Please evaluate this image."},
            {
                "type": "image_url",
                "image_url": {
                    "url": data_uri,
                    "detail": "low" # Low detail for speed/cost efficiency
                }
            }
        ]
        
        # 3. Call LLMAdapter
        try:
            from services.common.llm_adapter import ChatMessage
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_content),
            ]
            
            response_text, _ = await self._llm_adapter.chat(
                messages,
                model="gpt-4o", # Model with vision capabilities
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # 4. Parse Response
            result = json.loads(response_text)
            passed = result.get("pass", False)
            score = float(result.get("score", 0.0))
            feedback = result.get("feedback", "")
            
            return score, feedback, passed
            
        except Exception as e:
            logger.warning("Vision LLM check failed: %s", e)
            return 0.5, "Vision check error (defaulted pass)", True

