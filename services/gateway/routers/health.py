"""Health router extracted from the gateway monolith.

Provides a minimal /v1/health endpoint that can be mounted independently of
the legacy gateway file. Returns static OK until full integration wires real
health checks through the orchestrator.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
async def health() -> dict[str, object]:
    """Lightweight health with settings readiness signal for UI banner."""
    # Settings readiness is inferred from presence of required LLM fields in DB.
    settings_ready = True
    try:
        import asyncpg

        async def _check():
            async with asyncpg.create_pool(
                cfg.settings().database.dsn, min_size=1, max_size=2
            ) as pool:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key='sections'")
                    sections = row["value"] if row else []
            have_model = have_base = False
            if isinstance(sections, list):
                for sec in sections:
                    for fld in sec.get("fields", []):
                        fid = fld.get("id")
                        if fid == "llm_model" and (fld.get("value") or "").strip():
                            have_model = True
                        if fid == "llm_base_url" and (fld.get("value") or "").strip():
                            have_base = True
            return have_model and have_base

        settings_ready = await _check()
    except Exception:
        settings_ready = False

    status = "ok" if settings_ready else "degraded"
    return {
        "status": status,
        "components": {"settings": {"status": status, "ready": settings_ready}},
    }
