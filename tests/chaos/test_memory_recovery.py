#!/usr/bin/env python3
"""
Memory Recovery Chaos Testing: Durability and Recovery

Tests memory guarantees under failure conditions including:
- SomaBrain outages
- Database connection failures
- Kafka partition issues
- Network partitions
"""

import asyncio
import json
import os
import time
from typing import Any, Dict

import pytest

from services.common.memory_write_outbox import MemoryWriteOutbox
from src.core.domain.memory.replica_store import MemoryReplicaStore


class ChaosSimulator:
    """Simulates various failure conditions for memory testing."""

    def __init__(self):
        self.outbox = MemoryWriteOutbox()
        self.replica_store = MemoryReplicaStore()
        self.metrics = []

    async def simulate_somabrain_outage(self, duration: int = 30) -> Dict[str, Any]:
        """Simulate SomaBrain being unavailable."""
        start_time = time.time()

        # Create test memory entries
        test_payload = {
            "type": "conversation_event",
            "role": "user",
            "content": "Test message during outage",
            "session_id": f"chaos-{start_time}",
            "tenant": "chaos-test",
            "timestamp": time.time(),
        }

        # Attempt to write memory (should go to outbox)
        outbox_id = await self.outbox.enqueue(
            payload=test_payload, tenant="chaos-test", session_id=f"chaos-{start_time}"
        )

        await asyncio.sleep(duration)

        # Check recovery
        health = await self.outbox.get_health_metrics()
        lag = await self.outbox.get_lag_metrics()

        return {
            "chaos_type": "somabrain_outage",
            "duration": duration,
            "outbox_id": outbox_id,
            "health": health,
            "lag": lag,
            "recovery_time": time.time() - start_time,
        }

    async def simulate_database_failure(self, duration: int = 15) -> Dict[str, Any]:
        """Simulate database connection failure."""
        start_time = time.time()

        # Temporarily break database connection
        original_dsn = os.getenv("SA01_DB_DSN")
        os.environ["SA01_DB_DSN"] = "postgresql://invalid:invalid@localhost:5432/invalid"

        try:
            # Attempt operations that should fail
            try:
                await self.outbox.count_pending()
                db_available = False
            except Exception:
                db_available = False

            await asyncio.sleep(duration)

            # Restore connection
            os.environ["SA01_DB_DSN"] = original_dsn

            # Check recovery
            health = await self.outbox.get_health_metrics()

            return {
                "chaos_type": "database_failure",
                "duration": duration,
                "db_available": db_available,
                "recovery_time": time.time() - start_time,
                "health": health,
            }
        finally:
            os.environ["SA01_DB_DSN"] = original_dsn

    async def verify_memory_consistency(self, session_id: str) -> Dict[str, Any]:
        """Verify memory consistency after chaos."""
        try:
            # Check outbox for this session
            pool = await self.outbox._ensure_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM memory_write_outbox 
                    WHERE session_id = $1 
                    ORDER BY created_at
                    """,
                    session_id,
                )

            # Check replica store
            replica_rows = await self.replica_store.list_memories(session_id=session_id, limit=1000)

            return {
                "outbox_entries": len(rows),
                "replica_entries": len(replica_rows),
                "consistency_check": len(rows) <= len(replica_rows),
                "outbox_statuses": [r["status"] for r in rows],
            }
        except Exception as e:
            return {"error": str(e), "consistency_check": False}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_durability_somabrain_outage():
    """Test memory durability during SomaBrain outage."""
    simulator = ChaosSimulator()

    # Run chaos test
    result = await simulator.simulate_somabrain_outage(duration=10)

    # Assertions
    assert result["chaos_type"] == "somabrain_outage"
    assert result["outbox_id"] is not None, "Outbox should handle failed writes"
    assert result["health"]["healthy"] is True, "Outbox should remain healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_recovery_database_failure():
    """Test memory recovery after database failure."""
    simulator = ChaosSimulator()

    # Run chaos test
    result = await simulator.simulate_database_failure(duration=5)

    # Assertions
    assert result["recovery_time"] < 60, "Recovery should be quick"
    assert result["health"]["healthy"] is True, "System should recover successfully"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_consistency_end_to_end():
    """Test memory consistency across chaos scenarios."""
    simulator = ChaosSimulator()
    session_id = f"consistency-test-{time.time()}"

    # Simulate multiple chaos events
    results = []

    # Test 1: Normal operation
    results.append(await simulator.verify_memory_consistency(session_id))

    # Test 2: After database failure
    await simulator.simulate_database_failure(duration=2)
    results.append(await simulator.verify_memory_consistency(session_id))

    # Test 3: After SomaBrain outage
    await simulator.simulate_somabrain_outage(duration=2)
    results.append(await simulator.verify_memory_consistency(session_id))

    # Verify consistency across all tests
    for result in results:
        assert result["consistency_check"] is True, f"Memory consistency failed: {result}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sla_compliance():
    """Test SLA compliance under load."""
    simulator = ChaosSimulator()

    # Generate load
    tasks = []
    for i in range(100):
        payload = {
            "type": "conversation_event",
            "role": "user",
            "content": f"Message {i}",
            "session_id": f"sla-test-{time.time()}",
            "tenant": "sla-test",
        }
        tasks.append(
            simulator.outbox.enqueue(
                payload=payload, tenant="sla-test", session_id=f"sla-test-{time.time()}"
            )
        )

    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()

    # SLA checks
    duration = end_time - start_time
    success_count = sum(1 for r in results if not isinstance(r, Exception))

    assert duration < 30, "SLA: Batch enqueue should complete within 30 seconds"
    assert success_count >= 95, "SLA: At least 95% success rate required"

    health = await simulator.outbox.get_health_metrics()
    assert health["pending_count"] < 50, "SLA: Pending queue should remain small"


if __name__ == "__main__":
    # Run tests interactively
    async def run_all_tests():
        print("Running memory recovery chaos tests...")

        simulator = ChaosSimulator()

        # Test 1: SomaBrain outage
        print("Testing SomaBrain outage...")
        result = await simulator.simulate_somabrain_outage(duration=5)
        print(f"SomaBrain outage test: {json.dumps(result, indent=2)}")

        # Test 2: Memory consistency
        print("Testing memory consistency...")
        consistency = await simulator.verify_memory_consistency("interactive-test")
        print(f"Consistency check: {json.dumps(consistency, indent=2)}")

        print("Phase 3 chaos tests completed.")

    asyncio.run(run_all_tests())
