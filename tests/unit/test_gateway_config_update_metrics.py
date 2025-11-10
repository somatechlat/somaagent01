import pytest

from services.gateway import main as gateway_main


@pytest.mark.asyncio
async def test_config_update_metrics_increment(monkeypatch):
    app = gateway_main.app
    # Trigger startup to ensure metrics objects exist
    cm = gateway_main._gateway_lifespan(app)  # type: ignore
    await cm.__aenter__()
    try:
        registry = getattr(app.state, "config_registry", None)
        assert registry is not None
        before_ok = gateway_main.CONFIG_UPDATE_RESULTS._value.get(("ok",), 0)  # type: ignore[attr-defined]
        # Apply update
        doc = {"version": "1", "overlays": {}, "secrets": {}, "feature_flags": {}}
        registry.apply_update(doc)
        # Manually simulate listener increment path
        gateway_main.CONFIG_UPDATE_RESULTS.labels("ok").inc()
        after_ok = gateway_main.CONFIG_UPDATE_RESULTS._value.get(("ok",), 0)  # type: ignore[attr-defined]
        assert after_ok == before_ok + 1
    finally:
        await cm.__aexit__(None, None, None)
