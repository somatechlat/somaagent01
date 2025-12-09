#!/usr/bin/env python3
"""
Memory Monitoring Utility

Provides real-time monitoring of memory guarantees system:
- Outbox health
- WAL lag
- SLA compliance
- Tenant-specific metrics
"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any, Dict

import aiohttp

from services.common.memory_write_outbox import MemoryWriteOutbox
from src.core.infrastructure.repositories import MemoryReplicaStore


class MemoryMonitor:
    """Real-time memory system monitoring."""

    def __init__(self, api_url: str = "http://localhost:21016"):
        self.api_url = api_url
        self.outbox = MemoryWriteOutbox()
        self.replica = MemoryReplicaStore()

    async def get_gateway_health(self) -> Dict[str, Any]:
        """Get health from gateway API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/v1/health") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_direct_metrics(self) -> Dict[str, Any]:
        """Get metrics directly from services."""
        try:
            health = await self.outbox.get_health_metrics()
            lag = await self.outbox.get_lag_metrics()
            sla = await self.outbox.get_sla_metrics()

            return {
                "outbox_health": health,
                "wal_lag": lag,
                "sla_metrics": sla,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_tenant_overview(self, tenant: str) -> Dict[str, Any]:
        """Get tenant-specific metrics."""
        try:
            tenant_metrics = await self.outbox.get_tenant_metrics(tenant)
            return {
                "tenant": tenant,
                "metrics": tenant_metrics,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"tenant": tenant, "error": str(e)}

    async def cleanup_failed_messages(self, max_age_hours: int = 24) -> int:
        """Clean up stale failed messages."""
        try:
            cleaned = await self.outbox.cleanup_stale_retries(max_age_hours)
            return cleaned
        except Exception as e:
            print(f"Cleanup failed: {e}")
            return 0

    def format_health_summary(self, health: Dict[str, Any]) -> str:
        """Format health data for display."""
        if "error" in health:
            return f"❌ Error: {health['error']}"

        components = health.get("components", {})
        summary = []

        # Memory components
        memory_components = ["memory_write_outbox", "memory_wal_lag", "memory_replicator"]
        for component in memory_components:
            if component in components:
                status = components[component]["status"]
                icon = "✅" if status == "ok" else "⚠️" if status == "warning" else "❌"
                summary.append(f"{icon} {component}: {status}")

        return "\n".join(summary)


async def main():
    parser = argparse.ArgumentParser(description="Memory system monitoring")
    parser.add_argument("--api-url", default="http://localhost:21016", help="Gateway API URL")
    parser.add_argument("--tenant", help="Monitor specific tenant")
    parser.add_argument("--interval", type=int, default=30, help="Update interval in seconds")
    parser.add_argument("--cleanup", action="store_true", help="Clean up failed messages")
    parser.add_argument(
        "--format", choices=["json", "summary"], default="summary", help="Output format"
    )

    args = parser.parse_args()

    monitor = MemoryMonitor(args.api_url)

    if args.cleanup:
        cleaned = await monitor.cleanup_failed_messages()
        print(f"Cleaned up {cleaned} failed messages")
        return

    if args.tenant:
        metrics = await monitor.get_tenant_overview(args.tenant)
        print(json.dumps(metrics, indent=2) if args.format == "json" else str(metrics))
        return

    # Continuous monitoring
    print("Memory System Monitoring")
    print("=" * 40)

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking memory health...")

            # Get both API and direct metrics
            api_health = await monitor.get_gateway_health()
            direct_metrics = await monitor.get_direct_metrics()

            if args.format == "json":
                combined = {
                    "gateway_health": api_health,
                    "direct_metrics": direct_metrics,
                    "timestamp": datetime.now().isoformat(),
                }
                print(json.dumps(combined, indent=2))
            else:
                print("Gateway Health:")
                print(monitor.format_health_summary(api_health))

                print("\nDirect Metrics:")
                print(f"  Outbox Pending: {direct_metrics['outbox_health']['pending_count']}")
                print(
                    f"  SLA Compliance: {direct_metrics['sla_metrics']['sla_compliance_rate']:.2%}"
                )
                print(f"  Max Latency: {direct_metrics['sla_metrics']['max_latency_seconds']:.2f}s")

            await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nMonitoring stopped")


if __name__ == "__main__":
    asyncio.run(main())
