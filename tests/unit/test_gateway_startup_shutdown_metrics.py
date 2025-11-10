import pytest
from prometheus_client import generate_latest

from services.gateway import main as gateway_main


@pytest.mark.asyncio
async def test_startup_shutdown_metrics_smoke():
    app = gateway_main.app
    cm = gateway_main._gateway_lifespan(app)  # type: ignore
    await cm.__aenter__()
    try:
        data = generate_latest()
        text = data.decode("utf-8")
        assert "service_startup_seconds" in text
    finally:
        await cm.__aexit__(None, None, None)
    # After shutdown, metrics should still be present (histogram recorded)
    data2 = generate_latest()
    text2 = data2.decode("utf-8")
    assert "service_shutdown_seconds" in text2
