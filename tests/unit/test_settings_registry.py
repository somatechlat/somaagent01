import asyncio

from services.common.settings_registry import get_settings_registry


def test_settings_registry_snapshot_basic():
    """Snapshot should return a non-empty list of section dicts with expected keys.

    Runs without requiring a live Postgres instance (graceful fallbacks).
    """
    registry = get_settings_registry()
    sections = asyncio.run(registry.snapshot_sections())
    assert isinstance(sections, list)
    # Should at least have one section from defaults
    assert len(sections) > 0
    # Validate minimal shape for first few sections
    for sec in sections[:3]:
        assert isinstance(sec, dict)
        assert "fields" in sec
        assert isinstance(sec["fields"], list)
        for fld in sec["fields"][:3]:
            assert "id" in fld
            # value may be any type; presence is optional, so no strict assertion
