from unittest.mock import MagicMock

import pytest

import python.helpers.circuit_breaker as circuit_breaker


@pytest.fixture(autouse=True)
def reset_exporter_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment and in-memory flags before each test."""

    monkeypatch.delenv("CIRCUIT_BREAKER_METRICS_PORT", raising=False)
    monkeypatch.delenv("CIRCUIT_BREAKER_METRICS_HOST", raising=False)
    circuit_breaker._EXPORTER_STARTED = False  # type: ignore[attr-defined]


def test_metrics_exporter_no_port(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_start = MagicMock()
    monkeypatch.setattr(circuit_breaker, "start_http_server", mock_start)

    circuit_breaker.ensure_metrics_exporter()

    mock_start.assert_not_called()


def test_metrics_exporter_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIRCUIT_BREAKER_METRICS_PORT", "abc")
    mock_start = MagicMock()
    monkeypatch.setattr(circuit_breaker, "start_http_server", mock_start)

    circuit_breaker.ensure_metrics_exporter()

    mock_start.assert_not_called()


def test_metrics_exporter_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIRCUIT_BREAKER_METRICS_PORT", "1234")
    monkeypatch.setenv("CIRCUIT_BREAKER_METRICS_HOST", "127.0.0.1")
    mock_start = MagicMock()
    monkeypatch.setattr(circuit_breaker, "start_http_server", mock_start)

    circuit_breaker.ensure_metrics_exporter()
    circuit_breaker.ensure_metrics_exporter()

    mock_start.assert_called_once_with(1234, addr="127.0.0.1")
