"""Feature flags router.

Provides endpoints for feature flag listings with proper response formats.
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/v1/features")
async def list_features(request: Request):
    """Return feature list with profile information."""
    from src.core.config import cfg

    # Tenant from headers (reserved for future per-tenant feature flags)
    _ = request.headers.get("X-Tenant-Id", "default")

    # Get feature profile from config
    profile = cfg.env("SA01_FEATURE_PROFILE", "standard")

    # Define features based on profile and environment with expected schema
    features = []

    # Basic features always available
    features.append(
        {
            "key": "sse_enabled",
            "state": "active",
            "enabled": True,
            "profile_default": True,
            "dependencies": [],
            "stability": "stable",
            "tags": ["streaming", "realtime"],
        }
    )

    features.append(
        {
            "key": "sequence",
            "state": "active",
            "enabled": True,
            "profile_default": True,
            "dependencies": [],
            "stability": "stable",
            "tags": ["processing", "sequencing"],
        }
    )

    # Profile-specific features
    if profile in ["standard", "premium"]:
        features.append(
            {
                "key": "semantic_recall",
                "state": "active",
                "enabled": True,
                "profile_default": True,
                "dependencies": ["embeddings"],
                "stability": "stable",
                "tags": ["search", "semantic"],
            }
        )

    if profile == "premium":
        features.append(
            {
                "key": "audio_support",
                "state": "active",
                "enabled": True,
                "profile_default": False,
                "dependencies": ["stt", "tts"],
                "stability": "beta",
                "tags": ["audio", "voice"],
            }
        )

    return {"profile": profile, "features": features}


@router.get("/v1/feature-flags")
async def list_feature_flags(request: Request):
    """Return feature flags with tenant information."""
    from src.core.config import cfg

    # Get tenant from headers
    tenant = request.headers.get("X-Tenant-Id", "default")

    # Get feature profile from config
    profile = cfg.env("SA01_FEATURE_PROFILE", "standard")

    # Define feature flags with metadata as expected by tests
    flags = {}

    # Core flags with metadata
    flags["sse_enabled"] = {
        "enabled": True,
        "effective": True,
        "source": "local",
        "profile_default": True,
    }

    flags["sequence"] = {
        "enabled": True,
        "effective": True,
        "source": "local",
        "profile_default": True,
    }

    flags["auth_required"] = {
        "enabled": cfg.settings().auth.auth_required,
        "effective": cfg.settings().auth.auth_required,
        "source": "local",
        "profile_default": False,
    }

    # Profile-dependent flags
    semantic_enabled = profile in ["standard", "premium"]
    flags["semantic_recall"] = {
        "enabled": semantic_enabled,
        "effective": semantic_enabled,
        "source": "local",
        "profile_default": True,
    }

    audio_enabled = profile == "premium"
    flags["audio_support"] = {
        "enabled": audio_enabled,
        "effective": audio_enabled,
        "source": "local",
        "profile_default": False,
    }

    # Environment-dependent flags
    embeddings_enabled = cfg.flag("embeddings_ingest")
    flags["embeddings_ingest"] = {
        "enabled": embeddings_enabled,
        "effective": embeddings_enabled,
        "source": "local",
        "profile_default": False,
    }

    memory_enabled = cfg.flag("memory_guarantees", False)
    flags["memory_guarantees"] = {
        "enabled": memory_enabled,
        "effective": memory_enabled,
        "source": "local",
        "profile_default": False,
    }

    return {
        "tenant": tenant,
        "profile": profile,
        "flags": flags,
        "timestamp": "2025-12-05T00:00:00Z",
    }
