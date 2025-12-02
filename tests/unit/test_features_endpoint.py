import os
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_get_features_endpoint_minimal_surface(monkeypatch):
    # Ensure audio_support remains disabled to avoid whisper import in tests
    monkeypatch.setenv("SA01_FEATURE_PROFILE", "standard")
    # Disable auth requirements for test simplicity
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")

    # Import after env is set so the app initializes with the right profile
    from services.gateway.main import app  # noqa: WPS433  (import inside function for test)

    client = TestClient(app)
    resp = client.get("/v1/features")
    assert resp.status_code == 200

    payload: Dict[str, Any] = resp.json()
    assert set(payload.keys()) == {"profile", "features"}
    assert payload["profile"] == "standard"

    features: List[Dict[str, Any]] = payload["features"]
    assert isinstance(features, list)
    assert len(features) > 0

    # Validate minimal schema for each entry
    for item in features:
        assert set(item.keys()) >= {
            "key",
            "state",
            "enabled",
            "profile_default",
            "dependencies",
            "stability",
            "tags",
        }
        assert item["state"] in {"on", "degraded", "disabled"}
        assert isinstance(item["enabled"], bool)
        assert isinstance(item["profile_default"], bool)
        assert isinstance(item["dependencies"], list)
        assert isinstance(item["tags"], list)

    # Spot-check the presence of a core feature
    keys = {i["key"] for i in features}
    assert "sequence" in keys
