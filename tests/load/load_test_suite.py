"""Simple Locust load test for the SomaAgent01 orchestrator.

The test targets two core endpoints:
* ``/v1/health`` – verifies the health aggregation works under load.
* ``/metrics``   – ensures the Prometheus metrics endpoint can handle a
  reasonable request rate.

Locust is used because it provides a lightweight, script‑able load‑testing
framework that integrates well with CI pipelines. The test can be executed
directly via ``locust -f tests/load/load_test_suite.py`` or through the CI
workflow.
"""

from __future__ import annotations

import os

from locust import between, HttpUser, task


class OrchestratorUser(HttpUser):
    """User that repeatedly hits health and metrics endpoints."""

    # Wait 1‑2 seconds between tasks to simulate realistic traffic.
    wait_time = between(1, 2)

    @task(3)
    def health(self) -> None:
        self.client.get("/v1/health")

    @task(1)
    def metrics(self) -> None:
        self.client.get("/metrics")

    def on_start(self) -> None:
        # Set the host from an environment variable if provided; default to
        # the local orchestrator.
        self.host = os.getenv("ORCHESTRATOR_HOST", "http://localhost:8010")
