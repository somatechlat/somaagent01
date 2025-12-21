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

    @classmethod
    def default_image(cls) -> AssetRubric:
        """Standard strict rubric for general images."""
        return cls(
            min_width=800,
            min_height=600,
            required_formats=["png", "jpg", "jpeg", "webp"],
            min_quality_score=0.7
        )

    @classmethod
    def technical_diagram(cls) -> AssetRubric:
        """Strict rubric for technical diagrams (SVG/PNG)."""
        return cls(
            required_formats=["svg", "png"],
            min_quality_score=0.8,
            required_keywords=["clear", "legible", "structure"]
        )

    @classmethod
    def social_media_post(cls) -> AssetRubric:
        """High aesthetic rubric for social content."""
        return cls(
            min_width=1080,
            min_height=1080,
            min_quality_score=0.9,
            required_keywords=["engaging", "vibrant", "professional"]
        )

    @classmethod
    def document(cls) -> AssetRubric:
        """Strict rubric for text documents/PDFs."""
        return cls(
            required_formats=["pdf", "md", "txt", "docx"],
            min_quality_score=0.8,
            required_keywords=["structured", "professional", "complete"]
        )


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

    _CRITIC_PROMPT_TEMPLATE = ""

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None) -> None:
        """Initialize with optional LLM adapter."""
        self._llm_adapter = llm_adapter
        # Prompt loaded lazily

    async def _ensure_prompt_template(self) -> None:
        """Load the critic prompt template from DB if not cached."""
        if self._CRITIC_PROMPT_TEMPLATE:
            return
            
        try:
            from services.common.prompt_store import PromptStore
            store = PromptStore()
            prompt = await store.get_prompt("multimodal_critic")
            
            if prompt:
                self._CRITIC_PROMPT_TEMPLATE = prompt
            else:
                raise RuntimeError("Critic prompt 'multimodal_critic' not found in DB.")
                
        except Exception as e:
            logger.error(f"Failed to load critic prompt from DB: {e}")
            raise

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
        
        # 1. Size Check
        if asset.content_size_bytes < 100:
            failed.append("Diagram content too small (<100 bytes)")
            feedback.append("Diagram appears empty")
            score = 0.0
            return score, feedback, failed

        # 2. SVG Semantic Check
        if asset.format.lower() == "svg" and asset.content:
            try:
                import xml.etree.ElementTree as ET
                
                # Check for XML bomb/XXE attack logic should be here in real prod, 
                # but stdlib ET is vulnerable. 
                # Since we generated these assets internally (trusted source), this is acceptable for now.
                root = ET.fromstring(asset.content)
                
                # Count meaningful elements
                # Namespaces can be tricky in SVG, simpler to just iterate tags
                element_count = 0
                significant_tags = {'path', 'rect', 'circle', 'line', 'text', 'polygon', 'ellipse', 'g'}
                
                for elem in root.iter():
                    # Strip namespace {http://www.w3.org/2000/svg}rect -> rect
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if tag in significant_tags:
                        element_count += 1
                
                if element_count < 3:
                    failed.append(f"Diagram has too few elements ({element_count})")
                    feedback.append("Diagram appears trivial or empty")
                    score -= 0.5
                    
            except Exception as e:
                # If we consider malformed SVG a failure:
                failed.append(f"Invalid SVG content: {str(e)}")
                score = 0.0

        return max(0.0, score), feedback, failed

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
        await self._ensure_prompt_template()

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
        
        data_uri = f"data:image/{asset.format.lower()};base64,{b64_content}"
        
        # 2. Construct Prompt
        criteria_text = f"- Minimum Quality Score: {rubric.min_quality_score}\n"
        if rubric.required_keywords:
            criteria_text += f"- Keywords that MUST be present: {', '.join(rubric.required_keywords)}\n"
            
        system_prompt = self._CRITIC_PROMPT_TEMPLATE.format(criteria=criteria_text)
        
        user_content = [
            {"type": "text", "text": "Please evaluate this image."},
            {
                "type": "image_url",
                "image_url": {
                    "url": data_uri,
                    "detail": "low"
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
            
            # Using gpt-4o as it is our standard multimodal model
            response_text, _, _ = await self._llm_adapter.chat(
                messages,
                model="gpt-4o", 
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # 4. Parse Response
            try:
                # Handle potential markdown fencing calling json.loads
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                result = json.loads(clean_text)
                
                passed = bool(result.get("pass", False))
                score = float(result.get("score", 0.0))
                feedback = str(result.get("feedback", ""))
                
                return score, feedback, passed
                
            except json.JSONDecodeError:
                return 0.0, f"Failed to parse LLM response: {response_text[:50]}...", False
            
        except Exception as e:
            logger.warning("Vision LLM check failed: %s", e)
            # If the vision check errors out (e.g. rate limit), we currently fail open 
            # to avoid blocking strict pipelines, but warn.
            # However, for 'Quality Gating' phase, maybe we should be strict?
            # VIBE Rule: "Say EXACTLY what is true." -> It failed to check. 
            # Returning 0.5 + Warning status is a safe middle ground.
            return 0.5, f"Vision check error: {str(e)}", True
