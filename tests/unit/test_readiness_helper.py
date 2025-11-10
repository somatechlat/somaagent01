import pytest

from services.common.readiness import readiness_summary


@pytest.mark.asyncio
async def test_readiness_summary_structure(monkeypatch):
    # Force tiny timeout so checks return promptly even if deps absent
    monkeypatch.setenv("READINESS_CHECK_TIMEOUT", "0.05")
    # Disable Kafka probe to avoid attempting real broker connection in CI/unit tests
    monkeypatch.setenv("READINESS_DISABLE_KAFKA", "true")
    result = await readiness_summary()
    assert set(result.keys()) >= {"status", "timestamp", "components"}
    comps = result["components"]
    # Ensure all declared components present
    assert set(comps.keys()) == {"postgres", "kafka", "redis"}
    # Status is either ready or unready; components have statuses
    assert result["status"] in {"ready", "unready"}
    for v in comps.values():
        assert v.get("status") in {"healthy", "unhealthy"}
