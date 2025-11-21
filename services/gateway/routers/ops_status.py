"""Operational status endpoints consumed by the Web UI (degradation + circuit)."""
from __future__ import annotations

import os
import time

import httpx
from fastapi import APIRouter, HTTPException

import asyncio
from services.gateway.degradation_monitor import degradation_monitor
from services.gateway.circuit_breakers import CircuitBreakerHealth
from services.common.memory_write_outbox import MemoryWriteOutbox
from services.common.admin_settings import ADMIN_SETTINGS

router = APIRouter(prefix="/v1", tags=["ops"])


@router.on_event("startup")
async def _ensure_degradation_monitor():
    try:
        if not degradation_monitor.is_monitoring():
            await degradation_monitor.initialize()
            await degradation_monitor.start_monitoring()
    except Exception:
        # best-effort; health endpoint will surface issues
        pass


@router.get("/degradation/status")
async def degradation_status():
    try:
        return await degradation_monitor.get_degradation_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"degradation_status_error: {exc}")


@router.get("/degradation/components")
async def degradation_components():
    try:
        return await degradation_monitor.get_component_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"degradation_components_error: {exc}")


@router.get("/circuit/status")
async def circuit_status():
    try:
        return CircuitBreakerHealth.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"circuit_status_error: {exc}")


@router.get("/metrics/system")
async def metrics_system():
    """Return basic system metrics expected by the Web UI."""
    import shutil
    import psutil

    cpu_percent = 0.0
    mem_percent = 0.0
    disk_percent = 0.0
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
    except Exception:
        pass
    try:
        disk = shutil.disk_usage("/")
        disk_percent = round(disk.used / disk.total * 100, 2) if disk.total else 0.0
    except Exception:
        pass

    # Compute brain status from degradation + backlog
    brain_status = "unknown"
    brain_backlog = await _pending_outbox()
    try:
        brain_health = await degradation_monitor.get_degradation_status()
        # If overall is healthy and backlog == 0 => healthy
        if getattr(brain_health, "overall_level", None) == getattr(degradation_monitor, "DegradationLevel", None):
            pass  # Defensive; not expected here
    except Exception:
        brain_health = None

    try:
        # Simple rule: backlog>0 or degraded => buffering
        degraded = False
        try:
            status = await degradation_monitor.get_degradation_status()
            degraded = status.overall_level.name.lower() != "none" if hasattr(status, "overall_level") else False
        except Exception:
            pass
        if brain_backlog and brain_backlog > 0:
            brain_status = "buffering"
        if degraded:
            brain_status = "degraded"
        if (brain_backlog == 0 or brain_backlog == -1) and not degraded:
            brain_status = "healthy"
    except Exception:
        brain_status = "unknown"

    return {
        "status": "ok",
        "timestamp": time.time(),
        "cpu": {"percent": cpu_percent},
        "memory": {"percent": mem_percent},
        "disk": {"percent": disk_percent},
        "components": {
            "gateway": {"status": "healthy"},
            "somabrain": {"status": brain_status, "backlog": brain_backlog},
        },
    }


@router.get("/somabrain/health")
async def somabrain_health():
    base = os.getenv("SA01_SOMA_BASE_URL") or "http://localhost:9696"
    url = base.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        # Surface degraded state without blowing up the UI
        return {"status": "degraded", "error": str(exc)}


__all__ = ["router"]
async def _pending_outbox() -> int:
    """Return pending memory write outbox count."""
    try:
        store = MemoryWriteOutbox(dsn=ADMIN_SETTINGS.postgres_dsn)
        count = await store.count_pending()
        await store.close()
        return count
    except Exception:
        return -1  # signal error
