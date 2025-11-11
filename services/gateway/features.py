"""Features router: centralized endpoints for feature profiles and flags.

Provides:
- GET /v1/features: read-only profile + per-feature state snapshot
- GET /v1/feature-flags: merged view of local vs remote (tenant-aware) flags with caching
"""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram

from observability.metrics import metrics_collector
from services.common import runtime_config as cfg

router = APIRouter()


@router.get("/v1/features")
async def get_features() -> JSONResponse:
    """Return feature profile and per-feature states.

    Provides a stable JSON surface for UI diagnostics and automation. Uses the
    central FeatureRegistry; falls back gracefully if unavailable.
    """
    try:
        from services.common.features import build_default_registry

        reg = build_default_registry()
        metrics_collector.update_feature_metrics()
        items = []
        for d in reg.describe():
            items.append(
                {
                    "key": d.key,
                    "state": reg.state(d.key),
                    "enabled": reg.is_enabled(d.key),
                    "profile_default": d.profiles.get(reg.profile, d.default_enabled),
                    "dependencies": d.dependencies,
                    "stability": d.stability,
                    "tags": d.tags,
                }
            )
        return JSONResponse({"profile": reg.profile, "features": items})
    except Exception as exc:
        return JSONResponse({"error": "registry_unavailable", "detail": str(exc)}, status_code=500)


# ---------------------------------------------------------------------------
# Merged feature flags endpoint (registry + tenant remote overrides)
# ---------------------------------------------------------------------------

_FLAG_CACHE: Dict[str, Dict[str, Any]] = {}
_FLAG_CACHE_TTL_SECONDS = int(cfg.env("FEATURE_FLAGS_TTL_SECONDS", "30") or "30")

_flag_remote_requests_total = Counter(
    "gateway_flag_remote_requests_total",
    "Total remote flag lookups to Somabrain",
    ["result"],
)
_flag_remote_latency_seconds = Histogram(
    "gateway_flag_remote_latency_seconds",
    "Latency of remote flag lookups",
    buckets=[0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)


def _flag_cache_key(tenant_id: str, profile: str) -> str:
    return f"{tenant_id}:{profile}"


def _now_seconds() -> float:
    return time.time()


@router.get("/v1/feature-flags")
async def list_feature_flags(request: Request) -> JSONResponse:
    from services.common.features import build_default_registry
    from python.integrations.somabrain_client import get_tenant_flag

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    reg = build_default_registry()
    profile = reg.profile
    cache_key = _flag_cache_key(tenant_id, profile)
    cached = _FLAG_CACHE.get(cache_key)
    if cached and cached.get("expires_at", 0) > _now_seconds():
        return JSONResponse(cached["payload"])  # serve cached merged view

    descriptors = reg.describe()

    async def _fetch_remote(desc) -> tuple[str, Any]:
        start = time.time()
        try:
            remote_enabled = get_tenant_flag(tenant_id, desc.key)
            _flag_remote_requests_total.labels("ok").inc()
            _flag_remote_latency_seconds.observe(time.time() - start)
            return desc.key, bool(remote_enabled)
        except Exception:
            _flag_remote_requests_total.labels("error").inc()
            _flag_remote_latency_seconds.observe(time.time() - start)
            return desc.key, None  # treat failures as no override

    remote_results: Dict[str, Any] = {}
    for d in descriptors:
        k, v = await _fetch_remote(d)
        remote_results[k] = v

    merged: Dict[str, Dict[str, Any]] = {}
    for d in descriptors:
        local_on = reg.is_enabled(d.key)
        remote_override = remote_results.get(d.key)
        effective = local_on if remote_override is None else bool(remote_override)
        merged[d.key] = {
            "local": local_on,
            "remote": remote_override,
            "effective": effective,
            "source": "remote" if remote_override is not None else "local",
        }

    payload = {
        "tenant": tenant_id,
        "profile": profile,
        "ttl_seconds": _FLAG_CACHE_TTL_SECONDS,
        "flags": merged,
        "timestamp": time.time(),
    }
    _FLAG_CACHE[cache_key] = {"expires_at": _now_seconds() + _FLAG_CACHE_TTL_SECONDS, "payload": payload}
    return JSONResponse(payload)
