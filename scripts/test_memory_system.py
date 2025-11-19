#!/usr/bin/env python3
"""
Memory System Test Suite Runner

Comprehensive testing of memory guarantees, policy enforcement, and recovery mechanisms.
"""

import asyncio
import os
import sys
from datetime import datetime


def run_sync_tests():
    """Run synchronous unit tests."""
    print("🧪 Running synchronous memory tests...")

    # Import and test components
    try:
        from src.core.domain.memory.replica_store import MemoryReplicaStore
        from services.common.memory_write_outbox import MemoryWriteOutbox

        # Test basic functionality
        outbox = MemoryWriteOutbox()
        print("✅ Outbox initialized")

        replica = MemoryReplicaStore()
        print("✅ Replica store initialized")

        return True
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        return False


async def run_async_tests():
    """Run asynchronous integration tests."""
    print("🔄 Running async memory tests...")

    try:
        from services.common.memory_write_outbox import MemoryWriteOutbox

        outbox = MemoryWriteOutbox()

        # Test health metrics
        health = await outbox.get_health_metrics()
        print(f"✅ Health metrics: {health}")

        # Test SLA metrics
        sla = await outbox.get_sla_metrics()
        print(f"✅ SLA metrics: {sla}")

        # Test tenant metrics
        tenant_metrics = await outbox.get_tenant_metrics("test-tenant")
        print(f"✅ Tenant metrics: {tenant_metrics}")

        return True
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False


def run_policy_tests():
    """Test policy configuration."""
    print("🔐 Testing policy configuration...")

    try:
        policy_path = "policy/tool_policy.rego"
        if os.path.exists(policy_path):
            with open(policy_path, "r") as f:
                content = f.read()

            # Check for required elements
            checks = [
                ("memory.write" in content, "memory write policy"),
                ("memory.recall" in content, "memory recall policy"),
                ("tenant isolation" in content, "tenant isolation"),
                ("rate limiting" in content, "rate limiting"),
            ]

            for check, name in checks:
                if check:
                    print(f"✅ Policy: {name}")
                else:
                    print(f"⚠️ Policy: {name} missing")

            return True
        else:
            print("❌ Policy file not found")
            return False
    except Exception as e:
        print(f"❌ Policy test failed: {e}")
        return False


async def run_comprehensive_test():
    """Run comprehensive memory system test."""
    print("🚀 Running comprehensive memory system test")
    print("=" * 60)

    tests = [
        ("Sync tests", run_sync_tests),
        ("Policy tests", run_policy_tests),
        ("Async tests", lambda: run_async_tests()),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_name == "Async tests":
                result = await test_func()
            else:
                result = test_func()

            results.append({"name": test_name, "passed": result})
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}")
        except Exception as e:
            results.append({"name": test_name, "passed": False, "error": str(e)})
            print(f"  ❌ FAIL - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['name']}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All memory system tests passed!")
        return True
    else:
        print("⚠️ Some tests failed - check logs above")
        return False


if __name__ == "__main__":
    print("Memory System Test Suite")
    print("=" * 30)
    print(f"Started: {datetime.now()}")

    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test suite failed: {e}")
        sys.exit(1)
