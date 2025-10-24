"""Small reusable health check helpers for HTTP and gRPC targets.

These are intentionally lightweight async helpers with timeouts used by the
gateway `/healthz` aggregator and other services that need quick probes.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
import grpc

LOGGER = logging.getLogger(__name__)


async def http_ping(url: str, timeout: float = 1.5) -> Dict[str, Any]:
    """Ping an HTTP(S) URL with a short timeout.

    Returns a dict with keys: status (ok|degraded|down), code (int|None), detail (str|None)
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return {"status": "ok", "code": resp.status_code}
    except httpx.HTTPStatusError as exc:
        LOGGER.debug("HTTP ping returned non-2xx", extra={"url": url, "error": str(exc)})
        return {"status": "degraded", "code": getattr(exc.response, "status_code", None), "detail": str(exc)}
    except Exception as exc:
        LOGGER.debug("HTTP ping failed", extra={"url": url, "error": str(exc)})
        return {"status": "down", "code": None, "detail": str(exc)}


async def grpc_ping(target: str, stub_factory: Optional[Any] = None, timeout: float = 1.5) -> Dict[str, Any]:
    """Ping a gRPC target.

    - `target` is a host:port string the channel should connect to.
    - `stub_factory` is an optional callable(channel) -> stub with a `Ping` or `Health` method.

    If a `stub_factory` is provided it will be used to perform a lightweight RPC
    within the timeout window. Otherwise we open a channel and return ok if the
    channel connectivity becomes READY within the timeout.
    """
    try:
        async with grpc.aio.insecure_channel(target) as channel:  # type: ignore[attr-defined]
            if stub_factory is None:
                # Wait for READY state; if not READY quickly consider degraded
                try:
                    await asyncio.wait_for(channel.channel_ready(), timeout=timeout)
                    return {"status": "ok"}
                except asyncio.TimeoutError:
                    return {"status": "degraded", "detail": "channel not ready in time"}

            # If a stub factory is provided, call a lightweight RPC (Ping/Health)
            stub = stub_factory(channel)
            # Prefer common method names
            rpc = None
            for name in ("Ping", "Health", "Check"):
                if hasattr(stub, name):
                    rpc = getattr(stub, name)
                    break
            if rpc is None:
                # Fall back to channel readiness if we can't call a method
                try:
                    await asyncio.wait_for(channel.channel_ready(), timeout=timeout)
                    return {"status": "ok"}
                except asyncio.TimeoutError:
                    return {"status": "degraded", "detail": "channel not ready and no RPC available"}

            try:
                # Call the RPC - expect it to be short and side-effect free
                await asyncio.wait_for(rpc(), timeout=timeout)
                return {"status": "ok"}
            except asyncio.TimeoutError:
                return {"status": "degraded", "detail": "rpc timeout"}
            except Exception as exc:
                LOGGER.debug("gRPC ping RPC failed", extra={"target": target, "error": str(exc)})
                return {"status": "down", "detail": str(exc)}

    except Exception as exc:
        LOGGER.debug("gRPC ping channel failed to open", extra={"target": target, "error": str(exc)})
        return {"status": "down", "detail": str(exc)}
