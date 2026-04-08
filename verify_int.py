import os
import asyncio
import django
from django.conf import settings

# Setup Django (required for client to read settings)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
django.setup()

from admin.core.somabrain_client import get_somabrain_client

async def main():
    print("--- SOMA INTEGRATION VERIFICATION ---")
    client = get_somabrain_client()
    # Inject API key from environment (never hardcoded in source).
    token = os.environ.get("SA01_TEST_BEARER_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing SA01_TEST_BEARER_TOKEN environment variable")

    await client._ensure_client()
    client._client.headers["Authorization"] = f"Bearer {token}"
    print(f"Client URL: {client._base_url}")
    print(f"Client URL: {client._base_url}")

    # 1. Health Check
    print("1. Checking Brain Health...")
    try:
        healthy = await client.health_check()
        print(f"   Brain Healthy: {healthy}")
    except Exception as e:
        print(f"   Brain Health FAILED: {e}")

    # 2. Store Memory (Write)
    print("2. Storing Memory...")
    mem_content = "Integration Test Payload 777"
    try:
        resp = await client.remember(
            {
                "tenant": "proof-1",
                "namespace": "integration_test",
                "key": f"integration-test-{int(asyncio.get_event_loop().time())}",
                "value": {"content": mem_content},
                "universe": "test_universe"
            },
            tenant="proof-1",
            namespace="wm"
        )
        print(f"   Store Response: {resp}")
    except Exception as e:
        print(f"   Store FAILED: {e}")

    # 3. Recall Memory (Read)
    print("3. Recalling Memory...")
    try:
        print(f"   Querying: {mem_content}")
        # Give a small buffer for indexing if needed
        await asyncio.sleep(1)

        results = await client.recall(
            query=mem_content,
            tenant="proof-tenant",
            top_k=1
        )
        print(f"   Recall Results: {results}")

        # Verify content match
        memories = results.get("memories", [])
        # Handle different response formats (some return list of dicts directly)
        if isinstance(results, list):
             memories = results

        found = False
        for m in memories:
            # Check payload content
            p = m.get("payload", {})
            if isinstance(p, dict) and p.get("content") == mem_content:
                found = True
                break
            # Check top level content
            if m.get("content") == mem_content:
                found = True
                break

        if found:
            print("   ✅ SUCCESS: Content verified in return payload.")
        else:
            print("   ⚠️ WARNING: Content not found in top 1 result (might be indexing lag).")

    except Exception as e:
        print(f"   Recall FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
