import pytest

from services.gateway import main as gateway_main


@pytest.mark.asyncio
async def test_gateway_config_registry_present_after_lifespan():
    app = gateway_main.app
    # Manually invoke startup portion of lifespan (since contextmanager wraps yield)
    cm = gateway_main._gateway_lifespan(app)  # type: ignore
    await cm.__aenter__()
    try:
        registry = getattr(app.state, "config_registry", None)
        assert registry is not None
        snap = registry.get()
        assert snap is not None
        assert snap.version == "0"
        assert snap.checksum
    finally:
        await cm.__aexit__(None, None, None)
