"""SomaBrain connector — single resilient owner of the Agent↔SomaBrain link.

All brain I/O goes through ``SomaBrainClient``. This module exposes the
connector's **circuit + health** so the UI banner reflects the agent's
connector state (not a raw probe of SomaBrain).

Production rules:
- Fail-closed on missing config.
- Circuit breaker on every HTTP call (already in SomaBrainClient).
- Health is derived from the connector circuit + last successful call.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from services.common.circuit_breaker import CircuitState, get_circuit_breaker

LOGGER = logging.getLogger(__name__)

# Optional calls (neuromodulators) must never trip the memory circuit.
OPTIONAL_TIMEOUT_S = 3.0
REQUIRED_TIMEOUT_S = 5.0


@dataclass
class ConnectorHealth:
    """Agent-side SomaBrain connector health (what the UI banner shows)."""

    connected: bool
    circuit: str  # closed | open | half_open
    base_url: str
    last_success_at: Optional[float] = None
    last_error: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SomaBrainConnector:
    """Resilient SomaBrain connector facade used by chat + UI health."""

    _instance: Optional["SomaBrainConnector"] = None

    def __init__(self) -> None:
        self._last_success_at: Optional[float] = None
        self._last_error: Optional[str] = None
        self._latency_ms: Optional[float] = None

    @classmethod
    def instance(cls) -> "SomaBrainConnector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _breaker(self):
        return get_circuit_breaker("somabrain", failure_threshold=5, reset_timeout=30.0)

    async def health(self) -> ConnectorHealth:
        """Connector health — circuit state + cheap live ping when half/closed."""
        from admin.core.somabrain_client import SomaBrainClient

        breaker = self._breaker()
        state = breaker.state
        state_name = {
            CircuitState.CLOSED: "closed",
            CircuitState.OPEN: "open",
            CircuitState.HALF_OPEN: "half_open",
        }.get(state, str(state))

        base = ""
        client = await SomaBrainClient.get_async()
        if client is not None:
            base = getattr(client, "_base_url", "") or ""

        # Cheap ping only when circuit is not fully open.
        connected = state_name != "open"
        if connected and client is not None:
            started = time.perf_counter()
            try:
                await client.ping(timeout=OPTIONAL_TIMEOUT_S)
                self._last_success_at = time.time()
                self._last_error = None
                self._latency_ms = (time.perf_counter() - started) * 1000.0
                connected = True
            except Exception as exc:  # noqa: BLE001 — health must not raise
                self._last_error = str(exc)
                connected = False
                self._latency_ms = (time.perf_counter() - started) * 1000.0

        return ConnectorHealth(
            connected=connected and state_name == "closed",
            circuit=state_name,
            base_url=base,
            last_success_at=self._last_success_at,
            last_error=self._last_error,
            latency_ms=round(self._latency_ms, 1) if self._latency_ms else None,
        )

    def note_success(self, latency_ms: float) -> None:
        self._last_success_at = time.time()
        self._last_error = None
        self._latency_ms = latency_ms

    def note_error(self, error: str) -> None:
        self._last_error = error


def get_soma_brain_connector() -> SomaBrainConnector:
    return SomaBrainConnector.instance()
