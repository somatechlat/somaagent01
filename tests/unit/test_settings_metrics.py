import re

from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from observability.metrics import registry
from services.gateway.main import app

client = TestClient(app)


def _metric_value(metrics_text: str, name: str, suffix: str = "") -> float:
    pattern = re.compile(rf"^{re.escape(name + suffix)}(?:\{{[^}}]*\}})?\s+(\d+(?:\.\d+)?)$", re.M)
    m = pattern.search(metrics_text)
    return float(m.group(1)) if m else 0.0


def test_settings_read_increments_metric():
    before = generate_latest(registry).decode("utf-8")
    before_val = _metric_value(before, "settings_read_total", '{endpoint="ui.settings.sections"}')
    r = client.get("/v1/ui/settings/sections")
    assert r.status_code == 200
    after = generate_latest(registry).decode("utf-8")
    after_val = _metric_value(after, "settings_read_total", '{endpoint="ui.settings.sections"}')
    assert after_val >= before_val + 1.0


def test_settings_write_increments_metrics():
    payload = {"sections": []}
    before = generate_latest(registry).decode("utf-8")
    before_total = _metric_value(
        before, "settings_write_total", '{endpoint="ui.settings.sections",result="success"}'
    )
    before_sum = _metric_value(before, "settings_write_latency_seconds_sum")

    r = client.post("/v1/ui/settings/sections", json=payload)
    assert r.status_code == 200

    after = generate_latest(registry).decode("utf-8")
    after_total = _metric_value(
        after, "settings_write_total", '{endpoint="ui.settings.sections",result="success"}'
    )
    after_sum = _metric_value(after, "settings_write_latency_seconds_sum")

    assert after_total >= before_total + 1.0
    assert after_sum > before_sum
