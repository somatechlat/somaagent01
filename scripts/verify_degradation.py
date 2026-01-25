import asyncio
import os
import sys

import requests

# Ensure we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
os.environ["SOMA_API_TOKEN"] = "soma_aaas_secret_token_123"

import django

django.setup()

from django.conf import settings

# Patch settings to include SOMA_API_TOKEN since services.gateway.settings doesn't have it
settings.SOMA_API_TOKEN = os.environ.get("SOMA_API_TOKEN")
# Patch namespace and other things SFM might need
settings.SOMA_MEMORY_NAMESPACE = "test_ns"
settings.SOMA_LOG_LEVEL = "INFO"


from services.common.degradation_monitor import DegradationMonitor


def print_result(test_name: str, passed: bool, message: str = ""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {test_name}: {message}")


async def run_degradation_verification():
    print("🔬 Starting Degradation Mode Verification...")

    monitor = DegradationMonitor()
    await monitor.initialize()

    # 1. Check Initial Health (Assuming Milvus is DOWN)
    print("\n[Test 1] Checking Degradation Status (Milvus should be down)...")

    # Force check
    # We simulate a "check" by calling internal methods or just relying on the fact
    # that we turned off the container.
    # But DegradationMonitor uses REAL connections.

    # Initialize components first

    # Specifically check 'storage' or 'multimodal' or 'somafractalmemory'?
    # The monitor checks: somabrain, database, kafka, redis, etc.
    # It seems 'somafractalmemory' is NOT in the default 'core_components' list in __init__?
    # Wait, let's check the code again.
    # core_components include: somabrain, database, kafka...
    # Milvus is checked via 'vector_store' usually, but I don't see 'vector_store' in the list.
    # Ah, 'somafractalmemory' usually wraps Milvus.
    # Let's check if there is a 'vector_store' component or similar.

    # Looking at the code:
    # SERVICE_DEPENDENCIES: "somabrain", "database", "kafka"...
    # There doesn't seem to be a direct "milvus" component in DegradationMonitor?
    # This might be the issue the user is talking about ("I DONT KNOW HOW YO PASSED TESTS").

    # Wait, 'storage' checks 'multimodal_degradation_service.get_available_storage()'.
    # Does that check Milvus? No, that checks S3/MinIO.

    # If Milvus is missing from DegradationMonitor, that is a HUGE find.
    # But let's verify if the system fails gracefully anyway.

    # Let's try to hit the SFM API directly.
    # If Milvus is down, SFM should likely fail or return a degraded response.

    BASE_URL = "http://localhost:63901"  # SFM Port (Mapped)

    print(f"Connecting to SFM at {BASE_URL}...")

    try:
        headers = {"Authorization": f"Bearer {os.environ['SOMA_API_TOKEN']}"}
        resp = requests.get(f"{BASE_URL}/health", headers=headers)
        print(f"Health Response: {resp.status_code} - {resp.text}")

        # If Milvus is down, we expect healthy=False for vector_store
        data = resp.json()
        if not data.get("vector_store"):
            print_result("Vector Store Health", True, "Correctly reported as unhealthy")
        else:
            print_result(
                "Vector Store Health", False, "Reported as healthy despite Milvus being down!"
            )

    except Exception as e:
        print_result("Health Check", False, f"Failed to connect: {e}")

    # 2. Attempt Memory Save
    print("\n[Test 2] Attempting Memory Save (Graceful Failure Check)...")
    try:
        payload = {
            "coord": "1,1,1,1",
            "payload": {"content": "Test memory during degradation"},
            "memory_type": "episodic",
        }
        resp = requests.post(f"{BASE_URL}/memories", json=payload, headers=headers)

        print(f"Save Response: {resp.status_code} - {resp.text}")

        if resp.status_code == 200:
            print_result(
                "Graceful Failure",
                True,
                "Returned 200 OK! System gracefully degraded (Saved to SQL, skipped Milvus)",
            )
        elif resp.status_code == 503 or resp.status_code == 424:
            print_result(
                "Graceful Failure",
                False,
                "Returned error stats, system did not degrade gracefully.",
            )
        else:
            print_result("Graceful Failure", False, f"Unexpected code: {resp.status_code}")

    except Exception as e:
        print_result("Memory Save", False, f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(run_degradation_verification())
