"""Multimodal Executor service.

Orchestrates the execution of multimodal job plans. Manages dependencies,
selects appropriate providers, executes tasks, stores assets, and tracks progress.

SRS Reference: Section 16.6 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime


from services.common.asset_store import AssetStore, AssetType, AssetFormat
from services.common.asset_critic import AssetCritic, AssetRubric, evaluation_status
from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome
from services.common.portfolio_ranker import PortfolioRanker
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.common.policy_graph_router import PolicyGraphRouter
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
        policy_router: Optional[PolicyGraphRouter] = None,
    ) -> None:
        """Initialize executor with services.
        
        Args:
            dsn: Database connection string
            asset_store: AssetStore instance
            job_planner: JobPlanner instance
            execution_tracker: ExecutionTracker instance
            asset_critic: AssetCritic instance for quality gating
            soma_brain_client: SomaBrainClient instance for learning
            policy_router: PolicyGraphRouter instance for provider selection
        """
        self._dsn = dsn or cfg.settings().database.dsn
        self._asset_store = asset_store or AssetStore(dsn=self._dsn)
        self._job_planner = job_planner or JobPlanner(dsn=self._dsn)
        self._execution_tracker = execution_tracker or ExecutionTracker(dsn=self._dsn)
        self._soma_brain_client = soma_brain_client or SomaBrainClient()
        self._portfolio_ranker = PortfolioRanker(self._soma_brain_client)
        self._policy_router = policy_router or PolicyGraphRouter(dsn=self._dsn)
        
        # Initialize LLM Adapter for AssetCritic if needed
        # In a real app, we might inject this from a factory or globals
        from services.common.llm_adapter import LLMAdapter
        api_key = cfg.env("SA01_OPENAI_API_KEY")
        self._llm_adapter = LLMAdapter(api_key=str(api_key)) if api_key else None
        
        self._asset_critic = asset_critic or AssetCritic(llm_adapter=self._llm_adapter)
        
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
                success, step_error = await self._execute_step(plan, i, task, context)
                if not success:
                    failed = True
                    # Check if failure was due to quality gate exhaustion
                    error_msg = step_error or f"Step {task.task_id} failed after max attempts"
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
    ) -> Tuple[bool, Optional[str]]:
        """Execute a single task step with rework/retry loop.
        
        Args:
            plan: Parent plan
            step_index: Index of step
            task: Task definition
            context: Execution context (results of previous steps)
            
        Returns:
            Tuple of (Success boolean, Error message if failed)
        """
        # Provider Fallback Loop
        # We try providers in order from the PolicyGraphRouter
        # If a provider fails (error or quality), we add it to exclusions and try next
        
        failed_providers: List[Tuple[str, str]] = []
        last_error_message = ""
        
        # Infinite loop, broken by success or router exhaustion
        while True:
            # 1. Select Provider
            decision = await self._policy_router.route(
                modality=self._map_step_type_to_modality(task.step_type),
                tenant_id=plan.tenant_id,
                budget_used_cents=0,
                excluded_options=failed_providers,
                context={"intent": task.step_type.value}
            )
            
            # --- SHADOW MODE RANKING ---
            try:
                 shadow_candidates = []
                 if decision.success:
                     shadow_candidates.append((decision.tool_id, decision.model or "default"))
                 
                 ranked = self._portfolio_ranker.rank(shadow_candidates, task.step_type.value)
                 
                 if ranked and decision.success:
                     top_pick_id = ranked[0][0]
                     if top_pick_id != decision.tool_id:
                         logger.info(f"SHADOW DIVERGENCE: Policy={decision.tool_id}, Ranker={top_pick_id}")
            except Exception as e:
                logger.warning(f"Shadow ranking failed: {e}")
            # ---------------------------
            
            if not decision.success:
                # No more providers avaiable
                error_msg = f"No capability available. Exhausted: {failed_providers}. Last error: {last_error_message}"
                logger.error(
                    "Step %s failed: %s", 
                    task.task_id, error_msg
                )
                # Ensure we record a failure event if we haven't already
                if not failed_providers:
                     await self._execution_tracker.start(
                        plan.id, step_index, plan.tenant_id, "unknown", "unknown"
                    )
                return False, error_msg
                
            provider = self._providers.get(decision.tool_id)
            if not provider:
                # Should not happen if registry and executor are in sync
                logger.error("Provider %s approved by router but not loaded in executor", decision.tool_id)
                failed_providers.append((decision.tool_id, decision.provider))
                continue

            logger.info("Step %s selected provider %s (tool: %s)", task.task_id, decision.provider, decision.tool_id)

            # 2. Rework/Retry Loop (Same Provider)
            # Determines how many times we try THIS provider before falling back
            max_attempts = 1
            gate_config = task.quality_gate
            if gate_config.get("enabled", True):
                max_attempts = gate_config.get("max_reworks", 2) + 1
            
            attempt = 0
            prompt_feedback = ""
            provider_success = False
            
            while attempt < max_attempts:
                attempt += 1
                is_retry = attempt > 1
                
                # Prepare prompt
                base_prompt = self._resolve_dependencies(task.params.get("prompt", ""), context)
                if is_retry and prompt_feedback:
                    full_prompt = (
                        f"{base_prompt}\n\n"
                        f"CRITIC FEEDBACK: {prompt_feedback}"
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
                
                # Track Execution
                exec_record = await self._execution_tracker.start(
                    plan.id,
                    step_index,
                    plan.tenant_id,
                    provider.name,
                    provider.provider_id,
                    attempt_number=attempt,
                )
                
                try:
                    result = await provider.generate(request)
                    
                    if not result.success:
                        # Provider runtime error
                        logger.warning(
                            "Step %s provider %s attempt %d failure: %s",
                            task.task_id, provider.name, attempt, result.error_message
                        )
                        last_error_message = result.error_message
                        await self._execution_tracker.complete(
                            exec_record.id,
                            ExecutionStatus.FAILED,
                            error_code=result.error_code,
                            error_message=result.error_message,
                        )
                        prompt_feedback = f"Provider error: {result.error_message}"
                        # Try next attempt with same provider? Or fail provider immediately?
                        # Strategy: Runtime errors might be transient, retry unless critical.
                        continue
                        
                    # Asset Creation
                    asset_type = AssetType.IMAGE
                    if result.content_type and "svg" in result.content_type:
                        asset_type = AssetType.DIAGRAM
                    elif result.content_type and "pdf" in result.content_type:
                        asset_type = AssetType.DOCUMENT
                        
                    asset = await self._asset_store.create(
                        tenant_id=plan.tenant_id,
                        asset_type=asset_type,
                        format=AssetFormat(result.format).value if result.format else AssetFormat.PNG.value,
                        content=result.content,
                        dimensions=result.dimensions,
                        metadata={
                            "plan_id": str(plan.id),
                            "task_id": task.task_id,
                            "provider": provider.name,
                            "attempt": attempt,
                        }
                    )
                    
                    # Quality Gate
                    if gate_config.get("enabled", True):
                        # Construct Rubric from Task Constraints + Presets
                        if task.step_type == StepType.GENERATE_DIAGRAM:
                            rubric = AssetRubric.technical_diagram()
                        else:
                            rubric = AssetRubric.default_image()
                        
                        # Apply overrides
                        if task.constraints.get("min_width"):
                            rubric.min_width = task.constraints.get("min_width")
                        
                        evaluation = await self._asset_critic.evaluate(
                            asset, rubric, context=context
                        )
                        
                        if not evaluation.passed:
                             logger.warning(
                                "Step %s provider %s validation failed: %s",
                                task.task_id, provider.name, evaluation.failed_criteria
                             )
                             await self._execution_tracker.complete(
                                exec_record.id,
                                ExecutionStatus.FAILED,
                                asset_id=asset.id,
                                error_code="QUALITY_GATE_FAILED",
                                error_message=str(evaluation.failed_criteria),
                                latency_ms=result.latency_ms,
                                cost_estimate_cents=result.cost_cents
                            )
                             prompt_feedback = "; ".join(evaluation.feedback)
                             last_error_message = f"Quality Gate: {prompt_feedback}"
                             continue
                    
                    # Success
                    context[task.task_id] = asset
                    await self._execution_tracker.complete(
                        exec_record.id,
                        ExecutionStatus.SUCCESS,
                        asset_id=asset.id,
                        latency_ms=result.latency_ms,
                        cost_estimate_cents=result.cost_cents
                    )
                    provider_success = True
                    break # Break retry loop
                    
                except Exception as e:
                    logger.exception("Provider exception: %s", e)
                    last_error_message = str(e)
                    await self._execution_tracker.complete(
                        exec_record.id, ExecutionStatus.FAILED, error_message=str(e)
                    )

                finally:
                    # RECORD OUTCOME (Learning)
                    try:
                        # Re-calculate success for record
                        final_success = provider_success
                        
                        # Latency calc (assuming started_at is datetime)
                        latency = 0.0
                        if exec_record.started_at:
                            delta = datetime.now(exec_record.started_at.tzinfo) - exec_record.started_at
                            latency = delta.total_seconds() * 1000

                        outcome = MultimodalOutcome(
                            plan_id=str(plan.id),
                            task_id=task.task_id,
                            step_type=task.step_type.value,
                            provider=provider.name if provider else "unknown",
                            model=decision.model or "default",
                            success=final_success,
                            latency_ms=latency,
                            cost_cents=result.cost_cents if result and result.cost_cents else 0.0,
                            quality_score=evaluation.overall_score if gate_config.get("enabled", True) else None,
                            feedback=prompt_feedback if is_retry else None
                        )
                        # Avoid blocking
                        await self._soma_brain_client.record_outcome(outcome)
                    except Exception as ex:
                        logger.warning(f"Failed to record outcome: {ex}")
            
            # End of Retry Loop
            if provider_success:
                return True, None
            else:
                # This provider failed all attempts. Add to excluded list and Fallback.
                logger.warning(
                    "Provider %s failed all attempts for step %s. Falling back.", 
                    decision.provider, task.task_id
                )
                failed_providers.append((decision.tool_id, decision.provider))
                # Continue outer loop -> Select new provider


    def _select_provider(self, task: TaskStep) -> Optional[MultimodalProvider]:
        """Select appropriate provider for task by iterating registered capabilities.
        
        Uses the capability map built during provider registration to find
        all providers that can handle the required task type.
        """
        # Determine required capability from step type
        required_capability = self._step_type_to_capability(task.step_type)
        if not required_capability:
            logger.warning("No capability mapping for step type: %s", task.step_type)
            return None
            
        # Get all providers that support this capability
        provider_names = self._capability_map.get(required_capability, [])
        if not provider_names:
            logger.warning("No providers registered for capability: %s", required_capability)
            return None
            
        # Build candidates from registered providers
        candidates = []
        for name in provider_names:
            provider = self._providers.get(name)
            if provider:
                # Use provider's advertised model or 'default'
                model = getattr(provider, 'default_model', 'default')
                candidates.append((name, model))
        
        if not candidates:
            return None
            
        # Optimization: Single candidate? Skip ranking
        if len(candidates) == 1:
            return self._providers.get(candidates[0][0])
            
        # Use Ranker for multiple candidates
        ranked = self._portfolio_ranker.rank_providers(
            candidates, 
            task.step_type.value
        )
        
        if not ranked:
            return None
            
        best_provider_name, _ = ranked[0]
        return self._providers.get(best_provider_name)
    
    def _step_type_to_capability(self, step_type: StepType) -> Optional[ProviderCapability]:
        """Map step type to provider capability."""
        mapping = {
            StepType.GENERATE_DIAGRAM: ProviderCapability.DIAGRAM,
            StepType.GENERATE_IMAGE: ProviderCapability.IMAGE,
            StepType.CAPTURE_SCREENSHOT: ProviderCapability.SCREENSHOT,
        }
        return mapping.get(step_type)

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

    def _map_step_type_to_modality(self, step_type: StepType) -> str:
        """Map step type to router modality keys."""
        if step_type == StepType.GENERATE_DIAGRAM:
            return "image_diagram"
        if step_type == StepType.GENERATE_IMAGE:
            return "image_photo" # Default strict
        if step_type == StepType.CAPTURE_SCREENSHOT:
            return "screenshot"
        return "image" # Fallback
