#!/usr/bin/env python3
"""
Lightweight load/soak harness for the Gateway write path.

- Uses httpx.AsyncClient to POST /v1/sessions/message at a target rate.
- Env-configurable; no extra dependencies beyond repository requirements.
- Outputs latency stats (p50/p95/p99), error rates, and throughput.

Env vars (with defaults):
  TARGET_URL: Base URL for gateway (default http://127.0.0.1:8010)
  PATH: Request path (default /v1/sessions/message)
  RPS: Target requests per second (float, default 5)
  DURATION: Test duration in seconds (int, default 30)
  CONCURRENCY: Max in-flight requests (int, default 20)
  JWT: Bearer token to include (optional)
  TENANT: Tenant metadata to include (optional)
  PERSONA_ID: Persona to include (optional)
  MESSAGE: Payload message text (default "ping")

Example:
  TARGET_URL=http://127.0.0.1:8010 RPS=20 DURATION=60 CONCURRENCY=50 \
  python scripts/load/soak_gateway.py
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class Stats:
    """Stats class implementation."""

    latencies: list[float]
    ok: int = 0
    err: int = 0

    def record(self, latency: float, ok: bool) -> None:
        """Execute record.

        Args:
            latency: The latency.
            ok: The ok.
        """

        self.latencies.append(latency)
        if ok:
            self.ok += 1
        else:
            self.err += 1

    def snapshot(self) -> dict[str, Any]:
        """Execute snapshot."""

        lats = sorted(self.latencies)

        def pct(p: float) -> float:
            """Execute pct.

            Args:
                p: The p.
            """

            if not lats:
                return 0.0
            k = int(max(0, min(len(lats) - 1, round((p / 100.0) * (len(lats) - 1)))))
            return lats[k]

        total = self.ok + self.err
        return {
            "count": total,
            "ok": self.ok,
            "err": self.err,
            "err_rate": (self.err / total) if total else 0.0,
            "p50": pct(50),
            "p95": pct(95),
            "p99": pct(99),
            "avg": (sum(lats) / len(lats)) if lats else 0.0,
        }


def _env_float(name: str, default: float) -> float:
    """Execute env float.

    Args:
        name: The name.
        default: The default.
    """

    raw = os.environ.get(name, str(default))
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    """Execute env int.

    Args:
        name: The name.
        default: The default.
    """

    raw = os.environ.get(name, str(default))
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


async def _worker(
    name: str,
    client: httpx.AsyncClient,
    q: asyncio.Queue,
    stats: Stats,
    headers: dict[str, str],
    base_url: str,
    path: str,
    tenant: Optional[str],
    persona_id: Optional[str],
    message: str,
) -> None:
    """Execute worker.

    Args:
        name: The name.
        client: The client.
        q: The q.
        stats: The stats.
        headers: The headers.
        base_url: The base_url.
        path: The path.
        tenant: The tenant.
        persona_id: The persona_id.
        message: The message.
    """

    while True:
        try:
            _ = await q.get()
        except asyncio.CancelledError:
            return
        payload = {
            "session_id": str(uuid.uuid4()),
            "persona_id": persona_id,
            "message": message,
            "attachments": [],
            "metadata": {"tenant": tenant} if tenant else {},
        }
        start = time.perf_counter()
        ok = False
        try:
            resp = await client.post(f"{base_url.rstrip('/')}{path}", json=payload, headers=headers)
            ok = resp.status_code == 200
        except Exception:
            ok = False
        finally:
            stats.record(time.perf_counter() - start, ok)
            q.task_done()


async def main() -> None:
    """Execute main."""

    base_url = os.environ.get("TARGET_URL", "http://127.0.0.1:8010") or "http://127.0.0.1:8010"
    path = os.environ.get("PATH", "/v1/sessions/message") or "/v1/sessions/message"
    rps = _env_float("RPS", 5.0)
    duration = _env_int("DURATION", 30)
    concurrency = _env_int("CONCURRENCY", 20)
    jwt = os.environ.get("JWT")
    tenant = os.environ.get("TENANT")
    persona_id = os.environ.get("PERSONA_ID")
    message = os.environ.get("MESSAGE", "ping") or "ping"

    headers = {"content-type": "application/json"}
    if jwt:
        headers["authorization"] = f"Bearer {jwt}"

    stats = Stats(latencies=[])
    q: asyncio.Queue = asyncio.Queue(maxsize=concurrency)

    async with httpx.AsyncClient(timeout=10.0) as client:
        workers = [
            asyncio.create_task(
                _worker(
                    f"w{i}", client, q, stats, headers, base_url, path, tenant, persona_id, message
                )
            )
            for i in range(concurrency)
        ]
        start = time.monotonic()
        next_tick = start
        sent = 0
        try:
            while True:
                now = time.monotonic()
                if now - start >= duration:
                    break
                # Fill up to the target rate per second
                if now >= next_tick:
                    next_tick = now + 1.0
                    to_send = int(rps)
                    # fractional RPS support: probabilistic extra
                    fractional = rps - to_send
                    if fractional > 0 and (now % 1.0) < fractional:
                        to_send += 1
                    for _ in range(to_send):
                        try:
                            q.put_nowait(True)
                            sent += 1
                        except asyncio.QueueFull:
                            # backpressure: drop this tick's excess
                            break
                await asyncio.sleep(0.01)
        finally:
            await q.join()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    snap = stats.snapshot()
    print(
        json.dumps(
            {
                "target_url": base_url,
                "path": path,
                "rps": rps,
                "duration": duration,
                "concurrency": concurrency,
                "sent": sent,
                **snap,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
