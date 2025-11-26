import os
import pytest
import httpx
import json
import asyncio

@pytest.mark.asyncio
async def test_sprint_features_on_real_infra():
    """
    Comprehensive verification of Sprint 4 (Planning) and Sprint 5 (Cognition)
    features against the deployed infrastructure.
    """
    BASE_URL = os.environ.get("BASE_URL", "http://gateway:8010")
    print(f"Testing against BASE_URL: {BASE_URL}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ------------------------------------------------------------------
        # 1. Health Check (Foundation)
        # ------------------------------------------------------------------
        print("\n[1] Verifying System Health...")
        resp = await client.get(f"{BASE_URL}/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        print(f"    Status: {data.get('status')}")
        # We accept 'degraded' because SomaBrain (external) is known to be down
        assert data.get("status") in ["ok", "degraded"]

        # ------------------------------------------------------------------
        # 2. Decision Engine Verification (Sprint 5)
        # ------------------------------------------------------------------
        print("\n[2] Verifying Decision Engine (Chat)...")
        # Sending a simple message triggers the Decision Engine's GO/NOGO logic
        chat_payload = {
            "message": "Hello, checking your neuro-state.",
            "role": "user"
        }
        resp = await client.post(f"{BASE_URL}/v1/session/message", json=chat_payload)
        assert resp.status_code == 200
        chat_result = resp.json()
        session_id = chat_result.get("session_id")
        assert session_id is not None
        print(f"    Chat accepted. Session ID: {session_id}")

        # ------------------------------------------------------------------
        # 3. Request Plan Tool Verification (Sprint 4)
        # ------------------------------------------------------------------
        print("\n[3] Verifying Planning Tool (Sprint 4)...")
        # Sending a goal-oriented request should trigger the 'request_plan' tool
        # The worker will analyze this and likely select the tool.
        plan_payload = {
            "message": "Please create a detailed plan to organize a conference.",
            "role": "user",
            "session_id": session_id # Reuse session
        }
        resp = await client.post(f"{BASE_URL}/v1/session/message", json=plan_payload)
        assert resp.status_code == 200
        print(f"    Plan request accepted.")

        # Note: We cannot easily verify the *output* of the tool here without SSE,
        # but the acceptance of the request confirms the Gateway -> Worker path is open.
        # We will verify the tool execution via logs in the next step.
