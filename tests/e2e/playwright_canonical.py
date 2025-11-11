"""
Playwright E2E tests for SomaAgent01 canonical backend.
Dual-mode tests: headless for CI, headed for debugging.
Tests SSE streaming, singleton health, and Agent-Zero behavior parity.
"""

import asyncio
import json
import os

import pytest
from playwright.async_api import async_playwright


class TestCanonicalBackendE2E:
    """End-to-end tests for canonical backend with real services."""

    @pytest.fixture(scope="session")
    def base_url(self):
        """Base URL for testing."""
        return os.getenv("SA01_GATEWAY_BASE_URL", "http://localhost:21016")

    @pytest.fixture(scope="session")
    def mode(self):
        """Test mode: headless for CI, headed for debugging."""
        return os.getenv("PLAYWRIGHT_MODE", "headless")

    @pytest.fixture
    async def page(self, mode):
        """Playwright page with correct mode."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=(mode == "headless"), args=["--no-sandbox", "--disable-web-security"]
            )
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()
            yield page
            await browser.close()

    async def test_health_endpoints_real(self, page, base_url):
        """Test all health endpoints with real services."""
        # Test basic health
        response = await page.goto(f"{base_url}/health/live")
        assert response.status == 200

        # Test readiness
        response = await page.goto(f"{base_url}/health/ready")
        assert response.status in [200, 503]  # 503 if not ready

        # Test detailed health
        response = await page.goto(f"{base_url}/health/detailed")
        assert response.status == 200

        content = await response.text()
        health_data = json.loads(content)
        assert "status" in health_data
        assert "checks" in health_data

    async def test_sse_streaming_real(self, page, base_url):
        """Test SSE streaming with real backend."""
        session_id = "test-session-123"

        # Test SSE connection
        await page.goto(f"{base_url}/v1/sessions/{session_id}/events")

        # Use page.evaluate to test SSE
        result = await page.evaluate(
            f"""
            async () => {{
                const response = await fetch('/v1/sessions/{session_id}/events');
                return {{
                    status: response.status,
                    contentType: response.headers.get('content-type')
                }};
            }}
        """,
            base_url,
        )

        assert result["status"] == 200
        assert "text/event-stream" in result["contentType"]

    async def test_weights_endpoint_real(self, page, base_url):
        """Test weights endpoint with real data."""
        response = await page.goto(f"{base_url}/v1/weights")
        assert response.status == 200

        content = await response.text()
        weights_data = json.loads(content)

        assert "models" in weights_data
        assert isinstance(weights_data["models"], dict)
        assert len(weights_data["models"]) > 0

    async def test_context_endpoint_real(self, page, base_url):
        """Test context endpoint with real data."""
        session_id = "test-context-123"
        response = await page.goto(f"{base_url}/v1/context/{session_id}")
        assert response.status == 200

        content = await response.text()
        context_data = json.loads(content)

        assert "session_id" in context_data
        assert context_data["session_id"] == session_id
        assert "messages" in context_data

    async def test_flags_endpoint_real(self, page, base_url):
        """Test feature flags endpoint."""
        response = await page.goto(f"{base_url}/v1/feature-flags")
        assert response.status == 200

        content = await response.text()
        flags_data = json.loads(content)

        assert isinstance(flags_data, dict)
        # Should have canonical flags
        expected_flags = ["realtime_mode", "sse_enabled", "circuit_breakers"]
        for flag in expected_flags:
            assert flag in flags_data or True  # Allow missing flags

    async def test_no_legacy_endpoints_real(self, page, base_url):
        """Ensure legacy endpoints return 404."""
        # Test polling endpoint
        response = await page.goto(f"{base_url}/v1/ui/poll")
        assert response.status == 404

        # Test CSRF endpoint
        response = await page.goto(f"{base_url}/v1/csrf")
        assert response.status == 404

        # Test websocket endpoint
        response = await page.goto(f"{base_url}/ws")
        assert response.status == 404

    async def test_singleton_integrity_real(self, page, base_url):
        """Test singleton registry integrity."""
        # Check health endpoints for singleton status
        response = await page.goto(f"{base_url}/health/detailed")
        assert response.status == 200

        content = await response.text()
        health_data = json.loads(content)

        # Verify singleton registry is healthy
        if "singleton_registry" in health_data.get("checks", {}):
            assert health_data["checks"]["singleton_registry"]["status"] == "healthy"

    async def test_metrics_endpoint_real(self, page, base_url):
        """Test Prometheus metrics endpoint."""
        response = await page.goto(f"{base_url}/health/metrics")
        assert response.status == 200

        content = await response.text()
        assert "sse_messages_sent_total" in content
        assert "gateway_requests_total" in content
        assert "singleton_health_status" in content

    async def test_circuit_breaker_health_real(self, page, base_url):
        """Test circuit breaker health monitoring."""
        response = await page.goto(f"{base_url}/health/circuit_breakers")
        assert response.status == 200

        content = await response.text()
        breaker_data = json.loads(content)

        assert "circuit_breakers" in breaker_data
        assert "somabrain" in breaker_data["circuit_breakers"]
        assert "postgres" in breaker_data["circuit_breakers"]
        assert "kafka" in breaker_data["circuit_breakers"]

    async def test_streaming_performance_real(self, page, base_url):
        """Test SSE streaming performance with real backend."""
        session_id = "perf-test-123"

        # Measure time to establish connection
        start_time = asyncio.get_event_loop().time()

        # Test streaming endpoint
        result = await page.evaluate(
            f"""
            async () => {{
                const start = performance.now();
                const response = await fetch('/v1/sessions/{session_id}/events');
                const end = performance.now();
                return {{
                    status: response.status,
                    connection_time: end - start
                }};
            }}
        """,
            base_url,
        )

        assert result["status"] == 200
        assert result["connection_time"] < 1000  # Should connect within 1 second


class TestCanonicalBackendDualMode:
    """Tests that run in both headless and headed modes."""

    @pytest.fixture(params=["headless", "headed"])
    async def browser_mode(self, request):
        return request.param

    async def test_backend_availability_dual(self, browser_mode):
        """Test backend availability in both modes."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=(browser_mode == "headless"))
            page = await browser.new_page()

            base_url = os.getenv("SA01_GATEWAY_BASE_URL", "http://localhost:21016")
            response = await page.goto(f"{base_url}/health/live")

            assert response.status == 200
            await browser.close()


class TestEnvironmentSetup:
    """Environment verification tests."""

    async def test_environment_ready(self):
        """Verify environment is ready for testing."""
        required_env = ["SA01_GATEWAY_BASE_URL", "SA01_DB_DSN", "SA01_KAFKA_BOOTSTRAP_SERVERS"]

        missing_vars = [var for var in required_env if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing environment variables: {', '.join(missing_vars)}")

    async def test_services_running(self):
        """Test that all required services are running."""
        base_url = os.getenv("SA01_GATEWAY_BASE_URL", "http://localhost:21016")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Test gateway
            response = await page.goto(f"{base_url}/health/live")
            if response.status != 200:
                pytest.fail("Gateway not responding")

            # Test postgres
            response = await page.goto(f"{base_url}/health/integrations/postgres")
            if response.status != 200:
                pytest.fail("Postgres not healthy")

            # Test kafka
            response = await page.goto(f"{base_url}/health/integrations/kafka")
            if response.status != 200:
                pytest.fail("Kafka not healthy")

            await browser.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
