"""LLM Degradation Service - Automatic Failover.

Provides automatic LLM model switching when a provider is unavailable.
Tracks provider health and routes to fallback models.

VIBE COMPLIANT: Django patterns, no external frameworks.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMProviderStatus(Enum):
    """Status of an LLM provider."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class LLMProviderHealth:
    """Health status of an LLM provider."""
    provider: str
    model: str
    status: LLMProviderStatus = LLMProviderStatus.UNKNOWN
    last_check: float = 0.0
    last_success: float = 0.0
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    
    # Thresholds
    failure_threshold: int = 3  # Failures before marking unavailable
    recovery_threshold: int = 2  # Successes before marking healthy
    consecutive_successes: int = 0


@dataclass 
class LLMFallbackChain:
    """Fallback chain for LLM providers."""
    primary: str  # e.g., "openai/gpt-4o"
    fallbacks: List[str] = field(default_factory=list)  # e.g., ["anthropic/claude-3", "openrouter/qwen"]
    current_index: int = 0
    
    def get_current(self) -> str:
        """Get current active provider."""
        if self.current_index == 0:
            return self.primary
        return self.fallbacks[self.current_index - 1]
    
    def get_next_fallback(self) -> Optional[str]:
        """Get next fallback in chain."""
        if self.current_index >= len(self.fallbacks):
            return None
        self.current_index += 1
        return self.get_current()
    
    def reset_to_primary(self):
        """Reset to primary provider."""
        self.current_index = 0


class LLMDegradationService:
    """LLM Degradation Service with automatic failover.
    
    Monitors LLM providers and automatically switches to fallback
    models when a provider becomes unavailable.
    
    Usage:
        service = LLMDegradationService()
        await service.initialize()
        
        # Get the best available model
        model = await service.get_available_model("chat")
        
        # Report success/failure after calls
        await service.record_success("openai/gpt-4o", latency_ms=150)
        await service.record_failure("openai/gpt-4o", "Rate limit exceeded")
    """
    
    # Default fallback chains by use case
    DEFAULT_CHAINS: Dict[str, LLMFallbackChain] = {
        "chat": LLMFallbackChain(
            primary="openai/gpt-4o",
            fallbacks=["anthropic/claude-3-5-sonnet", "openrouter/qwen/qwen-2.5-72b-instruct"],
        ),
        "coding": LLMFallbackChain(
            primary="anthropic/claude-3-5-sonnet",
            fallbacks=["openai/gpt-4o", "openrouter/deepseek/deepseek-coder"],
        ),
        "fast": LLMFallbackChain(
            primary="openai/gpt-4o-mini",
            fallbacks=["anthropic/claude-3-haiku", "openrouter/meta-llama/llama-3.1-8b-instruct"],
        ),
        "embedding": LLMFallbackChain(
            primary="openai/text-embedding-3-small",
            fallbacks=["local/sentence-transformers"],
        ),
    }
    
    def __init__(self):
        self._provider_health: Dict[str, LLMProviderHealth] = {}
        self._fallback_chains: Dict[str, LLMFallbackChain] = {}
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._status_callbacks: List[Callable[[str, LLMProviderStatus], Awaitable[None]]] = []
        
    async def initialize(self):
        """Initialize the degradation service."""
        # Load configuration from Django settings or defaults
        chains_config = getattr(settings, "LLM_FALLBACK_CHAINS", None)
        
        if chains_config:
            for use_case, chain in chains_config.items():
                self._fallback_chains[use_case] = LLMFallbackChain(
                    primary=chain["primary"],
                    fallbacks=chain.get("fallbacks", []),
                )
        else:
            self._fallback_chains = self.DEFAULT_CHAINS.copy()
        
        # Initialize health tracking for all known providers
        all_providers = set()
        for chain in self._fallback_chains.values():
            all_providers.add(chain.primary)
            all_providers.update(chain.fallbacks)
        
        for provider in all_providers:
            parts = provider.split("/", 1)
            provider_name = parts[0]
            model_name = parts[1] if len(parts) > 1 else provider
            
            self._provider_health[provider] = LLMProviderHealth(
                provider=provider_name,
                model=model_name,
            )
        
        logger.info(f"LLM Degradation Service initialized with {len(self._fallback_chains)} chains")
    
    async def start_monitoring(self, check_interval: float = 60.0):
        """Start background health monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(check_interval))
        logger.info("LLM health monitoring started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("LLM health monitoring stopped")
    
    async def _monitor_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                await self._check_all_providers()
            except Exception as e:
                logger.error(f"LLM monitoring error: {e}")
            await asyncio.sleep(interval)
    
    async def _check_all_providers(self):
        """Check health of all known providers."""
        for provider_id, health in self._provider_health.items():
            try:
                await self._check_provider_health(provider_id)
            except Exception as e:
                logger.debug(f"Health check failed for {provider_id}: {e}")
    
    async def _check_provider_health(self, provider_id: str):
        """Check health of a specific provider with a lightweight call."""
        health = self._provider_health.get(provider_id)
        if not health:
            return
        
        start_time = time.time()
        
        try:
            # Attempt a minimal LLM call to verify connectivity
            # Uses lazy import to avoid circular dependencies
            from admin.llm.services.litellm_client import LiteLLMChatWrapper
            from langchain_core.messages import HumanMessage
            
            provider, model = provider_id.split("/", 1)
            wrapper = LiteLLMChatWrapper(model=model, provider=provider)
            
            # Minimal health check call
            response = wrapper._call(
                messages=[HumanMessage(content="ping")],
                max_tokens=1,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            await self.record_success(provider_id, latency_ms)
            
        except Exception as e:
            await self.record_failure(provider_id, str(e))
    
    async def record_success(self, provider_id: str, latency_ms: float = 0.0):
        """Record a successful LLM call."""
        health = self._provider_health.get(provider_id)
        if not health:
            return
        
        health.last_check = time.time()
        health.last_success = time.time()
        health.latency_ms = latency_ms
        health.consecutive_failures = 0
        health.consecutive_successes += 1
        health.last_error = None
        
        # Update error rate (exponential moving average)
        health.error_rate = health.error_rate * 0.9
        
        # Check if we should recover to healthy
        old_status = health.status
        if health.consecutive_successes >= health.recovery_threshold:
            health.status = LLMProviderStatus.HEALTHY
        elif health.status == LLMProviderStatus.UNAVAILABLE:
            health.status = LLMProviderStatus.DEGRADED
        
        # Notify if status changed
        if old_status != health.status:
            await self._notify_status_change(provider_id, health.status)
            logger.info(f"LLM provider {provider_id} recovered to {health.status.value}")
    
    async def record_failure(self, provider_id: str, error: str):
        """Record a failed LLM call."""
        health = self._provider_health.get(provider_id)
        if not health:
            return
        
        health.last_check = time.time()
        health.last_error = error
        health.consecutive_failures += 1
        health.consecutive_successes = 0
        
        # Update error rate (exponential moving average)
        health.error_rate = health.error_rate * 0.9 + 0.1
        
        # Check if we should mark as unavailable
        old_status = health.status
        if health.consecutive_failures >= health.failure_threshold:
            health.status = LLMProviderStatus.UNAVAILABLE
        elif health.consecutive_failures >= 1:
            health.status = LLMProviderStatus.DEGRADED
        
        # Notify if status changed
        if old_status != health.status:
            await self._notify_status_change(provider_id, health.status)
            logger.warning(f"LLM provider {provider_id} degraded to {health.status.value}: {error}")
    
    async def _notify_status_change(self, provider_id: str, status: LLMProviderStatus):
        """Notify callbacks of status change."""
        for callback in self._status_callbacks:
            try:
                await callback(provider_id, status)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def on_status_change(self, callback: Callable[[str, LLMProviderStatus], Awaitable[None]]):
        """Register a callback for status changes."""
        self._status_callbacks.append(callback)
    
    async def get_available_model(self, use_case: str = "chat") -> Optional[str]:
        """Get the best available model for a use case.
        
        Follows the fallback chain until a healthy provider is found.
        
        Args:
            use_case: The use case (chat, coding, fast, embedding)
            
        Returns:
            Model ID string (e.g., "openai/gpt-4o") or None if all unavailable
        """
        chain = self._fallback_chains.get(use_case)
        if not chain:
            chain = self._fallback_chains.get("chat")
        
        if not chain:
            return None
        
        # Check primary
        primary_health = self._provider_health.get(chain.primary)
        if primary_health and primary_health.status != LLMProviderStatus.UNAVAILABLE:
            return chain.primary
        
        # Check fallbacks
        for fallback in chain.fallbacks:
            fallback_health = self._provider_health.get(fallback)
            if fallback_health and fallback_health.status != LLMProviderStatus.UNAVAILABLE:
                return fallback
        
        # All unavailable - return primary anyway (let caller handle error)
        logger.error(f"All LLM providers unavailable for {use_case}, returning primary as last resort")
        return chain.primary
    
    def get_provider_status(self, provider_id: str) -> LLMProviderStatus:
        """Get current status of a provider."""
        health = self._provider_health.get(provider_id)
        if not health:
            return LLMProviderStatus.UNKNOWN
        return health.status
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        return {
            provider_id: {
                "status": health.status.value,
                "last_check": health.last_check,
                "last_success": health.last_success,
                "last_error": health.last_error,
                "consecutive_failures": health.consecutive_failures,
                "latency_ms": health.latency_ms,
                "error_rate": health.error_rate,
            }
            for provider_id, health in self._provider_health.items()
        }
    
    def is_degraded(self) -> bool:
        """Check if any provider in primary chains is degraded."""
        for chain in self._fallback_chains.values():
            primary_health = self._provider_health.get(chain.primary)
            if primary_health and primary_health.status != LLMProviderStatus.HEALTHY:
                return True
        return False
    
    def get_degradation_summary(self) -> Dict[str, Any]:
        """Get summary of LLM degradation status."""
        healthy = []
        degraded = []
        unavailable = []
        
        for provider_id, health in self._provider_health.items():
            if health.status == LLMProviderStatus.HEALTHY:
                healthy.append(provider_id)
            elif health.status == LLMProviderStatus.DEGRADED:
                degraded.append(provider_id)
            elif health.status == LLMProviderStatus.UNAVAILABLE:
                unavailable.append(provider_id)
        
        return {
            "is_degraded": self.is_degraded(),
            "healthy_providers": healthy,
            "degraded_providers": degraded,
            "unavailable_providers": unavailable,
            "active_fallbacks": [
                {
                    "use_case": use_case,
                    "active_model": chain.get_current(),
                    "is_fallback": chain.current_index > 0,
                }
                for use_case, chain in self._fallback_chains.items()
            ],
        }


# Global singleton instance
llm_degradation_service = LLMDegradationService()


async def get_llm_with_fallback(use_case: str = "chat", **kwargs) -> Any:
    """Get an LLM instance with automatic fallback.
    
    Convenience function that returns a ready-to-use LLM wrapper.
    
    Args:
        use_case: The use case (chat, coding, fast, embedding)
        **kwargs: Additional arguments for the LLM wrapper
        
    Returns:
        LiteLLMChatWrapper instance configured with the best available model
    """
    from admin.llm.services.litellm_client import LiteLLMChatWrapper
    
    # Initialize if needed
    if not llm_degradation_service._provider_health:
        await llm_degradation_service.initialize()
    
    # Get available model
    model_id = await llm_degradation_service.get_available_model(use_case)
    if not model_id:
        raise RuntimeError(f"No LLM available for use case: {use_case}")
    
    # Parse provider/model
    parts = model_id.split("/", 1)
    provider = parts[0]
    model = parts[1] if len(parts) > 1 else model_id
    
    return LiteLLMChatWrapper(model=model, provider=provider, **kwargs)
