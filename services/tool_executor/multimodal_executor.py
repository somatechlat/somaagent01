"""Multimodal Executor service.

Orchestrates the execution of multimodal job plans. Manages dependencies,
selects appropriate providers, executes tasks, stores assets, and tracks progress.

SRS Reference: Section 16.6 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID


from services.common.asset_store import AssetStore, AssetType, AssetFormat
from services.common.asset_critic import AssetCritic, AssetRubric, evaluation_status
from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.multimodal.base_provider import (
    MultimodalProvider,
    GenerationRequest,
    GenerationResult,
    ProviderError,
    ProviderCapability,
)
from services.multimodal.dalle_provider import DalleProvider
from services.multimodal.mermaid_provider import MermaidProvider
from services.multimodal.playwright_provider import PlaywrightProvider
from src.core.config import cfg

__all__ = ["MultimodalExecutor", "ExecutorError"]

logger = logging.getLogger(__name__)


class ExecutorError(Exception):
    """Base exception for executor errors."""
    pass


class MultimodalExecutor:
    """Orchestrates multimodal job execution.
    
    Coordinates providers, asset storage, and execution tracking to fulfill
    multimodal job plans. Handles dependency resolution and error recovery.
    
    Usage:
        executor = MultimodalExecutor()
        await executor.initialize()
        await executor.execute_plan(plan_id)
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        asset_store: Optional[AssetStore] = None,
        job_planner: Optional[JobPlanner] = None,
        execution_tracker: Optional[ExecutionTracker] = None,
        asset_critic: Optional[AssetCritic] = None,
        soma_brain_client: Optional[SomaBrainClient] = None,
    ) -> None:
        """Initialize executor with services.
        
        Args:
            dsn: Database connection string
            asset_store: AssetStore instance
            job_planner: JobPlanner instance
            execution_tracker: ExecutionTracker instance
            asset_critic: AssetCritic instance for quality gating
            soma_brain_client: SomaBrainClient instance for learning
        """
        self._dsn = dsn or cfg.settings().database.dsn
        self._asset_store = asset_store or AssetStore(dsn=self._dsn)
        self._job_planner = job_planner or JobPlanner(dsn=self._dsn)
        self._execution_tracker = execution_tracker or ExecutionTracker(dsn=self._dsn)
        self._execution_tracker = execution_tracker or ExecutionTracker(dsn=self._dsn)
        self._soma_brain_client = soma_brain_client or SomaBrainClient()
        
        # Initialize SLM Client for AssetCritic if needed
        # In a real app, we might inject this from a factory or globals
        from services.common.slm_client import SLMClient
        self._slm_client = SLMClient() if cfg.settings().llm.openai_api_key else None
        
        self._asset_critic = asset_critic or AssetCritic(slm_client=self._slm_client)
        
        # Initialize providers registry
        self._providers: Dict[str, MultimodalProvider] = {}
        self._capability_map: Dict[ProviderCapability, List[str]] = {}

    async def initialize(self) -> None:
        """Initialize providers and verify dependencies."""
        # Register default providers
        await self.register_provider(MermaidProvider())
        await self.register_provider(PlaywrightProvider())
        
        # Only register DALL-E if API key is present
        dalle = DalleProvider()
        if await dalle.health_check():
            await self.register_provider(dalle)
        else:
            logger.warning("DALL-E provider not available (missing API key?)")

    async def register_provider(self, provider: MultimodalProvider) -> None:
        """Register a provider instance.
        
        Args:
            provider: Provider instance to register
        """
        self._providers[provider.name] = provider
        
        # Update capability map
        for cap in provider.capabilities:
            if cap not in self._capability_map:
                self._capability_map[cap] = []
            self._capability_map[cap].append(provider.name)
            
        logger.info("Registered provider: %s", provider.name)

    async def execute_plan(self, plan_id: UUID) -> bool:
        """Execute a full job plan.
        
        Args:
            plan_id: UUID of plan to execute
            
        Returns:
            True if execution completed successfully
        """
        plan = await self._job_planner.get(plan_id)
        if not plan:
            raise ExecutorError(f"Plan {plan_id} not found")
        
        if plan.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
            logger.info("Plan %s already finished via status %s", plan_id, plan.status)
            return True
            
        # Update status to RUNNING
        await self._job_planner.update_status(plan.id, JobStatus.RUNNING)
        
        context: Dict[str, Any] = {}
        failed = False
        error_msg = None
        
        try:
            # Execute tasks in order (plan.tasks is already topologically sorted)
            for i, task in enumerate(plan.tasks):
                # Skip if already completed (resumption logic)
                latest_exec = await self._execution_tracker.get_latest_for_step(plan.id, i)
                # Check for cached asset in store
                if latest_exec and latest_exec.status == ExecutionStatus.SUCCESS:
                    logger.info("Step %d (%s) already completed", i, task.task_id)
                    if latest_exec.asset_id:
                        asset = await self._asset_store.get(latest_exec.asset_id)
                        if asset:
                            context[task.task_id] = asset
                    continue
                
                # Execute step with retry loop
                success = await self._execute_step(plan, i, task, context)
                if not success:
                    failed = True
                    # Check if failure was due to quality gate exhaustion
                    error_msg = f"Step {task.task_id} failed after max attempts"
                    break
                    
                # Update progress
                await self._job_planner.update_status(
                    plan.id,
                    JobStatus.RUNNING,
                    completed_steps=i + 1
                )
            
            # Final status update
            status = JobStatus.FAILED if failed else JobStatus.COMPLETED
            await self._job_planner.update_status(
                plan.id,
                status,
                error_message=error_msg
            )
            return not failed
            
        except Exception as exc:
            logger.exception("Plan execution failed: %s", exc)
            await self._job_planner.update_status(
                plan.id,
                JobStatus.FAILED,
                error_message=str(exc)
            )
            return False

    async def _execute_step(
        self,
        plan: JobPlan,
        step_index: int,
        task: TaskStep,
        context: Dict[str, Any],
    ) -> bool:
        """Execute a single task step with rework/retry loop.
        
        Args:
            plan: Parent plan
            step_index: Index of step
            task: Task definition
            context: Execution context (results of previous steps)
            
        Returns:
            True if successful, False if all attempts failed
        """
        # Resolve provider
        provider = self._select_provider(task)
        if not provider:
            msg = f"No provider found for step type {task.step_type}"
            logger.error(msg)
            await self._execution_tracker.start(
                plan.id, step_index, plan.tenant_id, "unknown", "unknown"
            )
            return False
            
        # Determine retry limits
        max_attempts = 1
        gate_config = task.quality_gate
        if gate_config.get("enabled", True):
            max_attempts = gate_config.get("max_reworks", 2) + 1  # 2 reworks = 3 attempts total

        # Rework loop
        attempt = 0
        prompt_feedback = ""
        
        while attempt < max_attempts:
            attempt += 1
            is_retry = attempt > 1
            
            # Prepare request with injected feedback if retry
            base_prompt = self._resolve_dependencies(task.params.get("prompt", ""), context)
            if is_retry and prompt_feedback:
                # Basic prompt injection logic for V1
                full_prompt = (
                    f"{base_prompt}\n\n"
                    f"IMPORTANT: The previous attempt failed quality checks. "
                    f"Please address this feedback: {prompt_feedback}"
                )
            else:
                full_prompt = base_prompt
                
            request = GenerationRequest(
                tenant_id=plan.tenant_id,
                session_id=plan.session_id,
                modality=task.modality,
                prompt=full_prompt,
                request_id=plan.request_id,
                format=task.params.get("format", "png"),
                dimensions=task.params.get("dimensions"),
                parameters=task.params,
            )
            
            # Start tracking execution
            exec_record = await self._execution_tracker.start(
                plan.id,
                step_index,
                plan.tenant_id,
                provider.name,
                provider.provider_id,
                attempt_number=attempt,
            )
            
            try:
                # Generate
                result = await provider.generate(request)
                
                if not result.success:
                    # Provider error (e.g. timeout, rate limit)
                    # We treat provider errors as attempt failures too for now
                    logger.warning(
                        "Step %s attempt %d failed: %s", 
                        task.task_id, attempt, result.error_message
                    )
                    await self._execution_tracker.complete(
                        exec_record.id,
                        ExecutionStatus.FAILED,
                        error_code=result.error_code,
                        error_message=result.error_message,
                    )
                    prompt_feedback = f"Provider error: {result.error_message}"
                    # Could add exponential backoff here if needed
                    continue

                # Map content type to asset type
                asset_type = AssetType.IMAGE
                if result.content_type and "svg" in result.content_type:
                    asset_type = AssetType.DIAGRAM
                elif result.content_type and "pdf" in result.content_type:
                    asset_type = AssetType.DOCUMENT
                
                # Create temporary asset object for evaluation (or persist first?)
                # Persisting first allows lineage tracking of failed attempts
                asset = await self._asset_store.create(
                    tenant_id=plan.tenant_id,
                    asset_type=asset_type,
                    asset_format=AssetFormat(result.format) if result.format else AssetFormat.PNG,
                    content=result.content,
                    metadata={
                        "plan_id": str(plan.id),
                        "task_id": task.task_id,
                        "provider": provider.name,
                        "dimensions": result.dimensions,
                        "attempt": attempt,
                    }
                )
                
                # Quality Gate Check
                if gate_config.get("enabled", True):
                    rubric = AssetRubric(
                         # TODO: Map from task.params/constraints to rubric
                         min_width=task.constraints.get("min_width"),
                         min_height=task.constraints.get("min_height"),
                         max_size_bytes=task.constraints.get("max_size_bytes"),
                    )
                    evaluation = await self._asset_critic.evaluate(
                        asset, 
                        rubric,
                        context=context  # Pass context for LLM evaluation
                    )
                    
                    if not evaluation.passed:
                        logger.warning(
                            "Step %s attempt %d failed quality gate: %s",
                            task.task_id, attempt, evaluation.failed_criteria
                        )
                        # Mark execution as failed due to quality
                        await self._execution_tracker.complete(
                            exec_record.id,
                            ExecutionStatus.FAILED,
                            asset_id=asset.id,
                            error_code="QUALITY_GATE_FAILED",
                            error_message=f"Quality check failed: {evaluation.failed_criteria}",
                            latency_ms=result.latency_ms,
                            cost_estimate_cents=result.cost_cents,
                        )
                        
                        prompt_feedback = "; ".join(evaluation.feedback)
                        continue
                        
                # Success!
                context[task.task_id] = asset
                await self._execution_tracker.complete(
                    exec_record.id,
                    ExecutionStatus.SUCCESS,
                    asset_id=asset.id,
                    latency_ms=result.latency_ms,
                    cost_estimate_cents=result.cost_cents,
                )
                return True
                
            except Exception as exc:
                logger.exception("Step execution attempt %d error: %s", attempt, exc)
                await self._execution_tracker.complete(
                    exec_record.id,
                    ExecutionStatus.FAILED,
                    error_message=str(exc),
                )
                prompt_feedback = f"System error: {str(exc)}"
                
            finally:
                # NEW: Record outcome for learning
                if 'result' in locals() and result:  # Check if result was assigned
                     # Calculate quality score (default 0.0 if failed, or passed eval score)
                    q_score = 0.0
                    explanation = None
                    if 'evaluation' in locals() and evaluation:
                        q_score = evaluation.score
                        explanation = "; ".join(evaluation.feedback) if evaluation.feedback else None
                    
                    outcome = MultimodalOutcome(
                        plan_id=str(plan.id),
                        task_id=task.task_id,
                        step_type=task.step_type.value,
                        provider=provider.name,
                        model=getattr(provider, "model", "unknown"),
                        success=result.success if result else False,
                        latency_ms=result.latency_ms if result else 0.0,
                        cost_cents=result.cost_cents if result else 0.0,
                        quality_score=q_score,
                        feedback=explanation or (result.error_message if result and not result.success else None)
                    )
                    await self._soma_brain_client.record_outcome(outcome)
                
        # If loop finishes without returning True, we failed
        logger.error("Step %s failed after %d attempts", task.task_id, max_attempts)
        return False

    def _select_provider(self, task: TaskStep) -> Optional[MultimodalProvider]:
        """Select appropriate provider for task."""
        # Simple selection logic for now
        # In future: use constraints, checking availability, costs, etc.
        
        if task.step_type == StepType.GENERATE_DIAGRAM:
            return self._providers.get("mermaid_diagram")
        elif task.step_type == StepType.GENERATE_IMAGE:
            # Prefer DALL-E if available
            return self._providers.get("dalle3_image_gen")
        elif task.step_type == StepType.CAPTURE_SCREENSHOT:
            return self._providers.get("playwright_screenshot")
            
        return None

    def _resolve_dependencies(self, prompt: str, context: Dict[str, Any]) -> str:
        """Resolve dependency placeholders in prompt.
        
        Replaces {{task_id.url}} or similar patterns with actual values
        from context.
        """
        resolved = prompt
        for task_id, asset in context.items():
            if f"{{{{{task_id}}}}}" in resolved:
                # Basic substitution, relying on string repr or ID
                resolved = resolved.replace(f"{{{{{task_id}}}}}", str(asset.id))
        return resolved
