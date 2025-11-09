import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from services.common.config_registry import ConfigRegistry


SCHEMA_PATH = Path("schemas/config/registry.v1.schema.json")


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_config_registry_valid_document(tmp_path):
    schema = load_schema()
    registry = ConfigRegistry(schema)
    doc = {
        "version": "1",
        "overlays": {
            "uploads": {"uploads_enabled": True, "uploads_max_mb": 10, "uploads_max_files": 5},
            "antivirus": {"av_enabled": False},
            "speech": {"stt_model_size": "tiny", "speech_realtime_enabled": False},
        },
        "secrets": {"openai": "openai"},
        "feature_flags": {"some_flag": True},
    }
    snap = registry.load_defaults(doc)
    assert snap.version == "1"
    assert snap.checksum
    # Apply an update with a new version
    doc2 = dict(doc)
    doc2["version"] = "2"
    snap2 = registry.apply_update(doc2)
    assert snap2.version == "2"
    assert snap2.checksum != snap.checksum


def test_config_registry_rejects_invalid_document():
    schema = load_schema()
    registry = ConfigRegistry(schema)
    bad = {"version": "1"}  # missing overlays
    with pytest.raises(ValidationError):
        registry.load_defaults(bad)
