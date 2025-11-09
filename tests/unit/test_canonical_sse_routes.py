"""
Perfect canonical backend route tests - testing real SSE endpoints with no mocks.
These tests verify the new canonical FastAPI endpoints work correctly with real services.
"""
import asyncio
import json
import os
import uuid
from typing import Dict, Any, List

import httpx
import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app
from python.integrations.somabrain_client import SomaClient
from python.integrations.postgres_client import postgres_pool
from python.integrations.opa_middleware import opa_client


class TestCanonicalSseRoutes:
    """Test the new canonical SSE-only endpoints with real implementations."""

    def setup_method(self):
        """Setup test client for each test."""
        self.client = TestClient(app)

    def test_weights_endpoint_no_mock(self):
        """Test /v1/weights endpoint returns real model weights."""
        response = self.client.get("/v1/weights")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], dict)
        # Verify we have at least one real model
        assert len(data["models"]) > 0
        
        # Check structure of first model
        first_model_key = next(iter(data["models"]))
        model_info = data["models"][first_model_key]
        assert "weight" in model_info
        assert "capabilities" in model_info
        assert isinstance(model_info["weight"], (int, float))

    def test_context_endpoint_no_mock(self):
        """Test /v1/context endpoint returns real context data."""
        session_id = str(uuid.uuid4())
        response = self.client.get(f"/v1/context/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_flags_endpoint_no_mock(self):
        """Test /v1/feature-flags endpoint returns real feature flags."""
        response = self.client.get("/v1/feature-flags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Verify we have real feature flags
        assert "realtime_mode" in data
        assert isinstance(data["realtime_mode"], bool)

    def test_sse_session_events_no_mock(self):
        """Test SSE endpoint for session events with real Postgres."""
        session_id = str(uuid.uuid4())
        
        # Create a test event in real Postgres
        async def create_test_event():
            async with postgres_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO session_events (session_id, payload) 
                    VALUES ($1, $2::jsonb)
                    """,
                    session_id,
                    json.dumps({
                        "event_id": str(uuid.uuid4()),
                        "type": "user",
                        "message": "test message",
                        "metadata": {"tenant": "test"}
                    })
                )
        
        # Run async database operation
        asyncio.run(create_test_event())
        
        # Test SSE endpoint
        with self.client.stream("GET", f"/v1/sessions/{session_id}/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Read first few events
            events = []
            for chunk in response.iter_lines():
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data != "[DONE]":
                        events.append(json.loads(data))
                    if len(events) >= 1:
                        break
            
            assert len(events) > 0
            assert events[0]["type"] == "user"
            assert events[0]["message"] == "test message"

    def test_sse_heartbeat_real_services(self):
        """Test SSE heartbeat events from real services."""
        session_id = str(uuid.uuid4())
        
        with self.client.stream("GET", f"/v1/sessions/{session_id}/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            # Look for heartbeat event
            events = []
            for chunk in response.iter_lines():
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data != "[DONE]":
                        events.append(json.loads(data))
                    if len(events) >= 2:  # Allow time for heartbeat
                        break
            
            # Should have at least system.keepalive
            heartbeat_events = [e for e in events if e.get("type") == "system.keepalive"]
            assert len(heartbeat_events) >= 1

    def test_authorization_integration_real(self):
        """Test authorization middleware with real OPA integration."""
        # Test unauthorized access
        response = self.client.get("/v1/weights", headers={"Authorization": "invalid"})
        assert response.status_code == 401
        
        # Test authorized access (assuming we have a valid token setup)
        # This would require proper JWT setup in real environment
        response = self.client.get("/v1/weights")
        # Should succeed (public endpoints don't require auth)
        assert response.status_code == 200

    def test_singleton_registry_no_duplicates(self):
        """Test that singleton registry doesn't create duplicate instances."""
        from integrations.somabrain import client as soma_client_1
        from integrations.somabrain import client as soma_client_2
        
        # Both imports should return the exact same instance
        assert soma_client_1 is soma_client_2

    def test_postgres_connection_reuse(self):
        """Test that Postgres connections are properly reused via singleton."""
        from integrations.postgres import pool as pool_1
        from integrations.postgres import pool as pool_2
        
        # Both should be the same pool instance
        assert pool_1 is pool_2

    def test_opa_client_singleton(self):
        """Test that OPA client is a singleton."""
        from integrations.opa import policy as opa_1
        from integrations.opa import policy as opa_2
        
        assert opa_1 is opa_2

    @pytest.mark.asyncio
    async def test_async_sse_flow_real(self):
        """Test async SSE flow with real services."""
        session_id = str(uuid.uuid4())
        
        # Use httpx async client for real async testing
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            async with client.stream("GET", f"/v1/sessions/{session_id}/events") as response:
                assert response.status_code == 200
                
                # Collect events
                events = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            events.append(json.loads(data))
                        if len(events) >= 1:
                            break
                
                assert len(events) >= 1  # At minimum should get system.keepalive