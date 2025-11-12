import os
from services.common import runtime_config as cfg
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Profile = Literal["minimal", "standard", "enhanced", "max"]
State = Literal["on", "degraded", "disabled"]


@dataclass(frozen=True)
class FeatureDescriptor:
    key: str
    description: str
    default_enabled: bool
    profiles: Dict[Profile, bool]
    dependencies: List[str] = field(default_factory=list)
    degrade_strategy: Literal["auto", "manual", "none"] = "auto"
    cost_impact: Literal["low", "medium", "high"] = "low"
    metrics_key: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    enabled_env_var: Optional[str] = None
    stability: Literal["stable", "beta", "experimental"] = "stable"


class FeatureRegistry:
    def __init__(self, descriptors: List[FeatureDescriptor], profile: Profile = "enhanced"):
        self._descriptors: Dict[str, FeatureDescriptor] = {d.key: d for d in descriptors}
        self._profile: Profile = profile
        self._state_cache: Dict[str, State] = {}

    @property
    def profile(self) -> Profile:
        return self._profile

    def describe(self) -> List[FeatureDescriptor]:
        return list(self._descriptors.values())

    def is_enabled(self, key: str) -> bool:
        return self.state(key) == "on" or self.state(key) == "degraded"

    def state(self, key: str) -> State:
        if key in self._state_cache:
            return self._state_cache[key]
        desc = self._descriptors[key]
        # Profile default
        enabled = desc.profiles.get(self._profile, desc.default_enabled)
        # Honor explicit environment override variables when provided.
        # This is not a prior path; tests and ops rely on fast env flips.
        try:
            if desc.enabled_env_var:
                raw = cfg.env(desc.enabled_env_var)
                if raw != "":
                    val = str(raw).lower() in {"1", "true", "yes", "on"}
                    enabled = bool(val)
        except Exception:
            pass
        # Dependencies: if any dependency disabled, mark disabled
        for dep in desc.dependencies:
            if self.state(dep) == "disabled":
                self._state_cache[key] = "disabled"
                return "disabled"
        self._state_cache[key] = "on" if enabled else "disabled"
        return self._state_cache[key]


def build_default_registry() -> FeatureRegistry:
    # Use the central runtime_config.env helper for consistency.
    profile = cfg.env("SA01_FEATURE_PROFILE", "enhanced").lower()
    if profile not in {"minimal", "standard", "enhanced", "max"}:
        profile = "enhanced"

    descriptors = [
        FeatureDescriptor(
            key="sse_enabled",
            description="Enable Server-Sent Events endpoints for streaming",
            default_enabled=True,
            profiles={"minimal": True, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="none",
            cost_impact="low",
            metrics_key="sse.enabled",
            tags=["streaming", "ui"],
            enabled_env_var="SA01_SSE_ENABLED",
            stability="stable",
        ),
        FeatureDescriptor(
            key="embeddings_ingest",
            description="Generate vector embeddings for messages and tool outputs",
            default_enabled=True,
            profiles={"minimal": False, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="auto",
            cost_impact="medium",
            metrics_key="embeddings_ingest",
            tags=["performance", "memory"],
            enabled_env_var="SA01_ENABLE_EMBEDDINGS_INGEST",
            stability="beta",
        ),
        FeatureDescriptor(
            key="learning_context",
            description="Enable Somabrain learning weights/context + reward",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            metrics_key="learning_context",
            tags=["learning"],
            stability="beta",
        ),
        FeatureDescriptor(
            key="sequence",
            description="Enable sequence orchestration features",
            default_enabled=True,
            profiles={"minimal": True, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="none",
            cost_impact="low",
            metrics_key="sequence",
            tags=["core"],
            stability="stable",
        ),
        FeatureDescriptor(
            key="semantic_recall",
            description="Vector similarity recall for contextual memory injection",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": False, "max": True},
            dependencies=["embeddings_ingest"],
            degrade_strategy="auto",
            cost_impact="high",
            metrics_key="semantic_recall",
            tags=["beta", "memory"],
            stability="experimental",
        ),
        FeatureDescriptor(
            key="tool_events",
            description="Emit tool call/result events to SSE stream",
            default_enabled=False,
            profiles={"minimal": False, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            metrics_key="tool_events",
            tags=["observability"],
            enabled_env_var="SA01_ENABLE_TOOL_EVENTS",
            stability="stable",
        ),
        FeatureDescriptor(
            key="content_masking",
            description="Mask sensitive content in responses and logs",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            metrics_key="content_masking",
            tags=["security"],
            enabled_env_var="SA01_ENABLE_CONTENT_MASKING",
            stability="stable",
        ),
        FeatureDescriptor(
            key="token_metrics",
            description="Collect token usage metrics per request",
            default_enabled=True,
            profiles={"minimal": True, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="none",
            cost_impact="low",
            metrics_key="token_metrics",
            tags=["observability"],
            enabled_env_var="SA01_ENABLE_TOKEN_METRICS",
            stability="stable",
        ),
        FeatureDescriptor(
            key="error_classifier",
            description="Classify gateway/provider errors for analytics",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            metrics_key="error_classifier",
            tags=["observability"],
            enabled_env_var="SA01_ENABLE_ERROR_CLASSIFIER",
            stability="beta",
        ),
        FeatureDescriptor(
            key="reasoning_stream",
            description="Stream reasoning events for UI thought bubbles",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            metrics_key="reasoning_stream",
            tags=["ui"],
            enabled_env_var="SA01_ENABLE_REASONING_STREAM",
            stability="beta",
        ),
        FeatureDescriptor(
            key="conversation_policy_bypass",
            description="Allow conversation policy bypass in LOCAL/dev mode for rapid iteration",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": False, "max": False},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="low",
            tags=["dev", "policy"],
            stability="experimental",
        ),
        # ------------------------------------------------------------------
        # Newly centralized service flags (deployment/profile aware)
        # ------------------------------------------------------------------
        FeatureDescriptor(
            key="escalation",
            description="Enable escalation LLM path for high-complexity queries",
            default_enabled=True,
            profiles={"minimal": False, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="medium",
            tags=["llm", "routing"],
            enabled_env_var="SA01_ENABLE_ESCALATION",
            stability="beta",
        ),
        FeatureDescriptor(
            key="escalation_fallback",
            description="Enable fallback escalation path when primary escalation fails",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": False, "max": True},
            dependencies=["escalation"],
            degrade_strategy="auto",
            cost_impact="low",
            tags=["llm", "routing"],
            enabled_env_var="SA01_ENABLE_ESCALATION_FALLBACK",
            stability="experimental",
        ),
        FeatureDescriptor(
            key="file_saving_disabled",
            description="Disable on-disk file saving in gateway (security hardening)",
            default_enabled=True,
            profiles={"minimal": True, "standard": True, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="none",
            cost_impact="low",
            tags=["security"],
            enabled_env_var="SA01_FILE_SAVING_DISABLED",
            stability="stable",
        ),
        FeatureDescriptor(
            key="audio_support",
            description="Enable Whisper audio transcription features",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": True, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="high",
            tags=["audio"],
            enabled_env_var="SA01_ENABLE_AUDIO",
            stability="experimental",
        ),
        FeatureDescriptor(
            key="browser_support",
            description="Enable browser automation (browser-use) features",
            default_enabled=False,
            profiles={"minimal": False, "standard": False, "enhanced": False, "max": True},
            dependencies=[],
            degrade_strategy="manual",
            cost_impact="high",
            tags=["automation"],
            enabled_env_var="SA01_ENABLE_BROWSER",
            stability="experimental",
        ),
    ]

    return FeatureRegistry(descriptors=descriptors, profile=profile)
