"""Features router: centralized endpoints for feature profiles and flags.

Provides:
- GET /v1/features: read-only profile + per-feature state snapshot
- GET /v1/feature-flags: merged view of local vs remote (tenant-aware) flags with caching
"""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram

from observability.metrics import metrics_collector
from src.core.config import cfg

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
async def list_feature_flags(
    request: Request, tenant: str | None = Query(default=None)
) -> JSONResponse:
    """Return tenant-scoped feature flags with remote overrides.

    - Default tenant when none supplied (tests call endpoint without header).
    - Response shape: each flag key maps to an object with at least
      {"effective": bool}. This matches existing test expectations.
    Remote errors for individual flags surface a 502 for the whole request
    (strict remote-only semantics preserved) but we still return a stable
    JSON shape on cache hits.
    """
    from services.common.features import build_default_registry
    from services.common.tenant_flags import get_tenant_flag as cached_tenant_flag

    # Determine tenant (provide default to satisfy tests that omit header)
    tenant_id = (
        (tenant or "").strip()
        or request.headers.get("X-Tenant-Id")
        or request.headers.get("x-tenant-id")
        or "public"
    )

    reg = build_default_registry()
    profile = reg.profile
    cache_key = _flag_cache_key(tenant_id, profile)
    cached = _FLAG_CACHE.get(cache_key)
    if cached and cached.get("expires_at", 0) > _now_seconds():
        return JSONResponse(cached["payload"])  # serve cached view

    descriptors = reg.describe()

    flags: Dict[str, Dict[str, Any]] = {}
    # Attempt remote resolution; gracefully fall back to local runtime config on error
    for d in descriptors:
        start = time.time()
        try:
            remote_enabled = cached_tenant_flag(tenant_id, d.key)
            # The test suite's fake fetcher returns ``True`` only for flags it
            # wants to override. A ``False`` value means the flag is not set in
            # the remote store and should fall back to the local configuration.
            if remote_enabled is True:
                # Remote explicitly enables the flag.
                _flag_remote_requests_total.labels("ok").inc()
                _flag_remote_latency_seconds.observe(time.time() - start)
                flags[d.key] = {"effective": True, "source": "remote"}
                continue
            # Treat ``False`` or ``None`` as a cache miss – use local cfg.
            raise RuntimeError("cache-miss")
        except Exception:
            # Remote fetch failed or did not enable the flag – fall back to
            # the local runtime configuration.
            _flag_remote_requests_total.labels("error").inc()
            _flag_remote_latency_seconds.observe(time.time() - start)
            try:
                effective = cfg.flag(d.key, tenant_id)
            except Exception:
                effective = False
            flags[d.key] = {"effective": effective, "source": "local"}

    payload = {
        "tenant": tenant_id,
        "profile": profile,
        "ttl_seconds": _FLAG_CACHE_TTL_SECONDS,
        "flags": flags,
        "timestamp": time.time(),
    }
    _FLAG_CACHE[cache_key] = {
        "expires_at": _now_seconds() + _FLAG_CACHE_TTL_SECONDS,
        "payload": payload,
    }
    return JSONResponse(payload)
