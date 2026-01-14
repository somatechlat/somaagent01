"""Multimodal Executor service.

Orchestrates the execution of multimodal job plans. Manages dependencies,
selects appropriate providers, executes tasks, stores assets, and tracks progress.

SRS Reference: Section 16.6 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from services.common.asset_critic import AssetCritic, AssetRubric
from services.common.asset_store import AssetStore, AssetType
from services.common.execution_tracker import ExecutionStatus, ExecutionTracker
from services.common.job_planner import JobPlan, JobPlanner, JobStatus, StepType, TaskStep
from services.common.policy_graph_router import PolicyGraphRouter
from services.common.portfolio_ranker import PortfolioRanker
from services.common.provenance_recorder import ProvenanceRecorder
from services.common.soma_brain_outcomes import SomaBrainOutcomesStore
from services.multimodal.base_provider import (
    GenerationRequest,
    MultimodalProvider,
    ProviderCapability,
)
from services.multimodal.dalle_provider import DalleProvider
from services.multimodal.mermaid_provider import MermaidProvider
from services.multimodal.playwright_provider import PlaywrightProvider

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
        soma_brain_client: Optional[SomaBrainOutcomesStore] = None,
        policy_router: Optional[PolicyGraphRouter] = None,
    ) -> None:
        """Initialize executor with services.

        Args:
            dsn: Database connection string
            asset_store: AssetStore instance
            job_planner: JobPlanner instance
            execution_tracker: ExecutionTracker instance
            asset_critic: AssetCritic instance for quality gating
            soma_brain_client: SomaBrainOutcomesStore instance for learning
            policy_router: PolicyGraphRouter instance for provider selection
        """
        self._dsn = dsn or os.environ.get("SA01_DB_DSN", "")
        self._asset_store = asset_store or AssetStore(dsn=self._dsn)
        self._job_planner = job_planner or JobPlanner(dsn=self._dsn)
        self._execution_tracker = execution_tracker or ExecutionTracker(dsn=self._dsn)
        self._soma_brain_client = soma_brain_client or SomaBrainOutcomesStore()
        self._portfolio_ranker = PortfolioRanker(self._soma_brain_client)
        self._policy_router = policy_router or PolicyGraphRouter(dsn=self._dsn)
        self._provenance_recorder = ProvenanceRecorder(dsn=self._dsn)
        self._initialized = False

        # Initialize LLM Adapter for AssetCritic if needed
        # In a real app, we might inject this from a factory or globals
        from services.common.llm_adapter import LLMAdapter
        from services.common.secret_manager import SecretManager

        # Prefer per-call secret retrieval to avoid stale keys.
        sm = SecretManager()

        def api_key_resolver():
            return sm.get("provider:openai")  # returns awaitable

        self._llm_adapter = LLMAdapter(api_key_resolver=api_key_resolver)

        self._asset_critic = asset_critic or AssetCritic(llm_adapter=self._llm_adapter)

        # Initialize providers registry
        self._providers: Dict[str, MultimodalProvider] = {}
        self._capability_map: Dict[ProviderCapability, List[str]] = {}

    async def initialize(self) -> None:
        """Initialize providers and verify dependencies."""
        if self._initialized:
            return

        # Ensure schemas exist before execution
        await self._asset_store.ensure_schema()
        await self._job_planner.ensure_schema()
        await self._execution_tracker.ensure_schema()
        await self._provenance_recorder.ensure_schema()
        await self._policy_router.ensure_schema()

        # Register default providers
        await self.register_provider(MermaidProvider())
        await self.register_provider(PlaywrightProvider())

        # Only register DALL-E if API key is present
        dalle = DalleProvider()
        if await dalle.health_check():
            await self.register_provider(dalle)
        else:
            logger.warning("DALL-E provider not available (missing API key?)")

        self._initialized = True

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

    async def run_pending(self, poll_interval: float = 2.0) -> None:
        """Continuously execute pending multimodal job plans.

        This loop claims pending plans atomically to avoid duplicate execution
        across multiple workers.
        """
        await self.initialize()
        while True:
            try:
                plan = await self._job_planner.claim_next_pending()
                if not plan:
                    await asyncio.sleep(poll_interval)
                    continue

                await self.execute_plan(plan.id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Multimodal job loop error: %s", exc)
                await asyncio.sleep(poll_interval)

    async def execute_plan(self, plan_id: UUID) -> bool:
        """Execute a full job plan.

        Args:
            plan_id: UUID of plan to execute

        Returns:
            True if execution completed successfully
        """
        await self.initialize()
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
        budget_used_cents = plan.budget_used_cents or 0

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
                success, step_error, step_cost = await self._execute_step(plan, i, task, context)
                if not success:
                    failed = True
                    # Check if failure was due to quality gate exhaustion
                    error_msg = step_error or f"Step {task.task_id} failed after max attempts"
                    break

                if step_cost:
                    budget_used_cents += step_cost
                    plan.budget_used_cents = budget_used_cents
                    if (
                        plan.budget_limit_cents is not None
                        and budget_used_cents > plan.budget_limit_cents
                    ):
                        failed = True
                        error_msg = f"budget_exceeded: used {budget_used_cents} > limit {plan.budget_limit_cents}"
                        break

                # Update progress
                await self._job_planner.update_status(
                    plan.id,
                    JobStatus.RUNNING,
                    completed_steps=i + 1,
                    budget_used_cents=budget_used_cents,
                )

            # Final status update
            status = JobStatus.FAILED if failed else JobStatus.COMPLETED
            await self._job_planner.update_status(
                plan.id,
                status,
                error_message=error_msg,
                budget_used_cents=budget_used_cents,
            )
            return not failed

        except Exception as exc:
            logger.exception("Plan execution failed: %s", exc)
            await self._job_planner.update_status(
                plan.id,
                JobStatus.FAILED,
                error_message=str(exc),
                budget_used_cents=budget_used_cents,
            )
            return False

    async def _execute_step(
        self,
        plan: JobPlan,
        step_index: int,
        task: TaskStep,
        context: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """Execute a single task step with rework/retry loop.

        Returns:
            Tuple of (success, error_message, cost_cents_used)
        """
        step_cost_cents = 0
        budget_used_cents = plan.budget_used_cents or 0
        budget_limit_cents = plan.budget_limit_cents
        decision = await self._policy_router.route(
            modality=self._map_step_type_to_modality(task.step_type),
            tenant_id=plan.tenant_id,
            budget_limit_cents=budget_limit_cents,
            budget_used_cents=budget_used_cents,
            context={"intent": task.step_type.value},
        )

        # --- SHADOW MODE RANKING ---
        try:
            shadow_candidates: List[Tuple[str, str]] = []
            if decision.provider:
                shadow_candidates.append((decision.provider, "default"))

            ranked = await self._portfolio_ranker.rank(
                shadow_candidates,
                task.step_type.value,
            )
            if ranked and decision.success and decision.provider:
                top_pick_id = ranked[0][0]
                if top_pick_id != decision.provider:
                    logger.info(
                        "SHADOW DIVERGENCE: Policy=%s, Ranker=%s",
                        decision.provider,
                        top_pick_id,
                    )
        except Exception as e:
            logger.warning("Shadow ranking failed: %s", e)
        # ---------------------------

        if not decision.success or not decision.tool_id:
            error_msg = "No capability available."
            logger.error("Step %s failed: %s", task.task_id, error_msg)
            await self._execution_tracker.start(
                plan.id, step_index, plan.tenant_id, "unknown", "unknown"
            )
            return False, error_msg, step_cost_cents

        provider = self._providers.get(decision.tool_id)
        if not provider:
            error_msg = f"Provider {decision.tool_id} not loaded in executor"
            logger.error(error_msg)
            return False, error_msg, step_cost_cents

        logger.info(
            "Step %s selected provider %s (tool: %s)",
            task.task_id,
            decision.provider,
            decision.tool_id,
        )

        max_attempts = 1
        gate_config = task.quality_gate
        if gate_config.get("enabled", True):
            max_attempts = gate_config.get("max_reworks", 2) + 1

        attempt = 0
        prompt_feedback = ""
        provider_success = False
        last_error_message: Optional[str] = None

        while attempt < max_attempts:
            attempt += 1
            is_retry = attempt > 1
            result = None
            evaluation_score = None
            evaluation_feedback: Dict[str, Any] | None = None
            quality_gate_passed = None
            asset = None
            error_code = None
            error_message = None
            exec_status = ExecutionStatus.FAILED

            base_prompt = self._resolve_dependencies(task.params.get("prompt", ""), context)
            if is_retry and prompt_feedback:
                full_prompt = f"{base_prompt}\n\nCRITIC FEEDBACK: {prompt_feedback}"
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
                if result and result.cost_cents:
                    step_cost_cents += int(result.cost_cents)

                if not result or not result.success:
                    logger.warning(
                        "Step %s provider %s attempt %d failure: %s",
                        task.task_id,
                        provider.name,
                        attempt,
                        result.error_message if result else "no_result",
                    )
                    error_code = result.error_code if result else "provider_error"
                    error_message = result.error_message if result else "provider_error"
                    last_error_message = error_message
                    prompt_feedback = f"Provider error: {error_message}"
                else:
                    asset_type = AssetType.IMAGE
                    if (
                        task.step_type == StepType.CAPTURE_SCREENSHOT
                        or task.modality == "screenshot"
                    ):
                        asset_type = AssetType.SCREENSHOT
                    elif task.step_type == StepType.GENERATE_DIAGRAM or task.modality in {
                        "diagram",
                        "image_diagram",
                    }:
                        asset_type = AssetType.DIAGRAM
                    elif task.step_type == StepType.GENERATE_VIDEO or task.modality.startswith(
                        "video"
                    ):
                        asset_type = AssetType.VIDEO
                    elif task.step_type == StepType.COMPOSE_DOCUMENT or task.modality == "document":
                        asset_type = AssetType.DOCUMENT

                    if result.content_type:
                        lowered = result.content_type.lower()
                        if "svg" in lowered:
                            asset_type = AssetType.DIAGRAM
                        elif "pdf" in lowered:
                            asset_type = AssetType.DOCUMENT

                    result_format = (result.format or task.params.get("format") or "png").lower()
                    asset = await self._asset_store.create(
                        tenant_id=plan.tenant_id,
                        session_id=plan.session_id,
                        asset_type=asset_type,
                        format=result_format,
                        content=result.content,
                        dimensions=result.dimensions,
                        metadata={
                            "plan_id": str(plan.id),
                            "task_id": task.task_id,
                            "provider": provider.name,
                            "attempt": attempt,
                        },
                    )

                    if gate_config.get("enabled", True):
                        if task.step_type == StepType.GENERATE_DIAGRAM:
                            rubric = AssetRubric.technical_diagram()
                        else:
                            rubric = AssetRubric.default_image()

                        if task.constraints.get("min_width"):
                            rubric.min_width = task.constraints.get("min_width")

                        evaluation = await self._asset_critic.evaluate(
                            asset, rubric, context=context
                        )
                        quality_gate_passed = evaluation.passed
                        evaluation_score = evaluation.score
                        evaluation_feedback = {
                            "feedback": evaluation.feedback,
                            "failed_criteria": evaluation.failed_criteria,
                        }

                        if not evaluation.passed:
                            logger.warning(
                                "Step %s provider %s validation failed: %s",
                                task.task_id,
                                provider.name,
                                evaluation.failed_criteria,
                            )
                            error_code = "QUALITY_GATE_FAILED"
                            error_message = str(evaluation.failed_criteria)
                            prompt_feedback = "; ".join(evaluation.feedback)
                            last_error_message = f"Quality Gate: {prompt_feedback}"

                            try:
                                await self._provenance_recorder.record(
                                    asset_id=asset.id,
                                    tenant_id=plan.tenant_id,
                                    tool_id=provider.name,
                                    provider=provider.provider_id,
                                    request_id=plan.request_id,
                                    execution_id=exec_record.id,
                                    plan_id=plan.id,
                                    session_id=plan.session_id,
                                    user_id=plan.user_id,
                                    prompt_summary=plan.prompt,
                                    generation_params=task.params,
                                    quality_gate_passed=False,
                                    quality_score=evaluation_score,
                                    rework_count=attempt,
                                )
                            except Exception as exc:
                                logger.debug("Failed to record provenance", exc_info=exc)
                        else:
                            try:
                                await self._provenance_recorder.record(
                                    asset_id=asset.id,
                                    tenant_id=plan.tenant_id,
                                    tool_id=provider.name,
                                    provider=provider.provider_id,
                                    request_id=plan.request_id,
                                    execution_id=exec_record.id,
                                    plan_id=plan.id,
                                    session_id=plan.session_id,
                                    prompt_summary=full_prompt,
                                    generation_params=request.parameters,
                                    model_version=result.model_version,
                                    quality_gate_passed=quality_gate_passed,
                                    quality_score=evaluation_score,
                                    rework_count=attempt - 1,
                                )
                            except Exception as exc:
                                logger.warning("Failed to record provenance: %s", exc)

                            context[task.task_id] = asset
                            exec_status = ExecutionStatus.SUCCESS
                    else:
                        context[task.task_id] = asset
                        exec_status = ExecutionStatus.SUCCESS

            except Exception as e:
                logger.exception("Provider exception: %s", e)
                last_error_message = str(e)
                error_message = last_error_message

            finally:
                try:
                    latency = 0.0
                    if exec_record.started_at:
                        delta = datetime.now(exec_record.started_at.tzinfo) - exec_record.started_at
                        latency = delta.total_seconds() * 1000
                    await self._execution_tracker.complete(
                        exec_record.id,
                        exec_status,
                        asset_id=asset.id if asset else None,
                        latency_ms=latency,
                        cost_estimate_cents=result.cost_cents if result else None,
                        quality_score=evaluation_score,
                        quality_feedback=evaluation_feedback,
                        error_code=error_code,
                        error_message=error_message,
                    )
                except Exception as ex:
                    logger.warning("Failed to record outcome: %s", ex)

            if exec_status == ExecutionStatus.SUCCESS:
                provider_success = True
                break

            last_error_message = error_message or last_error_message
            if attempt < max_attempts:
                continue
            break

        if provider_success:
            return True, None, step_cost_cents
        return False, prompt_feedback or last_error_message or "provider_failure", step_cost_cents

    def _resolve_dependencies(self, prompt: str, context: Dict[str, Any]) -> str:
        """Resolve dependency tokens in prompt.

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
            return "image_photo"
        if step_type == StepType.CAPTURE_SCREENSHOT:
            return "screenshot"
        if step_type == StepType.GENERATE_VIDEO:
            return "video_short"
        if step_type == StepType.COMPOSE_DOCUMENT:
            return "document"
        raise ValueError(f"Unsupported step type: {step_type}")
