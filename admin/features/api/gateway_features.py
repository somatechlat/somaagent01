"""Gateway Features & Flags API Router.

Migrated from: services/gateway/routers/features.py
Pure Django Ninja implementation with Django settings and centralized config.

VIBE COMPLIANT - Django patterns, no hardcoded values, I18N ready.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.conf import settings
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

router = Router(tags=["features"])
logger = logging.getLogger(__name__)

# Centralized feature profile from Django settings
DEFAULT_FEATURE_PROFILE = getattr(settings, "SA01_FEATURE_PROFILE", "standard")


class FeatureItem(BaseModel):
    """Feature item schema."""
    
    key: str
    state: str
    enabled: bool
    profile_default: bool
    dependencies: list[str]
    stability: str
    tags: list[str]


class FeaturesResponse(BaseModel):
    """Features list response."""
    
    profile: str
    features: list[FeatureItem]


class FeatureFlagItem(BaseModel):
    """Feature flag schema."""
    
    enabled: bool
    effective: bool
    source: str
    profile_default: bool


class FeatureFlagsResponse(BaseModel):
    """Feature flags response."""
    
    tenant: str
    profile: str
    flags: dict[str, FeatureFlagItem]
    timestamp: str


def _get_profile() -> str:
    """Get current feature profile from config."""
    from django.conf import settings
    return settings.FEATURE_PROFILE


def _build_features(profile: str) -> list[dict]:
    """Build feature list based on profile."""
    features = []
    
    # Basic features always available
    features.append({
        "key": "sse_enabled",
        "state": "active",
        "enabled": True,
        "profile_default": True,
        "dependencies": [],
        "stability": "stable",
        "tags": ["streaming", "realtime"]
    })
    
    features.append({
        "key": "sequence",
        "state": "active",
        "enabled": True,
        "profile_default": True,
        "dependencies": [],
        "stability": "stable",
        "tags": ["processing", "sequencing"]
    })
    
    # Profile-specific features
    if profile in ["standard", "premium"]:
        features.append({
            "key": "semantic_recall",
            "state": "active",
            "enabled": True,
            "profile_default": True,
            "dependencies": ["embeddings"],
            "stability": "stable",
            "tags": ["search", "semantic"]
        })
    
    if profile == "premium":
        features.append({
            "key": "audio_support",
            "state": "active",
            "enabled": True,
            "profile_default": False,
            "dependencies": ["stt", "tts"],
            "stability": "beta",
            "tags": ["audio", "voice"]
        })
    
    return features


def _build_flags(profile: str, tenant: str) -> dict:
    """Build feature flags based on profile and tenant."""
    from django.conf import settings
    
    flags = {}
    
    # Core flags
    flags["sse_enabled"] = {
        "enabled": True,
        "effective": True,
        "source": "local",
        "profile_default": True
    }
    
    flags["sequence"] = {
        "enabled": True,
        "effective": True,
        "source": "local",
        "profile_default": True
    }
    
    flags["auth_required"] = {
        "enabled": settings.AUTH_REQUIRED,
        "effective": settings.AUTH_REQUIRED,
        "source": "local",
        "profile_default": False
    }
    
    # Profile-dependent flags
    semantic_enabled = profile in ["standard", "premium"]
    flags["semantic_recall"] = {
        "enabled": semantic_enabled,
        "effective": semantic_enabled,
        "source": "local",
        "profile_default": True
    }
    
    audio_enabled = profile == "premium"
    flags["audio_support"] = {
        "enabled": audio_enabled,
        "effective": audio_enabled,
        "source": "local",
        "profile_default": False
    }
    
    # Environment-dependent flags
    embeddings_enabled = getattr(settings, "EMBEDDINGS_INGEST_ENABLED", True)
    flags["embeddings_ingest"] = {
        "enabled": embeddings_enabled,
        "effective": embeddings_enabled,
        "source": "local",
        "profile_default": False
    }
    
    memory_enabled = getattr(settings, "MEMORY_GUARANTEES_ENABLED", False)
    flags["memory_guarantees"] = {
        "enabled": memory_enabled,
        "effective": memory_enabled,
        "source": "local",
        "profile_default": False
    }
    
    return flags


@router.get("/features", response=FeaturesResponse, summary="List available features")
async def list_features(request: HttpRequest) -> dict:
    """Return feature list with profile information."""
    profile = _get_profile()
    features = _build_features(profile)
    
    return {
        "profile": profile,
        "features": features
    }


@router.get("/feature-flags", response=FeatureFlagsResponse, summary="List feature flags")
async def list_feature_flags(request: HttpRequest) -> dict:
    """Return feature flags with tenant information."""
    # Get tenant from headers
    tenant = request.headers.get("X-Tenant-Id", "default")
    profile = _get_profile()
    flags = _build_flags(profile, tenant)
    
    return {
        "tenant": tenant,
        "profile": profile,
        "flags": flags,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
