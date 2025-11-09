import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

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
        # Env override (migration compatibility)
        if desc.enabled_env_var:
            raw = os.getenv(desc.enabled_env_var)
            if raw is not None:
                if raw.lower() in {"1", "true", "yes", "on"}:
                    self._state_cache[key] = "on"
                    return "on"
                else:
                    self._state_cache[key] = "disabled"
                    return "disabled"
        # Profile default
        enabled = desc.profiles.get(self._profile, desc.default_enabled)
        # Dependencies: if any dependency disabled, mark disabled
        for dep in desc.dependencies:
            if self.state(dep) == "disabled":
                self._state_cache[key] = "disabled"
                return "disabled"
        self._state_cache[key] = "on" if enabled else "disabled"
        return self._state_cache[key]


def build_default_registry() -> FeatureRegistry:
    profile = os.getenv("SA01_FEATURE_PROFILE", "enhanced").lower()
    if profile not in {"minimal", "standard", "enhanced", "max"}:
        profile = "enhanced"

    descriptors = [
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
            enabled_env_var="ENABLE_EMBED_ON_INGEST",
            stability="beta",
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
    ]

    return FeatureRegistry(descriptors=descriptors, profile=profile) 
